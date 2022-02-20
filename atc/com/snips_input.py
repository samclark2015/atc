import hashlib
import importlib.resources as rsc
import json
import os
import shutil
from pprint import pprint
from typing import Any, Dict

from atc.com.common import convert
from snips_nlu import SnipsNLUEngine
from snips_nlu.dataset import Dataset
from snips_nlu.default_configs import CONFIG_EN

from ..resources import snips_intents as intents

intents_dir = os.path.dirname(intents.__file__)

engine = SnipsNLUEngine(config=CONFIG_EN, seed=42)


def init():
    global engine
    dataset = Dataset.from_yaml_files(
        "en",
        [
            os.path.join(intents_dir, file)
            for file in rsc.contents(intents)
            if file.endswith((".yaml", ".yml"))
        ],
    )
    dhash = hashlib.md5()
    encoded = json.dumps(dataset.json, sort_keys=True).encode()
    dhash.update(encoded)
    dataset_hash = dhash.hexdigest()
    build = True

    md5_path = os.path.join("nlu_engine", "dataset.md5")
    if os.path.exists(md5_path):
        with open(md5_path) as f:
            hsh = f.read()
        if hsh == dataset_hash:
            build = False

    if build:
        engine.fit(dataset)
        shutil.rmtree("nlu_engine", ignore_errors=True)
        engine.persist("nlu_engine")
        with open(md5_path, "w") as f:
            f.write(dhash.hexdigest())
    else:
        engine = SnipsNLUEngine.from_path("nlu_engine")


def get_intent(text: str) -> Dict[str, Any]:
    intent = engine.parse(text.lower())
    data = {
        "intent_type": intent["intent"]["intentName"],
        **{slot["slotName"]: slot["rawValue"] for slot in intent["slots"]},
    }

    if data:
        return convert(data, "in")
    else:
        return None


if __name__ == "__main__":
    import sys

    pprint(engine.parse(sys.argv[1]))
