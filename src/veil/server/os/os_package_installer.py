from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)
apt_get_update_executed = False

@atomic_installer
def os_package_resource(name):
    installed_version, downloaded_version = get_local_os_package_versions(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    action = None if installed_version else 'INSTALL'
    if UPGRADE_MODE_LATEST == get_upgrade_mode():
        action = action or 'UPGRADE'
    elif UPGRADE_MODE_FAST == get_upgrade_mode():
        action = action or (None if latest_version == installed_version else 'UPGRADE')
    elif UPGRADE_MODE_NO == get_upgrade_mode():
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if should_download_while_dry_run():
            download_os_package(name)
        dry_run_result['os_package?{}'.format(name)] = action or '-'
        return
    if not action:
        return
    if not downloaded_version or downloaded_version != latest_version or UPGRADE_MODE_LATEST == get_upgrade_mode():
        downloaded_version = download_os_package(name)
    if not installed_version or installed_version != downloaded_version:
        LOGGER.info('installing os package: %(name)s ...', {'name': name})
        shell_execute('apt-get -y install {}'.format(name), capture=True)


def download_os_package(name):
    LOGGER.info('downloading os package: %(name)s ...', {'name': name})
    update_os_package_catalogue()
    shell_execute('apt-get -y -d install {}'.format(name), capture=True)
    _, downloaded_version = get_local_os_package_versions(name)
    set_resource_latest_version(to_resource_key(name), downloaded_version)
    return downloaded_version


def update_os_package_catalogue():
    global apt_get_update_executed
    if not apt_get_update_executed:
        apt_get_update_executed = True
        LOGGER.info('updating os package catalogue...')
        shell_execute('apt-get update -q', capture=True)


def to_resource_key(pip_package):
    return 'veil.server.os.os_package_resource?{}'.format(pip_package)


def get_local_os_package_versions(name):
    installed_version = None
    downloaded_version = None
    lines = shell_execute('apt-cache policy {}'.format(name), capture=True).splitlines(False)
    if len(lines) >= 3:
        installed_version = lines[1].split('Installed:')[1].strip()
        if '(none)' == installed_version:
            installed_version = None
        downloaded_version = lines[2].split('Candidate:')[1].strip()
    return installed_version, downloaded_version
