from __future__ import unicode_literals, print_function, division
import os
from veil_installer import installer
from veil_installer import is_python_package_installed
from veil_installer import install_python_package
from veil_installer import install_file
from veil.backend.shell import *

@installer('db2_driver')
def install_db2_driver(dry_run_result):
    is_installed = is_python_package_installed('ibm-db')
    if dry_run_result is not None:
        dry_run_result['db2-driver'] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    env = os.environ.copy()
    env['IBM_DB_HOME'] = '/opt/db2-clidriver'
    install_python_package(None, 'ibm-db', env=env)
    install_file(None, path='/etc/ld.so.conf.d/db2-clidriver.conf', content='/opt/db2-clidriver/lib')
    shell_execute('ldconfig')


def download_db2_driver():
    if os.path.exists('/opt/db2-clidriver'):
        return
    shell_execute(
        'wget http://dependency-veil.googlecode.com/svn/trunk/db2-clidriver.tar.gz -O /tmp/db2-clidriver.tar.gz')
    #        'wget http://200.200.200.25:8080/db2-clidriver.tar.gz -O /tmp/db2-clidriver.tar.gz')
    shell_execute('tar xzf /tmp/db2-clidriver.tar.gz -C /opt')