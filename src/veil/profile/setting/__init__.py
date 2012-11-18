import veil_component

with veil_component.init_component(__name__):
    from veil.environment import *
    from veil.environment.setting import *
    from veil.backend.database.new_postgresql_setting import postgresql_program
    from veil.backend.database.new_redis_setting import redis_program
