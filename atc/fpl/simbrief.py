import importlib.resources as rsc
import json
from typing import List

import requests

from .. import resources
from .common import FlightPlan, Waypoint

USERNAME = "slc20154558"


class SimbriefImporter:
    def __init__(self):
        resp = requests.get(
            "https://www.simbrief.com/api/xml.fetcher.php?username={username}&json=1".format(
                username=USERNAME
            )
        )
        self.ofp_data = resp.json()

    def compile_plan(self):
        with rsc.open_text(resources, "airlines.json") as f:
            callsigns = {
                entry["icao"].lower(): entry["callsign"].lower()
                for entry in json.load(f)
            }

        callsign = (
            callsigns[self.ofp_data["general"]["icao_airline"].lower()]
            + " "
            + self.ofp_data["general"]["flight_number"]
        )
        origin = self.ofp_data["origin"]["icao_code"]
        dest = self.ofp_data["destination"]["icao_code"]

        waypoints: List[str] = self.ofp_data["general"]["route"].split(" ")

        sid = star = None
        if len(waypoints[0]) == 6:
            # this is a SID
            sid = waypoints[0]

        if len(waypoints[-1]) == 6:
            # this is a STAR
            star = waypoints[-1]

        # TODO: parse airways
        initial_alt = int(self.ofp_data["general"].get("initial_altitude", 0))

        waypoints = [wpt for wpt in waypoints if len(wpt) == 5]
        waypoints: List[Waypoint] = [Waypoint(wpt, alt_asn=initial_alt or None) for wpt in waypoints]

        if "stepclimb_string" in self.ofp_data["general"]:
            items = self.ofp_data["general"]["stepclimb_string"].split("/")
            steps = dict(
                (
                    (waypoints[0].name if wpt == origin else (waypoints[-1].name if wpt == dest else wpt)),
                    float(alt) * 100,
                )
                for wpt, alt in zip(items[0::2], items[1::2])
            )

            alt = 0
            for wpt in waypoints:
                if wpt.name in steps:
                    alt = steps[wpt.name]
                wpt.alt_asn = alt

        return FlightPlan(callsign, origin, dest, waypoints, sid, star)


if __name__ == "__main__":
    plan = SimbriefImporter()
    fpl = plan.compile_plan()
    print(fpl)
