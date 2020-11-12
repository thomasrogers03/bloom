# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import tkinter
import typing

from direct.showbase import DirectObject
from panda3d import bullet, core

from .. import (cameras, clicker, clicker_factory, constants, edit_menu,
                edit_mode)
from ..editor import map_editor


class EditMode(DirectObject.DirectObject):

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        menu: edit_menu.EditMenu,
        edit_mode_selector: 'bloom.edit_mode.EditMode'
    ):
        super().__init__()

        self._camera_collection = camera_collection
        self._edit_mode_selector = edit_mode_selector
        self._menu = menu

        self._tickers: typing.List[typing.Callable[[], None]] = []
        self._editor: map_editor.MapEditor = None
        self._clicker_factory = clicker_factory.ClickerFactory(
            self._edit_mode_selector.mouse_watcher,
            self._edit_mode_selector.task_manager
        )

    def set_editor(self, editor: map_editor.MapEditor):
        self._editor = editor

    def enter_mode(self):
        self._menu.clear()
        self._menu.add_command(
            label="Exit current mode (esc)",
            command=self._exit_current_mode
        )
        self._menu.add_separator()

    def tick(self):
        pass

    def exit_mode(self):
        self.ignore_all()

    def _exit_current_mode(self):
        self._edit_mode_selector.pop_mode()

    def _make_clicker(
        self,
        mouse_buttons: typing.List[core.MouseButton],
        on_click: typing.Callable[[], None] = None,
        on_double_click: typing.Callable[[], None] = None,
        on_click_move: typing.Callable[[core.Vec2], None] = None,
        on_click_after_move: typing.Callable[[], None] = None,
    ):
        return self._clicker_factory.make_clicker(
            mouse_buttons,
            on_click=on_click,
            on_double_click=on_double_click,
            on_click_move=on_click_move,
            on_click_after_move=on_click_after_move,
        ).append_tick_to(self._tickers)

    def tick(self):
        for ticker in self._tickers:
            ticker()
            if self._edit_mode_selector.tick_cancelled:
                break

