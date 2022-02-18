from reply import respond
from speech import get_intent

handlers = {
    "info:contact": ...,
}


def parse_intent(intent):
    if intent is None:
        respond("garbled")
        return 
    print(intent)
    type_ = intent["intent_type"]
    response = handlers[type_](intent)
    respond(response, intent)
    
if __name__ == "__main__":
    while True:
        input("Press enter to continue...")
        intent = get_intent()
        parse_intent(intent)
