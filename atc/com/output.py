import importlib.resources as rsc
import logging
import re

import yaml

from .. import resources
from ..db import get_airport_name
from .common import CONVERTERS, convert

LOGGER = logging.getLogger("atc.com.output")

from .common import NATO_ALPHA, NUMBER_MAP

reply_map = {
    r"(\d)(\d)\.(\d)(\d)": lambda match: "{} {} {} {}".format(
        *[NUMBER_MAP[i] for i in match.groups()]
    ),
    r"(^|\W)([a-zA-Z]|[A-Z]+)($|\W)": lambda match: "{}{}{}".format(
        match.group(1),
        " ".join(NATO_ALPHA[char] for char in match.group(2).lower()),
        match.group(3),
    ),
    "0{3}": "thousand",
    r"(\d)": lambda match: " " + NUMBER_MAP[match.group(1)] + " ",
    "intl|Intl": "international",
}

reply_map_re = {re.compile(key): value for key, value in reply_map.items()}

with rsc.open_text(resources, "replies.yml") as f:
    replies = yaml.safe_load(f)


def get_response(reply_type, data={}):
    if "origin" in data:
        data["origin"] = get_airport_name(data["origin"])

    if "destination" in data:
        data["destination"] = get_airport_name(data["destination"])

    options = replies.get(reply_type)
    if options is None:
        LOGGER.warning("No replies found for %s", reply_type)
        message = "Sorry, I don't know how to respond to that."
    else:
        message: str = max(
            options, key=lambda s: sum(s.count(k) for k in data.keys() if data[k])
        )

        matches = re.findall(r"\{([a-zA-Z_]+)\}", message)
        data = {match: data[match] for match in matches if data[match]}

        data = convert(data, "out")

        phonetic_data = {}
        for key, value in data.items():
            value = str(value)
            for regexp, replace in reply_map_re.items():
                value = regexp.sub(replace, value)
            phonetic_data[key] = value

        try:
            message = message.format_map(phonetic_data)
        except KeyError as e:
            LOGGER.critical("Missing value for %s in reply %s", e, reply_type)
            return "There was an error processing that request."

    return message
