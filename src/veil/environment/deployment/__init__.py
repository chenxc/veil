import veil.component

with veil.component.init_component(__name__):
    from .local import register_migration_command

    __all__ = [
        register_migration_command.__name__
    ]