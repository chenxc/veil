from __future__ import unicode_literals, print_function, division
import types
import os
import logging
import time
import sys
import threading
import functools
from veil.environment.supervisor import *
from veil.environment import *
from veil.frontend.cli import *

LOGGER = logging.getLogger(__name__)
modify_times = {}

@script('up')
def bring_up_source_code_monitor():
    for i in range(10):
        try:
            load_reloads_on_change_programs_components()
            break
        except:
            LOGGER.info('code contains error, retry in 10 seconds...')
            time.sleep(10) # give 10 seconds to you to fix the problem
    load_reloads_on_change_programs_components()
    restart_all()
    LOGGER.info('start monitoring source code changes...')
    while True:
        reload_on_change()


def load_reloads_on_change_programs_components():
    component_names = set()
    for program_name, program in list_reloads_on_change_programs().items():
        LOGGER.info('found reload on change program: %(program_name)s, watching for %(component_names)s', {
            'program_name': program_name,
            'component_names': program.reloads_on_change
        })
        component_names = component_names.union(set(program.reloads_on_change))
    for component_name in component_names:
        __import__(component_name)


def list_reloads_on_change_programs():
    programs = {}
    for program_name, program in get_current_veil_server().programs.items():
        if program.get('reloads_on_change'):
            programs[program_name] = program
    return programs


def reload_on_change():
    modified_path = is_source_code_modified()
    if modified_path:
        LOGGER.info('{} modified, reloading...'.format(modified_path))
        sys.exit(1)
    else:
        time.sleep(1)


def is_source_code_modified():
    for module_name, module in sys.modules.items():
        # Some modules play games with sys.modules (e.g. email/__init__.py
        # in the standard library), and occasionally this can cause strange
        # failures in getattr.  Just ignore anything that's not an ordinary
        # module.
        if not isinstance(module, types.ModuleType): continue
        path = getattr(module, "__file__", None)
        if not path: continue
        if path.endswith('.pyc') or path.endswith('.pyo'):
            path = path[:-1]
        try:
            modified = os.stat(path).st_mtime
        except:
            continue
        if path not in modify_times:
            modify_times[path] = modified
            continue
        if modify_times[path] != modified:
            return path


def restart_all():
    execute('restart')


def execute(action):
    death_list = set()
    for program_name, program in list_reloads_on_change_programs().items():
        if program.get('group'):
            death_list.add('{}:'.format(program.group))
        else:
            death_list.add(program_name)
    threads = []
    for death_target in death_list:
        killer = functools.partial(supervisorctl, action, death_target)
        thread = threading.Thread(target=killer)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()