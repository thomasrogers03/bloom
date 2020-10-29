# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import tkinter
import typing

from direct.showbase import DirectObject
from panda3d import core

from .. import clicker, constants, edit_menu, edit_mode
from ..editor import map_editor


class EditMode(DirectObject.DirectObject):

    def __init__(
        self,
        render: core.NodePath,
        scene: core.NodePath,
        builder_camera_2d: core.NodePath,
        builder_camera: core.NodePath,
        menu: edit_menu.EditMenu,
        edit_mode_selector: 'bloom.edit_mode.EditMode'
    ):
        super().__init__()

        self._render = render
        self._scene = scene
        self._builder_camera_2d = builder_camera_2d
        self._builder_camera = builder_camera
        self._edit_mode_selector = edit_mode_selector
        self._menu = menu

        self._tickers: typing.List[typing.Callable[[], None]] = []
        self._editor: map_editor.MapEditor = None

    def set_editor(self, editor: map_editor.MapEditor):
        self._editor = editor

    def enter_mode(self):
        self._menu.clear()

    def tick(self):
        pass

    def exit_mode(self):
        self.ignore_all()

    def _make_clicker(
        self,
        mouse_buttons: typing.List[core.MouseButton],
        on_click: typing.Callable[[], None] = None,
        on_double_click: typing.Callable[[], None] = None,
        on_click_move: typing.Callable[[core.Vec2], None] = None,
        on_click_after_move: typing.Callable[[], None] = None,
    ):
        return clicker.Clicker(
            self._edit_mode_selector.mouse_watcher,
            self._edit_mode_selector.task_manager,
            mouse_buttons,
            on_click=on_click,
            on_double_click=on_double_click,
            on_click_move=on_click_move,
            on_click_after_move=on_click_after_move,
        ).append_tick_to(self._tickers)

    def tick(self):
        for ticker in self._tickers:
            ticker()

    def _transform_to_camera_delta(self, delta: core.Vec2):
        heading = self._builder_camera.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))

        x_direction = sin_theta * delta.y + cos_theta * -delta.x
        y_direction = cos_theta * delta.y - sin_theta * -delta.x
        
        return core.Vec2(x_direction, y_direction) * constants.TICK_SCALE
