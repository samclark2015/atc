import math
import time

import plotly.graph_objects as go
from atc.db import get_runways
from atc.fpl.common import FlightPlan
from atc.nav.geo import coord_add, coord_bearing

RATE = 5.0


class DummyConnector:
    def __init__(self) -> None:
        self.coordinator = None
        self.vs = 0
        self.speed = 0
        self.state = "taxi"
        self.last_time = None
        self.pos = (39.178989, -76.665756)
        self.alt = 143
        self.heading = 0
        self.pos_hist = []
        self.ch = None
        
    def start(self):
        self.t_start = time.time()
        self.coordinator.state["pos"] = self.pos
        self.coordinator.state["alt"] = self.alt
        self.coordinator.state["heading"] = self.heading

    def stop(self):
        fpl: FlightPlan = self.coordinator.state["fpl"]

        self.fig = go.Figure(go.Scattergeo())

        self.fig.add_scattermapbox(
            lat=[pos[0] for pos in self.pos_hist],
            lon=[pos[1] for pos in self.pos_hist],
            mode="markers",
            name="acft",
        )

        for wpt in fpl.waypoints:
            self.fig.add_scattermapbox(
                lat=[wpt.coords[0]],
                lon=[wpt.coords[1]],
                mode="markers",
                marker=dict(size=10, color="red"),
                name=wpt.name,
            )

        self.fig.update_layout(
            mapbox_style="white-bg",
            mapbox_layers=[
                {
                    "below": "traces",
                    "sourcetype": "raster",
                    "sourceattribution": "United States Geological Survey",
                    "source": [
                        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                    ],
                }
            ],
        )
        self.fig.show()

    def takeoff(self):
        fpl: FlightPlan = self.coordinator.state["fpl"]
        rwy = [rwy for rwy in get_runways(fpl.origin) if rwy["name"] == fpl.dep_rwy]

        self.pos = (rwy[0]["laty"], rwy[0]["lonx"])
        self.heading = rwy[0]["heading"]
        self.alt = rwy[0]["altitude"]

        self.state = "climb"
        self.vs = 3000
        self.speed = 170

    def periodic(self):
        if not self.last_time:
            self.last_time = time.time()

        t_now = time.time()
        dt = (t_now - self.last_time) * RATE
        dl = 1.68781 * self.speed * dt
        dh = self.vs / 60 * dt
        # print("dt", dt, "dl", dl, "dh", dh)

        if self.alt >= 1_500:
            self.speed = 250
            self.heading = coord_bearing(self.pos, self.coordinator.state["next_wpt"].coords)

            # if time.time() - self.t_start > 25:
            #     if not self.ch:
            #         self.ch = self.heading
            #     self.heading = self.ch - 45

        elif self.alt > 10_000:
            self.speed = 400
            self.vs = 2000

        self.alt += dh
        self.pos = coord_add(self.pos, dl, self.heading)
        self.pos_hist.append(self.pos)

        self.coordinator.state["pos"] = self.pos
        self.coordinator.state["alt"] = self.alt
        self.coordinator.state["heading"] = self.heading
        self.coordinator.state["vs"] = self.vs * RATE
        self.coordinator.state["gs"] = self.speed * RATE

        print(
            "# state={}, alt={}, pos={}, heading={}".format(
                self.state, self.alt, self.pos, self.heading
            )
        )

        self.last_time = t_now
