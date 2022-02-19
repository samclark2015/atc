from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Waypoint:
    name: str
    lat_lon: Tuple[float, float]
    alt_cst: Optional[float]


@dataclass
class Vector:
    heading: float
    distance: float
    alt_cst: Optional[float]
