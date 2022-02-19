import importlib.resources as rsc
import os
from pprint import pprint
from typing import Any, Dict

from atc.com.common import convert
from snips_nlu import SnipsNLUEngine
from snips_nlu.dataset import Dataset
from snips_nlu.default_configs import CONFIG_EN

from ..resources import snips_intents as intents

intents_dir = os.path.dirname(intents.__file__)

engine = SnipsNLUEngine(config=CONFIG_EN, seed=42)
dataset = Dataset.from_yaml_files(
    "en",
    [
        os.path.join(intents_dir, file)
        for file in rsc.contents(intents)
        if file.endswith((".yaml", ".yml"))
    ],
)
engine.fit(dataset)


def get_intent(text: str) -> Dict[str, Any]:
    intent = engine.parse(text.lower())
    data = {
        "intent_type": intent["intent"]["intentName"],
        **{slot["slotName"]: slot["rawValue"] for slot in intent["slots"]},
    }

    if data:
        return convert(data)
    else:
        return None


if __name__ == "__main__":
    import sys

    pprint(engine.parse(sys.argv[1]))
