import sys

from padatious.intent_container import IntentContainer

container = IntentContainer('intent_cache')
container.load_file('contact', 'intents/contact.intent')

if __name__ == "__main__":
    container.train()

    data = container.calc_intent(sys.argv[1])
    print(data)
