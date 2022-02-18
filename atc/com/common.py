CONVERTERS = {}

def converter(key: str):
    def decorator(func):
        CONVERTERS[key] = func
        return func
    return decorator
