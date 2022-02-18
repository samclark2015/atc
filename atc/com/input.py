import importlib.resources as rsc
import json
import sys
from typing import Dict

from adapt.engine import IntentDeterminationEngine
from adapt.intent import Intent, IntentBuilder

from .. import resources
from . import converters
from .common import CONVERTERS

with rsc.open_text(resources, "adapt.json") as f:
    adapt_data = json.load(f)

engine = IntentDeterminationEngine()

intents: Dict[str, Intent] = {}
for name, data in adapt_data["intents"].items():
    inst = IntentBuilder(name)
    required = data.get("requires", [])
    optional = data.get("optional", [])
    for req in required:
        if isinstance(req, list):
            inst.one_of(*req)
        else:
            inst.require(req)
    for opt in optional:
        inst.optionally(opt)
    intents[name] = inst.build()

for name, data in adapt_data["terms"].items():
    if not isinstance(data, list):
        data = [data]

    for item in data:
        if isinstance(item, str):
            engine.register_entity(item, name)
        elif isinstance(item, dict) and "regex" in item:
            engine.register_regex_entity(item["regex"])

for parser in intents.values():
    engine.register_intent_parser(parser)


def get_intent(text: str) -> Intent:
    print("< {}".format(text))
    intents = engine.determine_intent(text.lower())
    intents = list(intents)

    if intents:
        intent = intents[0]
        data = {}
        for key in intent:
            if key in CONVERTERS:
                data[key + "__conv"] = CONVERTERS[key](intent[key])
            data[key] = intent[key]
        return data
    else:
        return None


if __name__ == "__main__":
    for intent in engine.determine_intent(sys.argv[1]):
        print(intent)
