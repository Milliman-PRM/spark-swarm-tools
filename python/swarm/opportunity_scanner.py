"""
### CODE OWNERS: Shea Parkes, Steve Gredell

### OBJECTIVE:
  Find Spark Cluster opportunities

### DEVELOPER NOTES:
  Try to be as project agnostic as possible
"""
import logging
import asyncio

import aiohttp
from yarl import URL
from swarm import shared

LOGGER = logging.getLogger(__name__)

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================


async def evaluate_opportunity(session_jenkins, session_noauth, executable):
    """Evaluate a possible opportunity to make an ad-hoc Spark cluster"""
    name_computer = executable['builtOn']
    LOGGER.info('%s Evaluating opportunities', name_computer)
    url_cattle = URL('http://' + name_computer)
    url_spark_rest = url_cattle.with_port(4040) / 'api' / 'v1'

    for action in executable['actions']:
        if 'parameters' in action:
            params_current = {
                param['name']: param['value']
                for param in action['parameters']
            }
            LOGGER.debug(
                '%s Found the current parameters: %s',
                name_computer,
                params_current,
            )
            break
    else:
        LOGGER.info('%s No build parameters found.', name_computer)
        return None

    try:
        applications = await shared.get_json_from_url(
            session_noauth,
            (url_spark_rest / 'applications').with_query({'status': 'running'}),
        )
    except OSError:
        LOGGER.info('%s No Spark application found', name_computer)
        return None

    for application in applications:
        LOGGER.info(
            '%s Found the following Spark application: %s',
            name_computer,
            application['name'],
        )
    assert len(applications) == 1, 'Expected only a single application, got {} on {}'.format(
        len(applications),
        name_computer,
    )
    application = applications[0]

    try:
        jobs = await shared.get_json_from_url(
            session_noauth,
            (url_spark_rest / 'applications' / application['id'] / 'jobs').with_query({
                'status': 'running',
            }),
        )
    except OSError:
        LOGGER.info('%s Spark application %s no longer found', name_computer, application['name'])
        return None

    if jobs:
        LOGGER.info(
            '%s Spark application %s currently working on job: %s',
            name_computer,
            application['name'],
            jobs[0]['name'],
        )
    else:
        LOGGER.info(
            '%s Spark application %s not currently working on any jobs',
            name_computer,
            application['name'],
        )
        return None

    if not {'spark_swarm_master', 'spark_swarm_application'}.issubset(params_current):
        # Should test this earlier, but testing here to make sure spark application sniffing works
        LOGGER.info(
            '%s Jenkins job is not configured for swarming: %s',
            name_computer,
            executable['url'],
        )
        return None
    if params_current['spark_swarm_master'].lower() != 'none':
        LOGGER.info('%s is already participating in a swarm', name_computer)
        return None

    url_job = URL(executable['url']).parent.parent
    queue = await shared.get_json_from_url(session_jenkins, shared.URL_JENKINS_QUEUE)
    for item in queue['items']:
        LOGGER.debug('Found the following queue item %s', item)
        # Stupid off by one due to trailing slash...
        if item['task']['url'].lower()[:-1] == str(url_job).lower():
            LOGGER.info('%s is already in queue to be swarmed', url_job)
            return None

    params_new = params_current.copy()
    params_new['spark_swarm_master'] = name_computer
    params_new['spark_swarm_application'] = application['name']
    LOGGER.info(
        '%s Swarming onto this job %s with these parameters %s',
        name_computer,
        url_job,
        params_new,
    )
    url_build = (url_job / 'buildWithParameters').with_query(params_new)

    async with session_jenkins.post(url_build) as response:
        LOGGER.debug(
            'Posted %s and got return status of %s',
            url_build.human_repr(),
            response.reason,
        )
        if response.reason.lower() == 'created':
            LOGGER.info('%s Swarming onto %s launched successfully', name_computer, url_job)
            return True
        else:
            LOGGER.info('Swarming onto %s failed with this response: %s', url_job, response.reason)
            return None

    return None


async def main(loop) -> int:
    """A function to enclose the execution of business logic."""
    LOGGER.info('About to do something awesome.')

    LOGGER.info('Setting up Jenkins authentication.')
    creds_jenkins = shared.get_jenkins_credentials()
    async with aiohttp.ClientSession(auth=creds_jenkins) as session_jenkins:
        # Jenkins 2.0 needs a live "crumb" to be in all POST headers
        crumb = await shared.get_json_from_url(
            session_jenkins,
            shared.URL_JENKINS / 'crumbIssuer' / 'api' / 'json'
        )
        crumb_header = {crumb['crumbRequestField']: crumb['crumb']}
        LOGGER.debug('Got this crumb to use: %s', crumb_header)

    LOGGER.info('Querying Jenkins for active builds')
    async with aiohttp.ClientSession(auth=creds_jenkins, headers=crumb_header) as session_jenkins, \
        aiohttp.ClientSession() as session_noauth:
        tasks_evaluation = []

        # Silly sized `tree` parameter to get exactly what we want
        # If we wanted to switch to xml, we could also filter the results on server side w/ xpath
        url_computers = (shared.URL_JENKINS / 'computer' / 'api' / 'json').with_query({
            'tree': '*,computer[executors[currentExecutable[*,actions[*,causes[*],parameters[*]]]]]'
            })
        computers = await shared.get_json_from_url(session_jenkins, url_computers)
        LOGGER.debug('Found the following keys: %s', computers.keys())
        LOGGER.debug('Claims this many cattle are busy: %s', computers['busyExecutors'])
        for computer in computers['computer']:
            for executor in computer['executors']:
                executable = executor['currentExecutable']
                if not executable:
                    continue
                LOGGER.info(
                    '%s is building %s',
                    executable['builtOn'],
                    executable['fullDisplayName'],
                )
                tasks_evaluation.append(loop.create_task(evaluate_opportunity(
                    session_jenkins,
                    session_noauth,
                    executable,
                )))
        results = await asyncio.gather(*tasks_evaluation)
        LOGGER.info('Launched %s swarms', results.count(True))

    LOGGER.info('Done doing something awesome.')

    return 0


if __name__ == '__main__':
    # pylint: disable=wrong-import-position, wrong-import-order, ungrouped-imports
    import sys
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
    )

    LOOP = asyncio.get_event_loop()

    RETURN_CODE = LOOP.run_until_complete(main(LOOP))
    LOOP.close()

    sys.exit(RETURN_CODE)
