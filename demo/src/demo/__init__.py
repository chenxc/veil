def init():
    from sandal.component import init_component
    from veil.environment import register_environment_settings_provider
    from veil.environment import create_nginx_server_settings
    from veil.environment import NGINX_BASE_SETTINGS

    init_component(__name__)

    DEMO_WEB_HOST = 'localhost'
    DEMO_WEB_PORT = 8080
    UNPRIVILIGED_USER = 'dejavu'
    UNPRIVILIGED_GROUP = 'dejavu'
    register_environment_settings_provider(lambda: {
        'nginx': {
            'inline_static_files_owner': UNPRIVILIGED_USER,
            'inline_static_files_group': UNPRIVILIGED_GROUP,
            'servers': create_nginx_server_settings(DEMO_WEB_HOST, DEMO_WEB_PORT)
        },
        'supervisor': {
            'programs': {
                'demo': {
                    'command': 'veil demo up'
                },
                'postgresql': {
                    'user': UNPRIVILIGED_USER
                }
            }
        },
        'postgresql': {
            'listen_addresses': 'localhost',
            'port': 5432,
            'data_owner': UNPRIVILIGED_USER,
            'user': 'veil',
            'password': 'p@55word'
        },
        'veil': {
            'logging': {
                'level': 'DEBUG'
            },
            'website': {
                'inline_static_files_directory': NGINX_BASE_SETTINGS.nginx.inline_static_files_directory,
                'external_static_files_directory': NGINX_BASE_SETTINGS.nginx.external_static_files_directory
            },
            'demo_database': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'db_name': 'demo',
                'user': 'veil',
                'password': 'p@55word'
            }
        }
    })

init()