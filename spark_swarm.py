"""
### CODE OWNERS: Shea Parkes

### OBJECTIVE:
  Find Spark Cluster opportunities

### DEVELOPER NOTES:
  Try to be as project agnositic as possible
"""
import logging
import asyncio

import aiohttp

LOGGER = logging.getLogger(__name__)

# =============================================================================
# LIBRARIES, LOCATIONS, LITERALS, ETC. GO ABOVE HERE
# =============================================================================



def main() -> int:
    """A function to enclose the execution of business logic."""
    LOGGER.info('About to do something awesome.')

    ### ADD NEW CODE HERE ###

    return 0


if __name__ == '__main__':
    # pylint: disable=wrong-import-position, wrong-import-order, ungrouped-imports
    import sys
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
    )

    RETURN_CODE = main()

    sys.exit(RETURN_CODE)
