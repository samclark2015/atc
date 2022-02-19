from threading import Event
from time import sleep


class TextCom:
    def __init__(self, file, conn):
        self.file = file
        self.conn = conn
        self.wait_event = Event()

    def get_input(self):
        line: str
        for line in self.file:
            if line.strip().startswith("@wait"):
                print("< {}".format(line))
                comps = line.strip().split(" ")
                if len(comps) == 1:
                    self.wait_event.wait()
                elif len(comps) == 2:
                    sleep(float(comps[1]))
                continue
            print("< {}".format(line))
            yield line

    def respond(self, text: str):
        if "takeoff" in text:
            self.conn.takeoff()

        print("> {}".format(text))

        self.wait_event.set()
        self.wait_event.clear()
