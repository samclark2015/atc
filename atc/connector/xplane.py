import time

import plotly.graph_objects as go
import xpc
from atc.db import get_runways
from atc.fpl.common import FlightPlan
from atc.nav.geo import coord_add, coord_bearing


class XPlaneConnector:
    def __init__(self) -> None:
        self.coordinator = None
        self.pos_hist = []
        self.t_start = None
        self.t_last = None

    def start(self):
        self.t_start = time.time()
        self.conn = xpc.XPlaneConnect()

    def stop(self):
        self.conn.close()

    def periodic(self):
        if not self.t_last:
            self.t_last = time.time()

        t_now = time.time()

        (lat,), (lon,), (alt,), (gs,), (vs,), (heading,) = self.conn.getDREFs(
            [
                "sim/flightmodel/position/latitude",
                "sim/flightmodel/position/longitude",
                "sim/flightmodel/position/elevation",
                "sim/flightmodel/position/groundspeed",
                "sim/flightmodel/position/vh_ind_fpm",
                "sim/flightmodel/position/mag_psi",
            ]
        )

        self.coordinator.state["pos"] = (lat, lon)
        self.coordinator.state["alt"] = alt
        self.coordinator.state["heading"] = heading
        self.coordinator.state["vs"] = vs
        self.coordinator.state["gs"] = gs * 1.94384

        self.t_last = t_now
