"""
### CODE OWNERS: Steve Gredell, Chas Busenburg

### OBJECTIVE:
  Find Luigi Flood opportunities

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


async def evaluate_luigi_opportunity(
    session_jenkins: aiohttp.client.ClientSession,
    executable: dict,
) -> None:
    """Evaluate opportunities to Flood Luigi jobs"""
    name_computer = executable['builtOn']
    LOGGER.info('%s Evaluating opportunities', name_computer)
    params_current = shared.extract_params(executable)
    if not params_current:
        return None

    if str(params_current.get('is_idempotent_can_flood', 'False')).lower() == "false":
        LOGGER.info('%s Cannot Flood', name_computer)
        return None

    url_job = URL(executable['url']).parent.parent
    queue = await shared.get_json_from_url(session_jenkins, shared.URL_JENKINS_QUEUE)
    for item in queue['items']:
        LOGGER.debug('Found the following queue item %s', item)
        # Stupid off by one due to trailing slash...
        try:
            if item['task']['url'].lower()[:-1] == str(url_job).lower():
                LOGGER.info('%s is already in queue to be Flooded', url_job)
                return None
        except KeyError:
            LOGGER.info("This queue item does not have a URL attribute %s", item)

    params_new = params_current.copy()
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
            LOGGER.info('%s Flooding onto %s launched successfully', name_computer, url_job)
            return True
        else:
            LOGGER.info('Flooding onto %s failed with this response: %s', url_job, response.reason)
            return None

    return None


async def main(loop):
    """Scan for Luigi flood opportunities"""
    creds_jenkins = shared.get_jenkins_credentials()
    crumb_header = await shared.get_jenkins_crumb(creds_jenkins)
    async with aiohttp.ClientSession(auth=creds_jenkins, headers=crumb_header) as session_jenkins:
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
                if 'builtOn' not in executable:
                    continue
                LOGGER.info(
                    '%s is building %s',
                    executable['builtOn'],
                    executable['fullDisplayName'],
                )

                tasks_evaluation.append(loop.create_task(evaluate_luigi_opportunity(
                    session_jenkins,
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
