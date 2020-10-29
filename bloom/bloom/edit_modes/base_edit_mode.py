# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.showbase import DirectObject
from panda3d import core

from .. import clicker, edit_mode
from ..editor import map_editor


class EditMode(DirectObject.DirectObject):

    def __init__(
        self,
        render: core.NodePath,
        scene: core.NodePath,
        builder_camera_2d: core.NodePath,
        builder_camera: core.NodePath,
        edit_mode_selector: 'bloom.edit_mode.EditMode'
    ):
        super().__init__()

        self._render = render
        self._scene = scene
        self._builder_camera_2d = builder_camera_2d
        self._builder_camera = builder_camera
        self._edit_mode_selector = edit_mode_selector
        self._tickers: typing.List[typing.Callable[[], None]] = []

        self._editor: map_editor.MapEditor = None

    def set_editor(self, editor: map_editor.MapEditor):
        self._editor = editor

    def enter_mode(self):
        pass

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
