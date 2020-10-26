# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core


class Clicker:
    ALL_MOUSE_BUTTONS = {
        core.MouseButton.one(),
        core.MouseButton.two(),
        core.MouseButton.three(),
        core.MouseButton.four(),
        core.MouseButton.five()
    }
    ALL_BUTTONS = ALL_MOUSE_BUTTONS.union({
        core.KeyboardButton.control(),
        core.KeyboardButton.shift()
    })

    def __init__(
        self,
        watcher: core.MouseWatcher,
        mouse_buttons: typing.List[core.MouseButton],
        on_click: typing.Callable[[], None] = None,
        on_click_move: typing.Callable[[core.Vec2], None] = None,
        on_click_after_move: typing.Callable[[], None] = None,
    ):
        self._watcher = watcher
        self._mouse_buttons = set(mouse_buttons)
        self._unwanted_mouse_buttons = self.ALL_BUTTONS - self._mouse_buttons
        self._on_click = on_click
        self._on_click_move = on_click_move
        self._on_click_after_move = on_click_after_move

        self._mouse_down_point: core.Point2() = None
        self._last_mouse_point: core.Point2() = None
        self._delta: core.Vec2 = None
        self._moved_when_down = False

    def tick(self):
        if not self._watcher.has_mouse():
            return

        x = self._watcher.get_mouse_x()
        y = self._watcher.get_mouse_y()
        mouse_point = core.Point2(x, y)

        if self._buttons_down():
            if self._mouse_down_point is None:
                self._mouse_down_point = mouse_point
                self._last_mouse_point = mouse_point

            delta: core.Vec2 = mouse_point - self._last_mouse_point
            total_delta: core.Vec2 = mouse_point - self._mouse_down_point
            moved = delta.length() > 0.0025

            if moved:
                self._moved_when_down = True
                if self._on_click_move is not None:
                    self._on_click_move(total_delta, delta)

            self._last_mouse_point = mouse_point
        else:
            if self._mouse_down_point is not None:
                if self._no_mouse_buttons_down():
                    if not self._moved_when_down:
                        if self._on_click is not None:
                            self._on_click()
                    else:
                        if self._on_click_after_move is not None:
                            self._on_click_after_move()
                self._mouse_down_point = None
                self._moved_when_down = False

    def _buttons_down(self):
        return self._wanted_buttons_down() and not self._any_unwanted_buttons_down()

    def _wanted_buttons_down(self):
        return all(self._watcher.is_button_down(button) for button in self._mouse_buttons)

    def _any_unwanted_buttons_down(self):
        return any(
            self._watcher.is_button_down(button)
            for button in self._unwanted_mouse_buttons
        )

    def _no_mouse_buttons_down(self):
        return not any(self._watcher.is_button_down(button) for button in self.ALL_MOUSE_BUTTONS)
