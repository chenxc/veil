from __future__ import unicode_literals, print_function, division
from argparse import ArgumentParser
from veil.backend.shell import *
from veil.environment.setting import *
from veil.frontend.cli import script
from .supervisor_setting import supervisor_settings

@script('up')
def bring_up_supervisor(*argv):
    argument_parser = ArgumentParser('Bring up the application')
    argument_parser.add_argument('--daemonize', action='store_true',
        help='should the process run in background')
    args = argument_parser.parse_args(argv)

    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    daemonize = args.daemonize or config.daemonize
    if daemonize:
        pass_control_to('supervisord -c {}'.format(config.config_file))
    else:
        pass_control_to('supervisord -n -c {}'.format(config.config_file))


@script('down')
def bring_down_supervisor():
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    with open(config.pid_file) as f:
        pass_control_to('kill {}'.format(f.read()))


