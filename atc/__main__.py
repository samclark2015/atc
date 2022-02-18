from argparse import ArgumentParser

from atc.controllers.connector.xplane import XPlaneConnector

from .com.input import get_intent
from .com.output import get_response
from .com.speech import SpeechCom
from .com.text import TextCom
from .controllers import Coordinator
from .controllers.connector.dummy import DummyConnector

parser = ArgumentParser()
parser.add_argument("--script", required=False, type=str)

args = parser.parse_args()


if args.script:
    connector = DummyConnector()
    f = open(args.script)
    com = TextCom(f, connector)
else:
    connector = XPlaneConnector()
    com = SpeechCom()

coordinator = Coordinator(com, connector)

try:
    for request in com.get_input():
        intent = get_intent(request)

        if intent:
            value = coordinator.current_engine.handle_request(
                intent["intent_type"], intent
            )
            if value:
                response, data = value
                message = get_response(response, data)
            else:
                message = get_response("garbled")
        else:
            message = get_response("garbled")

        com.respond(message)
except KeyboardInterrupt:
    ...
finally:
    coordinator.cleanup()
