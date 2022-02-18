import dataclasses
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
from atc.db import get_approach, get_runways, get_sid_star, waypoints_to_latlon
from metar.Metar import Metar


@dataclass
class Waypoint:
    name: str

    alt_cst: Optional[Tuple[Optional[float], Optional[float]]] = None
    alt_asn: Optional[float] = None
    coords: Optional[Tuple[float, float]] = None

    def __post_init__(self):
        if not self.coords:
            results = waypoints_to_latlon(self.name)
            if results:
                _, lon, lat = results[0]
                self.coords = (lat, lon)


@dataclass
class FlightPlan:
    callsign: str

    origin: str
    destination: str

    waypoints: List[Waypoint]

    sid: Optional[str] = None
    star: Optional[str] = None

    dep_rwy: Optional[str] = None
    arr_rwy: Optional[str] = None

    approach: Optional[List[Waypoint]] = None

    altimeter: Optional[float] = None

    def __post_init__(self):
        if not self.dep_rwy:
            self.dep_rwy = self.get_dep_rwy()["name"]

        if not self.arr_rwy:
            self.arr_rwy = self.get_arr_rwy()["name"]

        if self.sid:
            alt_cst = self.waypoints[0].alt_cst
            alt_asn = self.waypoints[-1].alt_asn

            for wpt in reversed(get_sid_star(self.sid, self.dep_rwy)):
                ad = wpt["alt_descriptor"]
                a1 = wpt["altitude1"]
                a2 = wpt["altitude2"]

                if ad == "A":
                    # At
                    wpt_cst = (a1, a1)
                elif ad == "B":
                    # Between
                    wpt_cst = (min(a1, a2), max(a1, a2))
                elif ad == "+":
                    # At or above
                    wpt_cst = (max(a1, a2), None)
                elif ad == "-":
                    # At or below
                    wpt_cst = (None, max(a1, a2))

                wpt = Waypoint(wpt["ident"], wpt_cst or alt_cst, alt_asn)
                alt_cst = wpt.alt_cst
                self.waypoints.insert(0, wpt)

        if self.star:
            alt_cst = self.waypoints[-1].alt_cst
            alt_asn = self.waypoints[-1].alt_asn

            for wpt in get_sid_star(self.star, self.arr_rwy):
                ad = wpt["alt_descriptor"]
                a1 = wpt["altitude1"]
                a2 = wpt["altitude2"]

                if ad == "A":
                    # At
                    wpt_cst = (a1, a1)
                elif ad == "B":
                    # Between
                    wpt_cst = (min(a1, a2), max(a1, a2))
                elif ad == "+":
                    # At or above
                    wpt_cst = (max(a1, a2), None)
                elif ad == "-":
                    # At or below
                    wpt_cst = (None, max(a1, a2))

                wpt = Waypoint(wpt["ident"], wpt_cst or alt_cst, alt_asn)
                alt_cst = wpt.alt_cst
                self.waypoints.append(wpt)

        approach = []
        alt_cst = self.waypoints[-1].alt_cst
        alt_asn = self.waypoints[-1].alt_asn
        for wpt in get_approach(self.destination, self.arr_rwy):
            ad = wpt["alt_descriptor"]
            a1 = wpt["altitude1"]
            a2 = wpt["altitude2"]

            if ad == "A":
                # At
                wpt_cst = (a1, a1)
            elif ad == "B":
                # Between
                wpt_cst = (min(a1, a2), max(a1, a2))
            elif ad == "+":
                # At or above
                wpt_cst = (max(a1, a2), None)
            elif ad == "-":
                # At or below
                wpt_cst = (None, max(a1, a2))

            wpt = Waypoint(wpt["fix_ident"], wpt_cst or alt_cst, alt_asn)
            alt_cst = wpt.alt_cst
            approach.append(wpt)
        self.approach = approach

        if not self.altimeter:
            metar = FlightPlan.get_metar(self.origin)
            self.altimeter = metar.press.value()

    def get_dep_rwy(self):
        metar = FlightPlan.get_metar(self.origin)
        return self.get_best_runway(self.origin, (metar.wind_dir.value() + 180 % 360))

    def get_arr_rwy(self):
        metar = FlightPlan.get_metar(self.destination)
        return self.get_best_runway(
            self.destination, (metar.wind_dir.value() + 180 % 360)
        )

    def to_dict(self):
        return dataclasses.asdict(self)

    @staticmethod
    def get_best_runway(icao, heading):
        runways = get_runways(icao)

        best_rwy = runways[0]
        best_angle = abs(runways[0]["heading"] - heading)

        for rwy in runways[1:]:
            angle = abs(rwy["heading"] - heading)
            if angle < best_angle:
                if (
                    best_rwy["length"] - rwy["length"] > 0
                    and abs(angle - best_angle) <= 15
                ):
                    ...
                else:
                    best_rwy = rwy
                    best_angle = angle
            else:
                if (
                    best_rwy["length"] - rwy["length"] > 0
                    and abs(angle - best_angle) <= 15
                ):
                    best_rwy = rwy
                    best_angle = angle
                else:
                    ...

        return best_rwy

    @staticmethod
    def get_metar(icao):
        data = requests.get(
            "http://tgftp.nws.noaa.gov/data/observations/metar/stations/{}.TXT".format(
                icao
            )
        ).text.splitlines()
        obs = None
        for line in data:
            if line.startswith(icao):
                report = line.strip()
                obs = Metar(report)
                break
        return obs
