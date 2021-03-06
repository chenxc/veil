from __future__ import unicode_literals, print_function, division
import fabric.api
import fabric.state
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

BASELINE_DIR = VEIL_HOME / 'baseline'

@script('download-baseline')
def download_baseline(veil_env_name, pattern):
    if BASELINE_DIR.exists():
        BASELINE_DIR.rmtree()
    BASELINE_DIR.mkdir()
    fabric.state.env.host_string = get_veil_server_deploys_via(veil_env_name, '@guard')
    dir = fabric.api.run('readlink /backup/latest')
    fabric.api.get('{}/{}'.format(dir, '*{}*'.format(pattern) if pattern else '*'), VEIL_HOME / 'baseline')


@script('restore-from-baseline')
def restore_from_baseline(veil_env_name=None, pattern=''):
    if veil_env_name:
        download_baseline(veil_env_name, pattern)
    else:
        if not BASELINE_DIR.exists():
            raise Exception('baseline not downloaded yet, pass env name to restore-from-baseline to download')
    shell_execute('veil down')
    VEIL_VAR_DIR.rmtree()
    VEIL_VAR_DIR.mkdir()
    for backup_path in BASELINE_DIR.listdir():
        shell_execute('tar xzf {} -C {}'.format(backup_path, VEIL_VAR_DIR))
    shell_execute('veil install-server')
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')
    shell_execute('veil down')
