import sandal.component

with sandal.component.init_component(__name__):
    from .client import register_redis

    __all__ = [
        # from client
        register_redis.__name__
    ]
