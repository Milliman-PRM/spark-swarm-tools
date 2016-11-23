"""
### CODE OWNERS: Shea Parkes

### OBJECTIVE:
  Find Spark Cluster opportunities

### DEVELOPER NOTES:
  Try to be as project agnositic as possible
"""
import logging
import asyncio
from configparser import ConfigParser

import aiohttp
from yarl import URL

import indypy.nonstandard.jenkins_tools.connect as indypy_jenkins

LOGGER = logging.getLogger(__name__)
URL_JENKINS = URL(indypy_jenkins.URL_JENKINS_LOCAL)

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================


def get_jenkins_credentials(path_config=indypy_jenkins.PATH_DEFAULT_CONFIG) -> aiohttp.BasicAuth:
    """Get Jenkins credentials from the default location"""
    config = ConfigParser()
    with path_config.open('r') as fh_creds:
        config.read_file(fh_creds)
    return aiohttp.BasicAuth(
        login=config['Credentials']['username'],
        password=config['Credentials']['api_token'],
    )


async def get_json_from_url(session, url) -> dict:
    """Query a REST API endpoint and return the decoded JSON"""
    LOGGER.debug('About to query %s', url)
    async with session.get(url) as response:
        LOGGER.debug('Queried %s and got return code of %s', url, response.reason)
        if response.reason.lower() == 'ok':
            return await response.json()
        else:
            return None


async def main(loop) -> int:
    """A function to enclose the execution of business logic."""
    LOGGER.info('About to do something awesome.')

    creds_jenkins = get_jenkins_credentials()
    async with aiohttp.ClientSession(auth=creds_jenkins) as session:

        # Silly sized `tree` parameter to get exactly what we want
        # If we wanted to switch to xml, we could also filter the results on server side w/ xpath
        url_computers = (URL_JENKINS / 'computer' / 'api' / 'json').with_query({
            'tree': '*,computer[executors[currentExecutable[*,actions[*,causes[*],parameters[*]]]]]'
            })
        computers = await get_json_from_url(session, url_computers)
        LOGGER.debug('Found the following keys: %s', computers.keys())
        LOGGER.debug('Claims this many are busy: %s', computers['busyExecutors'])
        for computer in computers['computer']:
            for executor in computer['executors']:
                executable = executor['currentExecutable']
                if not executable:
                    continue
                LOGGER.debug(
                    'Building %s on %s',
                    executable['fullDisplayName'],
                    executable['builtOn'],
                )

    LOGGER.info('Done doing something awesome.')

    return 0


if __name__ == '__main__':
    # pylint: disable=wrong-import-position, wrong-import-order, ungrouped-imports
    import sys
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
    )

    LOOP = asyncio.get_event_loop()

    RETURN_CODE = LOOP.run_until_complete(main(LOOP))
    LOOP.close()

    sys.exit(RETURN_CODE)
