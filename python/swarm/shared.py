"""
### CODE OWNERS: Steve Gredell, Chas Busenburg

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
URL_JENKINS = URL('http://indy-jenkinsdev.milliman.com')
URL_JENKINS_QUEUE = (URL_JENKINS / 'queue' / 'api' / 'json').with_query({
    'tree': 'items[task[url]]'
})

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================


def get_jenkins_credentials(
        path_config: Path=PATH_JENKINS_CONFIG,
) -> aiohttp.BasicAuth:
    """Get Jenkins credentials from the default location"""
    config = ConfigParser()
    with path_config.open('r') as fh_creds:
        config.read_file(fh_creds)
    return aiohttp.BasicAuth(
        login=config['Credentials']['username'],
        password=config['Credentials']['api_token'],
    )


async def get_json_from_url(
    session: aiohttp.client.ClientSession,
    url: URL,
) -> dict:
    """Query a REST API endpoint and return the decoded JSON"""
    LOGGER.debug('About to query %s', url)
    async with session.get(url) as response:
        LOGGER.debug('Queried %s and got return code of %s', url.human_repr(), response.reason)
        if response.reason.lower() == 'ok':
            return await response.json()
        else:
            return None


async def get_jenkins_crumb(
    creds_jenkins: aiohttp.BasicAuth=None,
) -> dict:
    """Get the crumb_header for Jenkins"""
    LOGGER.info('Setting up Jenkins authentication.')
    if not creds_jenkins:
        creds_jenkins = get_jenkins_credentials()
    async with aiohttp.ClientSession(auth=creds_jenkins) as session_jenkins:
        # Jenkins 2.0 needs a live "crumb" to be in all POST headers
        crumb = await get_json_from_url(
            session_jenkins,
            URL_JENKINS / 'crumbIssuer' / 'api' / 'json'
        )
        crumb_header = {crumb['crumbRequestField']: crumb['crumb']}
        LOGGER.debug('Got this crumb to use: %s', crumb_header)
    return crumb_header


def extract_params(
        executable: dict,
) -> dict:
    """Extract parameters from Jenkins response"""
    name_computer = executable['builtOn']
    for action in executable['actions']:
        if 'parameters' in action:
            try:
                params_current = {
                    param['name']: str(param['value'])
                    for param in action['parameters']
                }
                LOGGER.debug(
                    '%s Found the current parameters: %s',
                    name_computer,
                    params_current,
                )
            except KeyError:
                LOGGER.error("%s Failed to extract params", name_computer)
                return None
            break
    else:
        LOGGER.info('%s No build parameters found.', name_computer)
        return None
    return params_current
