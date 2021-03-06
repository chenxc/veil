from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.model.collection import *
from veil.environment import *
from veil.backend.redis_setting import redis_program
from veil.server.python import *
from veil_component import list_dynamic_dependency_providers


def queue_program(host, port):
    return objectify({
        'queue': redis_program('queue', host, port, persisted_by_aof=True).queue_redis
    })


def resweb_program(resweb_host, resweb_port, queue_host, queue_port):
    return objectify({
        'resweb': {
            'execute_command': 'resweb',
            'environment_variables': {'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'},
            'resources': [('veil.backend.queue.resweb_resource', {
                'resweb_host': resweb_host,
                'resweb_port': resweb_port,
                'queue_host': queue_host,
                'queue_port': queue_port
            })]
        }
    })


def delayed_job_scheduler_program(queue_host, queue_port, logging_level):
    return objectify({
        'delayed_job_scheduler': {
            'execute_command': 'veil sleep 3 pyres_scheduler --host={} --port={} -l {} -f stderr'.format(
                queue_host, queue_port, logging_level),
            'resources': [('veil_installer.component_resource', {'name': 'veil.backend.queue'})],
            'startretries': 10
        }
    })


def periodic_job_scheduler_program(application_logging_levels, application_config):
    veil_logging_level_config_path = VEIL_ETC_DIR / 'periodic-job-scheduler-log.cfg'
    application_component_names = set(list_dynamic_dependency_providers('periodic-job', '@'))
    resources = [
        veil_logging_level_config_resource(
            path=veil_logging_level_config_path,
            logging_levels=application_logging_levels),
        component_resource(name='veil.backend.queue'),
        application_resource(component_names=application_component_names, config=application_config)
    ]
    return objectify({
        'periodic_job_scheduler': {
            'execute_command': 'veil backend queue periodic-job-scheduler-up',
            'environment_variables': {
                'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                'VEIL_LOGGING_EVENT': 'True'
            },
            'redirect_stderr': False,
            'resources': resources
        }
    })


def job_worker_program(
        worker_name, pyres_worker_logging_level, application_logging_levels,
        queue_host, queue_port, queue_names,
        application_config, run_as=None, count=1, timeout=120):
    veil_logging_level_config_path = VEIL_ETC_DIR / '{}-worker-log.cfg'.format(worker_name)
    application_component_names = set()
    for queue_name in queue_names:
        providers = list_dynamic_dependency_providers('job', queue_name)
        application_component_names = application_component_names.union(set(providers))
    resources = [
        veil_logging_level_config_resource(
            path=veil_logging_level_config_path,
            logging_levels=application_logging_levels),
        component_resource(name='veil.backend.queue'),
        application_resource(component_names=application_component_names, config=application_config)
    ]
    pyrse_log_path = VEIL_LOG_DIR / '{}_worker-pyres.log'.format(worker_name)
    programs = {}
    for i in range(count):
        programs.update({
            '{}_worker{}'.format(worker_name, i+1): {
                'execute_command': 'veil sleep 10 pyres_worker --host={} --port={} -t {} -l {} -f {} {}'.format(
                    queue_host, queue_port, timeout, pyres_worker_logging_level, pyrse_log_path, ','.join(queue_names)
                ), # log instruction for the main process, a.k.a pyres_worker
                'environment_variables': {
                    'VEIL_LOGGING_LEVEL_CONFIG': veil_logging_level_config_path,
                    'VEIL_LOGGING_EVENT': 'True'
                }, # log instruction for the sub-process forked from pyres_worker, a.k.a our code
                'group': 'workers',
                'run_as': run_as or CURRENT_USER,
                'resources': resources,
                'startretries': 10,
                'startsecs': 10,
                'redirect_stderr': False,
                'patchable': True
            }
        })
    return objectify(programs)