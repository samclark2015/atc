from typing import Any, Dict

CONVERTERS = {}


def convert(data: Dict[str, Any]):
    from . import converters

    new = {}
    for key in data:
        if key in CONVERTERS:
            new[key + "__conv"] = CONVERTERS[key](data[key])
        new[key] = data[key]
    return new


def converter(*keys: str):
    def decorator(func):
        for key in keys:
            CONVERTERS[key] = func
        return func

    return decorator


NATO_ALPHA = {
    "a": "alpha",
    "b": "bravo",
    "c": "charlie",
    "d": "delta",
    "e": "echo",
    "f": "foxtrot",
    "g": "golf",
    "h": "hotel",
    "i": "india",
    "j": "juliet",
    "k": "kilo",
    "l": "leema",
    "m": "mike",
    "n": "november",
    "o": "oscar",
    "p": "papa",
    "q": "quebec",
    "r": "romeo",
    "s": "sierra",
    "t": "tango",
    "u": "uniform",
    "v": "victor",
    "w": "whisky",
    "x": "xray",
    "y": "yankee",
    "z": "zulu",
}

NUMBER_MAP = {
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "niner",
    "0": "zero",
}
