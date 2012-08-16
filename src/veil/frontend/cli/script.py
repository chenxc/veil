from __future__ import unicode_literals, print_function, division
import functools
from logging import getLogger
import sys
import json
from inspect import isfunction
from sandal.component import get_loading_component
from veil.environment.setting import *
from veil.environment import *

script_handlers = {}
LOGGER = getLogger(__name__)
executing_script_handlers = []

def is_script_defined(*argv):
    current_level = script_handlers
    for arg in argv:
        current_level = current_level.get(arg, None)
        if not current_level:
            return False
    return True


def execute_script(*argv, **kwargs):
    level = kwargs.get('level', script_handlers)
    arg = argv[0] if argv else None
    if arg not in level:
        print('{} is unknown, choose from: {}'.format(arg, level.keys()))
        sys.exit(1)
    next_level = level[arg]
    if isfunction(next_level):
        script_handler = next_level
        if script_handler.deployment_settings_provider:
            register_settings_provider(script_handler.deployment_settings_provider)
        user_settings = os.getenv('VEIL_SCRIPT_USER_SETTINGS')
        user_settings = json.loads(user_settings) if user_settings else None
        if user_settings:
            register_settings_provider(lambda settings: user_settings)
        bootstrap_runtime()
        try:
            executing_script_handlers.append(script_handler)
            return script_handler(*argv[1:])
        finally:
            executing_script_handlers.pop()
    else:
        return execute_script(level=next_level, *argv[1:])

def get_executing_script_handler():
    if executing_script_handlers:
        return executing_script_handlers[-1]
    else:
        return None


def script(command, deployment_settings_provider=None):
# syntax sugar for ScriptHandlerDecorator
    return ScriptHandlerDecorator(command, deployment_settings_provider)


class ScriptHandlerDecorator(object):
    def __init__(self, command, deployment_settings_provider):
        self.command = command
        self.deployment_settings_provider = deployment_settings_provider

    def __call__(self, script_handler):
        script_handler = script_handler
        script_handler.deployment_settings_provider = self.deployment_settings_provider

        @functools.wraps(script_handler)
        def wrapper(*args, **kwargs):
            return script_handler(*args, **kwargs)

        level_names = get_current_level_names()
        level = script_handlers
        for level_name in level_names:
            if not level_name.startswith('_'):
                level = level.setdefault(level_name.replace('_', '-'), {})
        if self.command in level:
            raise Exception('{}=>{} script has already been registered'.format(
                '=>'.join(level_names), self.command))
        level[self.command] = wrapper
        return script_handler


def get_current_level_names():
    component = get_loading_component()
    if not component:
        return []
    level_names = component.__name__.split('.')[1:]
    return level_names

