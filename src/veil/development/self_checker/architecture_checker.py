from __future__ import unicode_literals, print_function, division
import veil_component
from veil.environment import *
from veil.backend.web_service import check_web_service_dependencies
from veil.backend.database.client import check_database_dependencies

architecture_checkers = {
    'WEB_SERVICES': check_web_service_dependencies,
    'DATABASES': check_database_dependencies,
    'TABLES': lambda *args, **kwargs: None # tables are checked in runtime
}

def check_architecture():
    for component_name in get_application_components():
        __import__(component_name) # check if all components can be loaded
    architecture = get_application_architecture()
    for component_name, value in architecture.items():
        check_component_architecture([component_name], value)


def check_component_architecture(component_names, architecture):
    if isinstance(architecture, list):
        return check_component_dependencies(component_names, architecture)
    if not isinstance(architecture, dict):
        raise Exception('do not know how to check architecture for: {}'.format(component_names))
    component_dependencies = architecture.pop('DEPENDENCIES', None)
    if component_dependencies:
        check_component_dependencies(component_names, component_dependencies)
    component_dependencies = architecture.pop('', None)
    if component_dependencies is not None:
        check_component_dependencies(component_names, component_dependencies)
    for key, value in architecture.items():
        if key.startswith('.'):
            inner_component_names = list(component_names)
            inner_component_names.append(key)
            inner_architecture = value
            check_component_architecture(inner_component_names, inner_architecture)
        else:
            architecture_checkers[key](component_names, value)


def check_component_dependencies(component_names, expected_dependencies):
    actual_dependencies = set()
    component_name_prefix = ''.join(component_names)
    parent_component_name_prefix = ''.join(component_names[:-1])
    expected_dependencies = make_component_dependencies_absolute(parent_component_name_prefix, expected_dependencies)
    for component_name, dependencies in veil_component.get_component_map().items():
        if component_name_prefix == component_name or component_name.startswith('{}.'.format(component_name_prefix)):
            actual_dependencies = actual_dependencies.union(
                filter_dependencies(dependencies, 'veil', 'veil.', '{}.'.format(component_name_prefix)))
    unexpected_dependencies = actual_dependencies - set(expected_dependencies)
    if unexpected_dependencies:
        raise Exception('{} should not reference {}'.format(component_name_prefix, unexpected_dependencies))
    unreal_dependencies = set(expected_dependencies) - actual_dependencies
    if unreal_dependencies:
        raise Exception('{} did not reference {}'.format(component_name_prefix, unreal_dependencies))


def make_component_dependencies_absolute(component_name_prefix, dependencies):
    absolute_dependencies = set()
    for dependency in dependencies:
        if dependency.startswith('.'):
            absolute_dependencies.add('{}{}'.format(component_name_prefix, dependency))
        else:
            absolute_dependencies.add(dependency)
    return absolute_dependencies


def filter_dependencies(dependencies, *white_list):
    white_list = set(white_list)
    filtered_dependencies = set()
    for dependency in dependencies:
        if any(dependency.startswith(prefix) for prefix in white_list):
            continue
        filtered_dependencies.add(dependency)
    return filtered_dependencies
