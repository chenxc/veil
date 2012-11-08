import veil_component

with veil_component.init_component(__name__):
    from .migration import register_migration_command

    __all__ = [
        register_migration_command.__name__
    ]