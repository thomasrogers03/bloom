# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.task import Task
from panda3d import core

from . import clicker, edit_mode


class ClickerFactory:

    def __init__(
        self, 
        mouse_watcher: core.MouseWatcher, 
        task_manager: Task.TaskManager
    ):
        self._mouse_watcher = mouse_watcher
        self._task_manager = task_manager

    def make_clicker(
        self,
        mouse_buttons: typing.List[core.MouseButton],
        on_mouse_down: typing.Callable[[core.Point2], None] = None,
        on_click: typing.Callable[[], None] = None,
        on_double_click: typing.Callable[[], None] = None,
        on_click_move: typing.Callable[[core.Vec2], None] = None,
        on_click_after_move: typing.Callable[[], None] = None
    ):
        return clicker.Clicker(
            self._mouse_watcher,
            self._task_manager,
            mouse_buttons,
            on_mouse_down=on_mouse_down,
            on_click=on_click,
            on_double_click=on_double_click,
            on_click_move=on_click_move,
            on_click_after_move=on_click_after_move,
        )
