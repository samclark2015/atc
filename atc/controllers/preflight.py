from random import randint
from typing import Optional

from atc.com.common import convert

from ..fpl import FlightPlan, SimbriefImporter
from ..nav.ground import find_path_runway, get_ground_network
from .common import Controller, handles, requires_flightplan


class GroundController(Controller):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self.coordinator.state.update(
            {
                "clearance": False,
                "pushback": False,
                "taxi": False,
            }
        )

    @handles("request:clearance")
    def handle_clearance(self, data):
        if "fpl" not in self.coordinator.state:
            simbrief = SimbriefImporter()
            self.coordinator.state["fpl"] = fpl = simbrief.compile_plan()

            # alt = randint(3000, 10000)
            # self.coordinator.state["assigned_alt"] = assalt = 1000 * round(alt / 1000)
            self.coordinator.state["assigned_alt"] = assalt = 5000

            self.coordinator.state["waypoints"] = wpts = fpl.waypoints.copy()
            self.coordinator.state["next_wpt"] = wpts.pop(0)

        self.coordinator.state["clearance"] = True
        return "request:clearance:ok", {**self.coordinator.state, **fpl.to_dict()}

    @handles("readback:clearance")
    @requires_flightplan
    def handle_clearance_readback(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]

        if (
            self.coordinator.state["assigned_alt"] == data.get("altitude__conv")
            and fpl.dep_rwy == data.get("runway__conv")
            and fpl.sid == data.get("sid__conv")
        ):
            return "readback:ok", {**self.coordinator.state, **fpl.to_dict()}
        else:
            return "request:clearance:ok", {**self.coordinator.state, **fpl.to_dict()}

    @handles("request:pushback")
    @requires_flightplan
    def handle_pushback(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        return "request:pushback:ok", {"callsign": fpl.callsign}

    @handles("request:taxi")
    @requires_flightplan
    def handle_taxi(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        pos = self.coordinator.state["pos"]
        twy_network = get_ground_network(fpl.origin)
        path = find_path_runway(twy_network, pos, fpl.origin, fpl.dep_rwy)
        # self.coordinator.current_engine = self.coordinator.flight_engine
        self.coordinator.state["taxi_path"] = [c.lower() for c in path]
        return "request:taxi:ok", {
            "callsign": fpl.callsign,
            "path": "... ".join(path),
            "rwy": fpl.dep_rwy,
        }

    @handles("readback:taxi")
    @requires_flightplan
    def handle_taxi_readback(self, data):
        fpl: FlightPlan = self.coordinator.state["fpl"]

        if self.coordinator.state["taxi_path"] == data.get("path__conv"):
            return "readback:ok", {**self.coordinator.state, **fpl.to_dict()}
        else:
            return "request:taxi_path:ok", {
                "callsign": fpl.callsign,
                "path": "... ".join(self.coordinator.state["taxi_path"]),
                "rwy": fpl.dep_rwy,
            }

    def periodic(self):
        ...
