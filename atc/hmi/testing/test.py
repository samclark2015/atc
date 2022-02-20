from threading import Event
from time import sleep

from ...com.snips_input import init as input_init
from ...controllers.coordinator import Coordinator


class TestFrontend:
    def __init__(self, file, conn):
        self.file = open(file)
        self.conn = conn
        self.wait_event = Event()
        self.more = True

    def get_input(self):
        line: str = self.file.readline()
        self.more = bool(line)
        if not self.more:
            return None

        while line.strip().startswith("@wait"):
            print("< {}".format(line))
            comps = line.strip().split(" ")
            if len(comps) == 1:
                self.wait_event.wait()
            elif len(comps) == 2:
                sleep(float(comps[1]))
            line = self.file.readline()
        print("< {}".format(line))
        return line

    def respond(self, text: str):
        if "takeoff" in text:
            self.conn.takeoff()

        if "descend" in text:
            self.conn.descent()
        
        if "approach" in text:
            self.conn.approach()

        print("> {}".format(text))

        self.wait_event.set()
        self.wait_event.clear()

    def start(self):
        input_init()
        coordinator = Coordinator(self, self.conn)
        try:
            while self.more:
                coordinator.listen()
        except KeyboardInterrupt:
            pass
        finally:
            coordinator.cleanup()
