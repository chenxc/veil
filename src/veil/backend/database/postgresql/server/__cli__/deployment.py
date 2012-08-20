from __future__ import unicode_literals, print_function, division
import logging
from veil.environment.setting import *
from veil.backend.shell import *
from veil.frontend.cli import *
from veil.environment import VEIL_HOME

LOGGER = logging.getLogger(__name__)

@script('create-database')
def create_database(purpose):
    try:
        shell_execute('createdb -h {host} -p {port} -U {user} {database}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port'),
            user=get_option(purpose, 'user'),
            database=get_option(purpose, 'database')), capture=True)
    except ShellExecutionError, e:
        if 'already exists' in e.output:
            pass # ignore
        else:
            raise

@script('drop-database')
def drop_database(purpose):
    try:
        shell_execute('dropdb -h {host} -p {port} -U {user} {database}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port'),
            user=get_option(purpose, 'user'),
            database=get_option(purpose, 'database')), capture=True)
    except ShellExecutionError, e:
        if 'not exist' in e.output:
            pass # ignore
        else:
            raise

@script('migrate')
def migrate(purpose):
    sql_path = VEIL_HOME / 'db' / purpose / '001-baseline.sql'
    shell_execute('psql -h {host} -p {port} -U {user} -f {sql_path} {database}'.format(
        host=get_option(purpose, 'host'),
        port=get_option(purpose, 'port'),
        user=get_option(purpose, 'user'),
        database=get_option(purpose, 'database'),
        sql_path=sql_path))

@script('reset')
def reset(purpose):
    drop_database(purpose)
    create_database(purpose)
    migrate(purpose)


def get_option(purpose, key):
    return get_settings()['{}_postgresql'.format(purpose)][key]