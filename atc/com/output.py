import importlib.resources as rsc
import json
import re

from .. import resources
from ..db import get_airport_name
from .common import CONVERTERS

nato_alpha = {
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

number_map = {
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

reply_map = {
    r"(\d)(\d)\.(\d)(\d)": lambda match: "{} {} {} {}".format(*[number_map[i] for i in match.groups()]),
    r"(^|\W)([a-zA-Z]|[A-Z]+)($|\W)": lambda match: "{}{}{}".format(
        match.group(1),
        " ".join(nato_alpha[char] for char in match.group(2).lower()),
        match.group(3),
    ),
    "0{3}": "thousand",
    r"(\d)": lambda match: " " + number_map[match.group(1)] + " ",
    "intl|Intl": "international",
}

reply_map_re = {re.compile(key): value for key, value in reply_map.items()}

with rsc.open_text(resources, "replies.json") as f:
    replies = json.load(f)


def get_response(reply_type, data={}):
    if "origin" in data:
        data["origin"] = get_airport_name(data["origin"])

    if "destination" in data:
        data["destination"] = get_airport_name(data["destination"])

    if reply_type in CONVERTERS:
        CONVERTERS[reply_type](data)

    options = replies.get(reply_type)
    if not options:
        message = "Sorry, I don't know how to respond to that."

    message: str = max(options, key=lambda s: sum(s.count(k) for k in data.keys()))

    phonetic_data = {}
    for key, value in data.items():
        value = str(value)
        for regexp, replace in reply_map_re.items():
            value = regexp.sub(replace, value)
        phonetic_data[key] = value

    message = message.format_map(phonetic_data)

    return message
