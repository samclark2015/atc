from collections import defaultdict
from threading import Thread
from typing import *

from edifice import App, Button, Component, Label, View, register_props
from edifice.base_components import CustomWidget
from edifice.state import _add_subscription
from PyQt5.QtCore import QObject, pyqtSignal
from pyqtlet2 import L, MapWidget

from ...com.snips_input import init as input_init
from ...controllers.coordinator import Coordinator
from .speech import SpeechCom


class MyButton(Button):
    @register_props
    def __init__(self, title: Any = "", disabled=False, **kwargs):
        super().__init__(title, **kwargs)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = super()._qt_update_commands(children, newprops, newstate)

        if "disabled" in newprops:
            commands.append((self.underlying.setDisabled, newprops["disabled"]))

        return commands


class ThreadSafeStateValue(QObject):
    setSignal = pyqtSignal(object)

    """Container to store a value and rerender on value change.

    A StateValue stores an underlying Python object.
    Components can subscribe to the StateValue.
    StateValues are modified by the set method, which will trigger re-renders
    for all subscribed components.

    Args:
        initial_value: the initial value for the StateValue
    """

    def __init__(self, initial_value: Any):
        super().__init__()
        self._value = initial_value
        self._subscriptions = dict()
        self.setSignal.connect(self._set)

    def _set_subscriptions(self, new_subscriptions):
        # This helper method is overridden by StateManager
        self._subscriptions = new_subscriptions

    def subscribe(self, component: Component) -> Any:
        """Subscribes a component to this value's updates and returns the current value.

        Call this method in the Component render method (or after Component mounts).

        Args:
            component: Edifice Component
        Returns:
            Current value.
        """
        self._set_subscriptions(_add_subscription(self._subscriptions, component))
        return self._value

    @property
    def value(self) -> Any:
        """Returns the current value.

        **This will not subscribe your component to this value. Changes in the value will not cause your component to rerender!!!**

        Most of the time you probably want to use subscribe.

        Returns:
            Current value.
        """
        return self._value

    def _set(self, value: Any):
        """Sets the current value and trigger rerender.

        Re-renders will only be triggered for subscribed components.
        If an exception occurs while re-rendering, all changes are unwound
        and the StateValue retains the old value.

        Args:
            value: value to set to.
        Returns:
            None
        """
        old_value = self._value
        try:
            self._value = value
            by_app = defaultdict(list)
            for comp in self._subscriptions:
                by_app[comp._controller].append(comp)

            for app, components in by_app.items():
                app._request_rerender(components, {})
        except Exception as e:
            self._value = old_value
            raise e

    def set(self, value):
        self.setSignal.emit(value)


class MapView(CustomWidget):
    @register_props
    def __init__(self, points):
        ...

    def create_widget(self):
        widget = MapWidget()

        self.map = L.map(widget)
        L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png").addTo(self.map)

        return widget

    def paint(self, widget: MapWidget, newprops: Dict[str, Any]):
        if "points" in newprops:
            for layer in self.map.layers:
                self.map.removeLayer(layer)
            for label, (lat, lon) in newprops["points"]:
                marker = L.marker([lat, lon])
                marker.bindTooltip(label)
                self.map.addLayer(self.marker)


class MainView(Component):
    def __init__(self, coord):
        super().__init__()
        self.coord = coord
        self.talking = False

    def render(self):
        loading = STATE["loading"].subscribe(self)
        points = STATE["points"].subscribe(self)

        if loading:
            children = [Label("Loading...")]
        else:
            children = [
                # MapView(points),
                MyButton(
                    "Push to Speak",
                    disabled=self.talking,
                    on_click=lambda e: Thread(target=self.ptt).start(),
                )
            ]
        return View(layout="row")(*children)  # Layout children in a row

    def ptt(self):
        self.set_state(talking=True)
        self.coord.listen()
        self.set_state(talking=False)


STATE = {"loading": ThreadSafeStateValue(True), "points": ThreadSafeStateValue([])}


class UIFrontend:
    def __init__(self, connector) -> None:
        self.connector = connector
        self.com = SpeechCom()

    def bg_task(self):
        input_init()
        STATE["loading"].set(False)

    def start(self):
        coordinator = Coordinator(self.com, self.connector)
        window = MainView(coordinator)

        Thread(target=self.bg_task).start()
        App(window).start()
