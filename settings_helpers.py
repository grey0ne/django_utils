import os

def config_get(key: str, **kwargs: str | bool | None) -> str | bool | None:
    value = os.environ.get(key)
    if value is None or value == '':
        if 'default' in kwargs:
            value = kwargs['default']
        else:
            raise ValueError(f'No environment var {key}')
    return value

def config_get_str(key: str, default: str | None = None, warning: str | None = None) -> str:
    value = os.environ.get(key)
    if value is None or value == '':
        if warning:
            print(f'Warning: {warning}')
        if default is None:
            raise ValueError(f'No environment var {key}')
        else:
            return default
    return value