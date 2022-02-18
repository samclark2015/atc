import json
import random

import pyttsx3

reply_map = {
    "1": "one ",
    "2": "two ",
    "3": "three ",
    "4": "four ",
    "5": "five ",
    "6": "six ",
    "7": "seven ",
    "8": "eight ",
    "9": "niner ",
    "0": "zero ",
}

replies = json.load(open("replies.json"))
engine = pyttsx3.init()


def respond(reply_type, data={}):
    options = replies.get(reply_type)
    if not options:
        message = "Sorry, I don't know how to respond to that."

    message: str = random.choice(options)
    message = message.format_map(data)
    print(message)
    for entry in reply_map:
        message = message.replace(entry, reply_map[entry])

    engine.say(message)
    engine.runAndWait()
