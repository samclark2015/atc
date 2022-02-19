import logging
from argparse import ArgumentParser

from PyQt5.QtWidgets import QApplication, QWidget

from atc.controllers.connector.xplane import XPlaneConnector

from .com.output import get_response
from .com.snips_input import get_intent
from .com.speech import SpeechCom
from .com.text import TextCom
from .controllers import Coordinator
from .controllers.connector.dummy import DummyConnector

parser = ArgumentParser()
parser.add_argument("--script", required=False, type=str)

args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

if args.script:
    connector = DummyConnector()
    f = open(args.script)
    com = TextCom(f, connector)
else:
    connector = DummyConnector()
    # connector = XPlaneConnector()
    com = SpeechCom()

coordinator = Coordinator(com, connector)
coordinator.run()

