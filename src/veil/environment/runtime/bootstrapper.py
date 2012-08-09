from __future__ import unicode_literals, print_function, division
import logging
import sys
from veil.development.test import *
from .option import register_option
from .option import init_options
from .option import EVENT_OPTIONS_INITIALIZED

LOGGER = logging.getLogger(__name__)
boostrapped = False

@test_hook
def bootstrap_runtime(option_updates=None):
    global boostrapped
    if boostrapped:
        return
    else:
        boostrapped = True
    import sys
    import os.path

    __dir__ = os.path.dirname(__file__)
    if __dir__ in sys.path:
        sys.path.remove(__dir__) # disable old style relative import

    import logging
    from ConfigParser import RawConfigParser
    from veil.model.event import subscribe_event
    from veil.environment.layout import VEIL_ETC_DIR


    get_logging_level = register_option('logging', 'level')

    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def configure_logging(logging_level=None):
        LOGGING_LEVEL_VALUES = {}
        for level in [logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.CRITICAL]:
            LOGGING_LEVEL_VALUES[logging.getLevelName(level)] = level
        level = LOGGING_LEVEL_VALUES[logging_level or get_logging_level() or 'INFO']
        logger = logging.getLogger()
        logger.setLevel(level)
        logger.addHandler(handler)

    configure_logging('INFO')
    subscribe_event(EVENT_OPTIONS_INITIALIZED, configure_logging)

    config_parser = RawConfigParser()
    veil_cfg = VEIL_ETC_DIR / 'veil.cfg'
    executing_test = get_executing_test(optional=True)
    if executing_test and not veil_cfg.exists():
        raise Exception('{} not exists'.format(veil_cfg))
    config_parser.read(veil_cfg)
    options = {}
    for section in config_parser.sections():
        options[section] = dict(config_parser.items(section))
    if option_updates:
        options = merge_options(options, option_updates)
    if options:
        init_options(options)
    else:
        LOGGER.debug('options is empty')

def merge_options(base, updates):
    if not base:
        return updates
    if isinstance(base, dict) and isinstance(updates, dict):
        updated = {}
        for k, v in base.items():
            try:
                updated[k] = merge_options(v, updates.get(k))
            except:
                raise Exception('can not merge: {}\r\n{}'.format(k, sys.exc_info()[1]))
        for k, v in updates.items():
            if k not in updated:
                updated[k] = v
        return updated
    if base == updates:
        return base
    if updates:
        raise Exception('can not merge {} with {}'.format(base, updates))
    return base
