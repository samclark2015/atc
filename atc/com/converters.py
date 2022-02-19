import re
from typing import Any, Dict

from .common import NATO_ALPHA, converter

NATO_REV = {v: k for k, v in NATO_ALPHA.items()}


@converter("altitude")
def convert_altitude(value: str) -> float:
    if value.endswith(("ft", "feet")):
        value, unit = value.split(" ")
        value = float(value.replace(",", ""))
    elif value.startswith("flight level"):
        unit, value = value.rsplit(" ", 1)
        value = float(value) * 100
    return value


@converter("path")
def convert_nato(value: str) -> str:
    value = value.lower()
    for key, letter in NATO_REV.items():
        value = value.replace(key, letter)
    return value


@converter("sid", "star", "wpt")
def convert_icao(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", value).upper()


@converter("altimeter")
def convert_altimeter(value: str) -> float:
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
    return float(value)


@converter("runway")
def convert_runway(value: str) -> str:
    value = (
        value.replace("left", "L")
        .replace("right", "R")
        .replace("center", "C")
        .replace(" ", "")
    )
    return value


@converter("request:alt_change:ok")
def convert_flight_level(data: Dict[str, Any]) -> float:
    alt = data["alt"]
    if alt > 10_000:
        data["alt"] = "flight level {:03d}".format(int(alt / 100))
    else:
        data["alt"] = "{} feet".format(int(alt))
