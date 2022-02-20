import os

os.environ["EDIFICE_QT_VERSION"] = "PyQt5"

import logging
from argparse import ArgumentParser

from .connector.dummy import DummyConnector
from .connector.xplane import XPlaneConnector
from .hmi.interactive.ui import *
from .hmi.testing.test import TestFrontend

parser = ArgumentParser()
parser.add_argument(
    "--backend", required=False, choices=("voice", "test"), default="voice"
)
parser.add_argument(
    "--connector", required=False, choices=("xplane", "dummy"), default="dummy"
)
parser.add_argument("--script", required=False, default="script.txt")

args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

if args.connector == "xplane":
    connector = XPlaneConnector()
else:
    connector = DummyConnector()

if args.backend == "test":
    frontend = TestFrontend(args.script, connector)
else:
    frontend = UIFrontend(connector)

frontend.start()
