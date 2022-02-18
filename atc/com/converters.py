from typing import Any, Dict

from .common import converter


@converter("altitude")
def convert_altitude(value: str) -> float:
    if value.endswith(("ft", "feet")):
        value, unit = value.split(" ")
    elif value.startswith("flight level"):
        unit, value = value.rsplit(" ", 1)
        value *= 100
    return float(value)

@converter("request:alt_change:ok")
def convert_flight_level(data: Dict[str, Any]) -> float:
    alt = data["alt"]
    if alt > 10_000:
        data["alt"] = "flight level {:03d}".format(int(alt / 100))
    else:
        data["alt"] = "{} feet".format(int(alt))
