"""
### CODE OWNERS: Steve Gredell

### OBJECTIVE:
  Host shared code for opportunity scanning

### DEVELOPER NOTES:
  Try to be as project agnostic as possible
"""
import logging
import asyncio
from configparser import ConfigParser
from pathlib import Path

import aiohttp
from yarl import URL

LOGGER = logging.getLogger(__name__)
PATH_JENKINS_CONFIG = Path('H:/.jenkins')
URL_JENKINS = URL('http://indy-jenkins.milliman.com')
URL_JENKINS_QUEUE = (URL_JENKINS / 'queue' / 'api' / 'json').with_query({
    'tree': 'items[task[url]]'
})

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================


def get_jenkins_credentials(path_config=PATH_JENKINS_CONFIG) -> aiohttp.BasicAuth:
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
        LOGGER.debug('Queried %s and got return code of %s', url.human_repr(), response.reason)
        if response.reason.lower() == 'ok':
            return await response.json()
        else:
            return None

