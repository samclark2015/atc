import inspect
from typing import Any, Callable, Dict, Tuple, Type


def requires_flightplan(
    func: Callable[[Type["Controller"], Dict[str, Any]], Tuple[str, Dict[str, Any]]]
):
    def wrapper(self: Type["Controller"], data: Dict[str, Any]):
        if not "fpl" in self.coordinator.state:
            return "request:clearance:notfiled", data
        return func(self, data)

    return wrapper


# def requires_readback(func: Callable[[Type["Controller"], Dict[str, Any]], Tuple[str, Dict[str, Any]]]):
#     def wrapper(self: Type["Controller"], data: Dict[str, Any]):

#     return wrapper


def handles(intent: str):
    def wrapper(
        func: Callable[[Type["Controller"], Dict[str, Any]], Tuple[str, Dict[str, Any]]]
    ):
        func.handles = intent
        return func

    return wrapper


class Controller:
    def __init__(self, coordinator) -> None:
        self.coordinator = coordinator
        self.handlers = {}
        self.prior = None
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(func, "handles"):
                self.handlers[func.handles] = func

    def periodic(self):
        pass

    def handle_request(
        self, intent: str, data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        if (
            "fpl" in self.coordinator.state
            and "callsign" in data
            and data["callsign"].lower()
            != self.coordinator.state["fpl"].callsign.lower()
        ):
            return "say_again", data

        if intent in self.handlers:
            self.prior = self.handlers[intent](data)
            return self.prior
        else:
            return "cant_handle", data

    def get_readback(self):
        utterance = next(self.coordinator.com.get_input())
        return utterance

    @handles("say_again")
    def handle_sayagain(self, data):
        if self.prior:
            return self.prior
