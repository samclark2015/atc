import re
from typing import Any, Dict

from .common import NATO_ALPHA, NUMBER_MAP, converter

NATO_REV = {"whiskey": "w", **{v: k for k, v in NATO_ALPHA.items()}}
NUM_REV = {"nine": "9", **{v: k for k, v in NUMBER_MAP.items()}}


@converter("altitude", "alt")
def convert_altitude(value: str, direction) -> float:
    if direction == "out":
        if isinstance(value, (float, int)):
            if value > 10_000:
                value = "flight level {:03d}".format(int(value / 100))
            else:
                value = "{} feet".format(int(value))
    else:
        if value.endswith(("ft", "feet")):
            value, unit = value.split(" ")
            value = float(value.replace(",", ""))
        elif value.startswith("flight level"):
            unit, value = value.rsplit(" ", 1)
            value = float(value) * 100
    return value


@converter("path")
def convert_nato(value: str, direction) -> str:
    if direction == "in":
        value = value.lower()
        for key, letter in NATO_REV.items():
            value = value.replace(key, letter)

        for key, letter in NUM_REV.items():
            value = value.replace(key, letter)

        value = value.replace(" ", "")
    else:
        value = re.sub(r"(\w)(\w)", r"\1 \2", value)
    return value


@converter("sid", "star", "wpt")
def convert_icao(value: str, direction) -> str:
    if direction == "in":
        return re.sub(r"[^a-zA-Z0-9]", "", value).upper()
    return value


@converter("altimeter")
def convert_altimeter(value: str, direction) -> float:
    if direction == "in":
        match = re.search(r"\d", value)
        if match:
            value = (
                int(match.group(1)) * 10
                + int(match.group(2))
                + int(match.group(3)) / 10
                + int(match.group(4)) / 100
            )
        else:
            value = 29.92
        value = float(value)
    return value


@converter("runway")
def convert_runway(value: str, direction) -> str:
    if direction == "in":
        value = (
            value.replace("left", "L")
            .replace("right", "R")
            .replace("center", "C")
            .replace(" ", "")
        )
    else:
        value = value.replace("L", "left").replace("R", "right").replace("C", "center")
    return value


@converter("freq")
def convert_readback_ok(value: str, direction) -> float:
    if direction == "out":
        freq = str(value)
        value = freq.replace(".", " dot ")
    return value
