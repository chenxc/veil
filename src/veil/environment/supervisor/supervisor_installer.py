from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

LOGGER = logging.getLogger(__name__)

@composite_installer('supervisor')
@using_isolated_template
def install_supervisor(programs):
    return [], []
#    resources = list(BASIC_LAYOUT_RESOURCES)
#    resources.extend([
#        python_package_resource('supervisor'),
#        file_resource(config.config_file, get_template('supervisord.cfg.j2').render(
#            config=config,
#            CURRENT_USER=CURRENT_USER,
#            format_execute_command=format_execute_command,
#            format_environment_variables=format_environment_variables
#        )),
#        directory_resource(config.logging.directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
#    ])
#    return [], resources


def format_execute_command(program):
    try:
        execute_command_args = program.get('execute_command_args', {})
        return get_template(template_source=program.execute_command).render(**execute_command_args)
    except:
        LOGGER.error('Failed to format command for: {}'.format(program))
        raise


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])