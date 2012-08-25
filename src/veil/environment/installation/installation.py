from __future__ import unicode_literals, print_function, division
import functools
import json
from veil.component import get_loading_component, get_component_dependencies
from veil.backend.shell import *
from veil.environment.setting import *
from veil.environment import *
from veil.frontend.cli import *
from .filesystem import create_directory

# create basic layout before deployment
def installation_script():
    decorator = script('install')

    def decorate(func):
        component_name = get_loading_component().__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if os.getenv('VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'):
                return func(*args, **kwargs)
            create_layout()
            for dependency in get_transitive_dependencies(component_name):
                install_dependency(dependency)
            env = os.environ.copy()
            env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'] = 'TRUE'
            shell_execute('veil {} install'.format(' '.join(component_name.split('.')[1:])), env=env)
            return None

        return decorator(wrapper)

    return decorate


def install_dependency(component_name):
    args = list(component_name.split('.'))[1:]
    args = [arg.replace('_', '-') for arg in args]
    args.append('install')
    if is_script_defined(*args):
        env = os.environ.copy()
        env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'] = 'TRUE'
        shell_execute('veil {}'.format(' '.join(args)), env=env)


def get_transitive_dependencies(component_name):
    dependencies = list()
    collect_transitive_dependencies(component_name, dependencies)
    return dependencies


def collect_transitive_dependencies(component_name, dependencies):
    for dependency in get_component_dependencies().get(component_name, ()):
        if dependency not in dependencies:
            collect_transitive_dependencies(dependency, dependencies)
            dependencies.append(dependency)


def create_layout():
    create_directory(VEIL_HOME / 'log')
    create_directory(VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    create_directory(VEIL_HOME / 'etc')
    create_directory(VEIL_ETC_DIR)
    create_directory(VEIL_HOME / 'var')
    create_directory(VEIL_VAR_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)