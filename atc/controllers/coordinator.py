from threading import Thread, Timer
from time import sleep, time
from typing import Any, Dict

from atc.com.input import get_intent
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

    def run(self):
        try:
            for request in self.com.get_input():
                intent = get_intent(request)

                message = None

                if intent:
                    value = self.current_engine.handle_request(
                        intent["intent_type"], intent
                    )
                    if value:
                        response, data = value
                        message = get_response(response, data)
                else:
                    message = get_response("garbled")

                if message:
                    self.com.respond(message)
        except KeyboardInterrupt:
            ...
        finally:
            self.cleanup()

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
