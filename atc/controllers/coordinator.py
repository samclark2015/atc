from threading import Thread, Timer
from time import sleep, time
from typing import Any, Dict

from atc.com.output import get_response
from atc.controllers.flight import FlightController

from .preflight import GroundController

PERIODIC_TIMER = 1.0

class Coordinator:
    def __init__(self, com, connector) -> None:
        self.com = com
        self.state: Dict[str, Any] = {}

        # Set up the connector
        self.connector = connector
        self.connector.coordinator = self
        self.connector.start()

        # Set up the engines
        self.ground_controller = GroundController(self)
        self.flight_engine = FlightController(self)

        self.current_engine = self.ground_controller

        # Set up the periodic timer
        self.periodic_timer = Thread(target=self.periodic, daemon=True)
        self.periodic_timer.start()

    def cleanup(self):
        self.connector.stop()
        
    def periodic(self):
        while True:
            self.current_engine.periodic()
            self.connector.periodic()
            sleep(PERIODIC_TIMER)

    def say(self, utterance, data):
        message = get_response(utterance, data)
        self.com.respond(message)
