import math
import time
from random import randint
from typing import *

from atc.fpl.common import Waypoint

from ..fpl import FlightPlan
from ..nav.geo import coord_bearing, coord_dist
from .common import Controller, handles, requires_flightplan

DIST_THRESH = 1.0
HDG_THRESH = 1.5
TIME_THRESH = 30


class FlightController(Controller):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self.coordinator.state.update({"stage": "climb", "last_wpt": None})
        self.last_vector_time = None
        self.current_vector = None
        self.vector_calls = 0
        self.lvl_change = "UP"
        self.departed = False

    @handles("request:takeoff")
    @requires_flightplan
    def handle_takeoff(self, data):
        if self.departed:
            return "request:takeoff:already_departed", data

        fpl: FlightPlan = self.coordinator.state["fpl"]
        self.coordinator.state["next_wpt"] = fpl.waypoints[0]
        return "request:takeoff:ok", {
            "callsign": fpl.callsign,
            "altimeter": fpl.altimeter,
            "rwy": fpl.dep_rwy,
        }

    @handles("request:alt_change")
    @requires_flightplan
    def handle_alt_change(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        alt = self.coordinator.state["alt"]
        direction = "climb" if data["altitude__conv"] > alt else "descend"
        return "request:alt_change:ok", {
            "callsign": fpl.callsign,
            "dir": direction,
            "alt": data["altitude__conv"],
        }

    @handles("readback:alt_change")
    @requires_flightplan
    def handle_alt_change(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        alt = self.coordinator.state["alt"]
        asn = self.coordinator.state["assigned_alt"]

        if data["altitude__conv"] != asn:
            direction = "climb" if data["altitude__conv"] > alt else "descend"
            return "request:alt_change:ok", {
                "callsign": fpl.callsign,
                "dir": direction,
                "alt": data["altitude__conv"],
            }

    @handles("request:dir_wpt")
    @requires_flightplan
    def handle_dir_wpt(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        alt = self.coordinator.state["alt"]
        direction = "climb" if data["altitude__conv"] > alt else "descend"
        return "request:alt_change:ok", {
            "callsign": fpl.callsign,
            "dir": direction,
            "alt": data["altitude__conv"],
        }

    def advance(self):
        self.coordinator.state["last_wpt"] = self.coordinator.state["next_wpt"]
        self.coordinator.state["next_wpt"] = self.coordinator.state["waypoints"].pop(0)

    def periodic(self):
        self.lateral_check()
        self.vertical_check()

        # Ready for altitude clearance
        alt = self.coordinator.state["alt"]
        asn = self.coordinator.state["assigned_alt"]
        nxt = self.coordinator.state["next_wpt"].alt_asn
        if asn - alt < randint(700, 1500):
            if asn != nxt:
                self.lvl_change = "UP" if nxt > asn else "DOWN"
                self.coordinator.state["assigned_alt"] = nxt
                self.coordinator.say(
                    "request:alt_change:ok",
                    {
                        "callsign": self.coordinator.state["fpl"].callsign,
                        "dir": "climb" if self.lvl_change == "UP" else "descend",
                        "alt": self.coordinator.state["assigned_alt"],
                    },
                )

        if self.dist_to_next < DIST_THRESH:
            self.advance()

    def vertical_check(self):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        wpt: Waypoint = self.coordinator.state["next_wpt"]
        alt: float = self.coordinator.state["alt"]  # ft
        vs: float = self.coordinator.state["vs"] / 60.0  # ft / sec
        gs: float = self.coordinator.state["gs"] * 1.68781  # ft / sec

        dist_ft = self.dist_to_next * 6076.12  # ft

        if gs > 0:
            alt_at_next = alt + vs * dist_ft / gs

            if wpt.alt_cst[0] and alt_at_next < wpt.alt_cst[0]:
                # Too low
                ...
            elif wpt.alt_cst[1] and wpt.alt_cst[1] < alt_at_next:
                # Too high

                ...

    def lateral_check(self):
        fpl: FlightPlan = self.coordinator.state["fpl"]

        if self.coordinator.state["last_wpt"] is not None:
            planned_hdg = coord_bearing(
                self.coordinator.state["last_wpt"].coords,
                self.coordinator.state["next_wpt"].coords,
            )
        else:
            planned_hdg = coord_bearing(
                self.coordinator.state["pos"], self.coordinator.state["next_wpt"].coords
            )

        dir_hdg = coord_bearing(
            self.coordinator.state["pos"], self.coordinator.state["next_wpt"].coords
        )
        act_hdg = self.coordinator.state["heading"]

        hdg_dev = abs(planned_hdg - dir_hdg)
        track_dev = abs(
            self.dist_to_next * math.sin(math.radians(hdg_dev)) / math.sin(math.pi / 2)
        )

        if (
            self.coordinator.state["alt"] >= 2000
            and (track_dev > DIST_THRESH or abs(act_hdg - dir_hdg) > HDG_THRESH)
            and (
                self.current_vector is None
                or (
                    abs(act_hdg - self.current_vector) > HDG_THRESH
                    and time.time() - self.last_vector_time > TIME_THRESH
                )
            )
        ):
            self.last_vector_time = time.time()
            self.current_vector = dir_hdg
            self.coordinator.say(
                "info:off_course:vectors",
                {
                    "callsign": fpl.callsign,
                    "hdg": "{:03.0f}".format(dir_hdg),
                    "dir": "right"
                    if (360 + dir_hdg - act_hdg) % 360 <= 180
                    else "left",
                    "dist": "{:3.1f}".format(track_dev),
                    "wpt": self.coordinator.state["next_wpt"].name,
                },
            )

            if -1 < self.vector_calls >= 1:
                self.advance()
                self.vector_calls = -1
            elif 0 <= self.vector_calls:
                self.vector_calls += 1

        elif (
            self.current_vector is not None
            and abs(act_hdg - self.current_vector) <= HDG_THRESH
            and track_dev <= DIST_THRESH
        ):
            self.current_vector = None
            self.last_vector_time = None
            self.vector_calls = 0
            self.coordinator.say("info:off_course:ok", {"callsign": fpl.callsign})

    @property
    def dist_to_next(self):
        if (
            "pos" not in self.coordinator.state
            or "next_wpt" not in self.coordinator.state
        ):
            return None

        return coord_dist(
            self.coordinator.state["pos"], self.coordinator.state["next_wpt"].coords
        )
