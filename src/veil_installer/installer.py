from __future__ import unicode_literals, print_function, division
import functools
import logging
import inspect
import importlib
import contextlib
import veil_component

LOGGER = logging.getLogger(__name__)
installed_resource_codes = set()
executing_installers = []
dry_run_result = None
application_sub_resources = None
installing = False
stack = []
UPGRADE_MODE_NO = 'no'
UPGRADE_MODE_FAST = 'fast'
UPGRADE_MODE_LATEST = 'latest'
upgrade_mode = None
download_while_dry_run = False

def atomic_installer(func):
    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapper(**kwargs):
        if not kwargs.pop('do_install', False):
            return '{}.{}'.format(
                veil_component.get_leaf_component(func.__module__),
                func.__name__), kwargs
        try:
            executing_installers.append(func)
            return func(**kwargs)
        finally:
            executing_installers.pop()

    return wrapper


def composite_installer(func):
    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapper(**kwargs):
        global executing_composite_installer

        try:
            executing_installers.append(func)
            return func(**kwargs)
        finally:
            executing_installers.pop()

    return atomic_installer(wrapper)


@atomic_installer
def application_resource(component_names, config):
    global application_sub_resources
    try:
        application_sub_resources = {}
        component_resources = [('veil_installer.component_resource', dict(name=name)) for name in component_names]
        install_resources(component_resources)
        for component_name in component_names:
            try:
                __import__(component_name)
            except:
                if get_dry_run_result() is None:
                    raise
        resources = []
        for section, resource_provider in application_sub_resources.items():
            resources.append(resource_provider(config[section]))
        return resources
    finally:
        application_sub_resources = None


def add_application_sub_resource(section, resource_provider):
    if not is_installing():
        return
    if application_sub_resources is None:
        raise Exception('not installing any application resource')
    application_sub_resources[section] = resource_provider


def get_executing_installer():
    return executing_installers[-1]


def install_resource(resource):
    install_resources([resource])


def install_resources(resources):
    global installing
    installing = True
    resources = list(skip_installed_resources(resources))
    for resource in resources:
        more_resources = do_install(resource)
        stack.append(resource)
        try:
            if len(stack) > 30:
                LOGGER.error('failed to install sub resources: %(stack)s', {
                    'stack': stack
                })
                raise Exception('too many levels')
            install_resources(more_resources)
        finally:
            stack.pop()
        installed_resource_codes.add(to_resource_code(resource))


def do_install(resource):
    installer_name, installer_args = resource
    if installer_name != 'veil_installer.component_resource':
        if '.' not in installer_name:
            raise Exception('invalid installer: {}'.format(installer_name))
        installer_module_name = get_installer_module_name(installer_name)
        if 'veil_installer' != installer_module_name:
            install_resources([('veil_installer.component_resource', dict(name=installer_module_name))])
    try:
        installer = get_installer(installer_name)
        return installer(do_install=True, **installer_args) or []
    except:
        if get_dry_run_result() is None:
            raise
        else:
            return []


def get_installer(installer_name):
    module = importlib.import_module(get_installer_module_name(installer_name))
    return getattr(module, installer_name.split('.')[-1])


def get_installer_module_name(installer_name):
    return '.'.join(installer_name.split('.')[:-1])


def skip_installed_resources(resources):
    for resource in resources:
        resource_code = to_resource_code(resource)
        if resource_code not in installed_resource_codes:
            yield resource


def to_resource_code(resource):
    if len(resource) != 2:
        raise Exception('invalid resource: {}'.format(resource))
    installer_name, installer_args = resource
    if not isinstance(installer_args, dict):
        raise Exception('invalid resource: {}, {}'.format(installer_name, installer_args))
    resource_code = '{}?{}'.format(installer_name, '&'.join(
        ['{}={}'.format(k, installer_args[k])
         for k in sorted(installer_args.keys())]))
    return resource_code


def get_dry_run_result():
    return dry_run_result


@contextlib.contextmanager
def dry_run():
    global dry_run_result

    dry_run_result = {}
    try:
        yield
    finally:
        dry_run_result = None


def is_installing():
    return installing


def set_upgrade_mode(value):
    global upgrade_mode
    upgrade_mode = value


def get_upgrade_mode():
    return upgrade_mode or UPGRADE_MODE_NO


def set_download_while_dry_run(value):
    global download_while_dry_run
    download_while_dry_run = value


def should_download_while_dry_run():
    return download_while_dry_run
