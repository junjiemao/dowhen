# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .event_handler import EventHandler


E = sys.monitoring.events


class Instrumenter:
    def __new__(self, *args, **kwargs):
        if not hasattr(self, "_instance"):
            self._instance = super().__new__(self)
            self._instance._intialized = False
        return self._instance

    def __init__(self, tool_id=4):
        if not self._intialized:
            self.tool_id = tool_id
            self.line_handlers = {}
            self.return_handlers = {}
            self.start_handlers = {}

            sys.monitoring.use_tool_id(self.tool_id, "dowhen instrumenter")
            sys.monitoring.register_callback(self.tool_id, E.LINE, self.line_callback)
            sys.monitoring.register_callback(
                self.tool_id, E.PY_RETURN, self.return_callback
            )
            sys.monitoring.register_callback(
                self.tool_id, E.PY_START, self.start_callback
            )
            self._intialized = True

    def clear_all(self):
        for code in self.line_handlers:
            sys.monitoring.set_local_events(self.tool_id, code, E.NO_EVENTS)
        for code in self.start_handlers:
            sys.monitoring.set_local_events(self.tool_id, code, E.NO_EVENTS)
        for code in self.return_handlers:
            sys.monitoring.set_local_events(self.tool_id, code, E.NO_EVENTS)
        self.line_handlers.clear()
        self.start_handlers.clear()
        self.return_handlers.clear()

    def submit(self, event_handler: EventHandler):
        event = event_handler.event
        if event.event_type == "line":
            self.register_line_event(
                event.code,
                event.event_data["line_number"],
                event_handler,
            )
        elif event.event_type == "start":
            self.register_start_event(event.code, event_handler)
        elif event.event_type == "return":
            self.register_return_event(event.code, event_handler)

    def register_line_event(self, code, line_number, event_handler: EventHandler):
        if code not in self.line_handlers:
            self.line_handlers[code] = {}
        if line_number not in self.line_handlers[code]:
            self.line_handlers[code][line_number] = []
        self.line_handlers[code][line_number].append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.LINE)
        sys.monitoring.restart_events()

    def line_callback(self, code, line_number):  # pragma: no cover
        if code in self.line_handlers and line_number in self.line_handlers[code]:
            for handler in self.line_handlers[code][line_number]:
                handler(sys._getframe(1))
        else:
            return sys.monitoring.DISABLE

    def register_start_event(self, code, event_handler: EventHandler):
        if code not in self.start_handlers:
            self.start_handlers[code] = []
        self.start_handlers[code].append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_START)
        sys.monitoring.restart_events()

    def start_callback(self, code, offset):  # pragma: no cover
        if code in self.start_handlers:
            for handler in self.start_handlers[code]:
                handler(sys._getframe(1))
        else:
            return sys.monitoring.DISABLE

    def register_return_event(self, code, event_handler: EventHandler):
        if code not in self.return_handlers:
            self.return_handlers[code] = []
        self.return_handlers[code].append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_RETURN)
        sys.monitoring.restart_events()

    def return_callback(self, code, offset, retval):  # pragma: no cover
        if code in self.return_handlers:
            for handler in self.return_handlers[code]:
                handler(sys._getframe(1))
        else:
            return sys.monitoring.DISABLE

    def remove_handler(self, event_handler: EventHandler):
        event = event_handler.event
        if (
            event.event_type == "line"
            and event.code in self.line_handlers
            and event.event_data["line_number"] in self.line_handlers[event.code]
            and event_handler
            in self.line_handlers[event.code][event.event_data["line_number"]]
        ):
            self.line_handlers[event.code][event.event_data["line_number"]].remove(
                event_handler
            )
            if not self.line_handlers[event.code][event.event_data["line_number"]]:
                del self.line_handlers[event.code][event.event_data["line_number"]]
            if not self.line_handlers[event.code]:
                del self.line_handlers[event.code]
                events = sys.monitoring.get_local_events(self.tool_id, event.code)
                sys.monitoring.set_local_events(
                    self.tool_id, event.code, events & ~E.LINE
                )
        elif (
            event.event_type == "start"
            and event.code in self.start_handlers
            and event_handler in self.start_handlers[event.code]
        ):
            self.start_handlers[event.code].remove(event_handler)
            if not self.start_handlers[event.code]:
                del self.start_handlers[event.code]
                events = sys.monitoring.get_local_events(self.tool_id, event.code)
                sys.monitoring.set_local_events(
                    self.tool_id, event.code, events & ~E.PY_START
                )
        elif (
            event.event_type == "return"
            and event.code in self.return_handlers
            and event_handler in self.return_handlers[event.code]
        ):
            self.return_handlers[event.code].remove(event_handler)
            if not self.return_handlers[event.code]:
                del self.return_handlers[event.code]
                events = sys.monitoring.get_local_events(self.tool_id, event.code)
                sys.monitoring.set_local_events(
                    self.tool_id, event.code, events & ~E.PY_RETURN
                )


def clear_all():
    Instrumenter().clear_all()
