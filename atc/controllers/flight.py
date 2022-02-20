import logging
import math
import time
from random import randint
from typing import *

from atc.db import get_airport_info
from atc.fpl.common import Waypoint

from ..fpl import FlightPlan
from ..nav.geo import coord_bearing, coord_dist
from .common import Controller, handles, requires_flightplan

LOGGER = logging.getLogger(__name__)

DIST_THRESH = 1.5  # nautical miles
HDG_THRESH = 1.5  # degrees
TIME_THRESH = 30  # seconds
DESCENT_SLOPE = 3.0  # degrees


class FlightController(Controller):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self.coordinator.state.update({"stage": "climb", "last_wpt": None})
        self.last_vector_time = None
        self.current_vector = None

        self.last_alt_time = None

        self.vector_calls = 0
        self.departed = False
        self.phase = "climb"

    @handles("request:takeoff", "report:hold_short")
    @requires_flightplan
    def handle_takeoff(self, data):
        if self.departed:
            return "request:takeoff:already_departed", data

        fpl: FlightPlan = self.coordinator.state["fpl"]
        self.coordinator.state["next_wpt"] = fpl.waypoints[0]
        return "request:takeoff:ok", {
            "callsign": fpl.callsign,
            "altimeter": fpl.altimeter,
            "runway": fpl.dep_rwy,
        }

    @handles("request:alt_change")
    @requires_flightplan
    def handle_alt_change(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        alt = self.coordinator.state["alt"]
        direction = "climb" if data["altitude"] > alt else "descend"
        return "request:alt_change:ok", {
            "callsign": fpl.callsign,
            "dir": direction,
            "alt": data["altitude"],
        }

    @handles("readback:alt_change")
    @requires_flightplan
    def handle_alt_change(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        alt = self.coordinator.state["alt"]
        asn = self.coordinator.state["assigned_alt"]

        if data["altitude"] != asn:
            direction = "climb" if data["altitude"] > alt else "descend"
            return "request:alt_change:ok", {
                "callsign": fpl.callsign,
                "dir": direction,
                "alt": data["altitude"],
            }

    @handles("request:dir_wpt")
    @requires_flightplan
    def handle_dir_wpt(self, data):
        ...
        # fpl: FlightPlan = self.coordinator.state["fpl"]
        # alt = self.coordinator.state["alt"]
        # direction = "climb" if data["altitude__conv"] > alt else "descend"
        # return "request:alt_change:ok", {
        #     "callsign": fpl.callsign,
        #     "dir": direction,
        #     "alt": data["altitude__conv"],
        # }

    @handles("readback:takeoff")
    def noop(self, data):
        pass
    

    def advance(self):
        if self.coordinator.state["waypoints"]:
            self.coordinator.state["last_wpt"] = self.coordinator.state["next_wpt"]
            self.coordinator.state["next_wpt"] = self.coordinator.state["waypoints"].pop(0)
        else:
            self.coordinator.state["next_wpt"] = None

    def periodic(self):
        self.lateral_check()
        self.vertical_check()

    def clear_alt(self, alt):
        self.coordinator.state["assigned_alt"] = alt
        self.coordinator.say(
            "request:alt_change:ok",
            {
                "callsign": self.coordinator.state["fpl"].callsign,
                "dir": "climb" if self.coordinator.state["alt"] < alt else "descend",
                "alt": self.coordinator.state["assigned_alt"],
            },
        )

    def vertical_check(self):
        fpl: FlightPlan = self.coordinator.state["fpl"]

        wpt: Waypoint = self.coordinator.state["next_wpt"]
        asn = self.coordinator.state["assigned_alt"]

        alt: float = self.coordinator.state["alt"]  # ft
        vs: float = self.coordinator.state["vs"] / 60.0  # ft / sec
        gs: float = self.coordinator.state["gs"] * 1.68781  # ft / sec

        LOGGER.debug(
            "Current altitude %.1f ft, assigned altitude %.1f ft, vertical speed %.1f ft/sec",
            alt,
            asn,
            vs,
        )

        # Ready for altitude clearance
        if abs(asn - alt) < randint(700, 1500) and self.phase != "approach":
            if wpt.alt_asn != self.coordinator.state["assigned_alt"]:
                self.clear_alt(wpt.alt_asn)

        # Transition to cruise when captured
        if self.phase == "climb" and abs(asn - alt) < 200:
            LOGGER.info("Transitioning to cruise")
            self.phase = "cruise"

        dist_ft = self.dist_to_next * 6076.12  # ft

        if gs > 0:
            alt_at_next = alt + vs * dist_ft / gs
            if wpt.alt_cst:
                if wpt.alt_cst[0] and alt_at_next < wpt.alt_cst[0]:
                    # TODO: tell too low
                    ...
                elif wpt.alt_cst[1] and wpt.alt_cst[1] < alt_at_next:
                    # TODO: tell too high
                    ...

            if abs(vs) <= 75 and abs(alt - asn) > 250:
                # If we're not climbing nor descending and are not at the assigned altitude,
                if alt < asn:
                    # TODO: tell to climb
                    ...
                else:
                    # TODO: tell to descend
                    ...

        # Check if it's time to descend
        airport = get_airport_info(fpl.destination)
        dist_to_dest = (
            coord_dist(
                self.coordinator.state["pos"], (airport["laty"], airport["lonx"])
            )
            * 6076.12
        )  # in feet
        aoe = math.degrees(math.atan2(alt - airport["altitude"], dist_to_dest))

        LOGGER.info(
            "Distance to destination: %.1f nm, angle of elevation: %.1f deg",
            dist_to_dest / 6076.12,
            aoe,
        )

        if aoe >= DESCENT_SLOPE and self.phase not in ("descent", "approach"):
            LOGGER.info("Transitioning to descent")
            self.phase = "descent"
            iaf_alt = int(fpl.approach[0].alt_cst[0])
            
            # self.coordinator.state["assigned_alt"] = iaf_alt
            self.coordinator.state["next_wpt"].alt_asn = iaf_alt
            for wpt in self.coordinator.state["waypoints"]:
                wpt.alt_asn = iaf_alt


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
        LOGGER.info("Heading deviation: %.1f deg, track deviation: %.1f nm", hdg_dev, track_dev)

        if (
            self.coordinator.state["alt"] >= 2000
            and (track_dev > DIST_THRESH and abs(act_hdg - dir_hdg) > HDG_THRESH)
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

        LOGGER.info("Distance to next waypoint: %.1f nm", self.dist_to_next)
        if self.dist_to_next < DIST_THRESH:
            if self.phase == "approach":
                self.coordinator.say("info:approach:cleared", {"callsign": fpl.callsign, "runway": fpl.arr_rwy})

            self.advance()
            if not self.coordinator.state["next_wpt"] and self.phase != "approach":
                LOGGER.info("Transitioning to approach")
                self.coordinator.state["waypoints"] = fpl.approach.copy()
                self.phase = "approach"
                self.advance()

    @property
    def dist_to_next(self):
        if (
            not self.coordinator.state.get("pos")
            or not self.coordinator.state.get("next_wpt")
        ):
            return None

        return coord_dist(
            self.coordinator.state["pos"], self.coordinator.state["next_wpt"].coords
        )
