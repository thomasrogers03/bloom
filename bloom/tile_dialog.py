# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from . import constants, edit_mode, tile_view
from .edit_modes import empty_edit_mode
from .tiles import manager
from .utils import gui


class TileDialog(empty_edit_mode.EditMode):
    def __init__(
        self,
        parent: core.NodePath,
        tile_manager: manager.Manager,
        edit_mode: edit_mode.EditMode,
        task_manager: Task.TaskManager,
    ):
        self._dialog = DirectGui.DirectFrame(
            parent=parent, frameSize=(-1.1, 1.1, -0.9, 0.9)
        )
        self._dialog.hide()

        self._tile_manager = tile_manager
        self._tile_selected: typing.Optional[typing.Callable[[int], None]] = None
        DirectGui.DirectButton(
            parent=self._dialog,
            text="Ok",
            scale=0.05,
            pos=core.Vec3(0.81, -0.85),
            command=self._confirm,
        )
        DirectGui.DirectButton(
            parent=self._dialog,
            text="Cancel",
            scale=0.05,
            pos=core.Vec3(0.95, -0.85),
            command=self._hide,
        )

        self._tiles = tile_view.TileView(
            self._dialog,
            (-1.05, 1.05, -0.8, 0.88),
            self._tile_manager,
            self._select_tile,
        )
        self._tiles.load_tiles()

        self._task_manager = task_manager

        self._edit_mode = edit_mode
        self._selected_picnum: typing.Optional[int] = None

    @property
    def tile_manager(self):
        return self._tile_manager

    def _select_tile(self, picnum: int):
        if picnum == self._selected_picnum:
            self._confirm()

        self._selected_picnum = picnum
        self._task_manager.do_method_later(
            constants.DOUBLE_CLICK_TIMEOUT,
            self._reset_selected_picnum,
            "reset_double_click_tile",
        )

    def _reset_selected_picnum(self, task):
        self._selected_picnum = None
        return task.done

    def load_tiles(self, tile_indices: typing.List[int] = None):
        self._tiles.load_tiles(tile_indices)

    def show(self, picnum: int, tile_selected: typing.Callable[[int], None]):
        self._dialog.show()
        self._tile_selected = tile_selected
        self._edit_mode.push_mode(self)

        if picnum < 0:
            picnum = 0

        self._tiles.set_selected(picnum)

    def enter_mode(self, state: dict):
        pass

    def exit_mode(self):
        self._dialog.hide()
        self._tile_selected = None
        return {}

    def _confirm(self):
        self._selected_picnum = self._tiles.get_selected()
        callback = self._tile_selected
        self._hide()
        callback(self._selected_picnum)

    def _hide(self):
        self._edit_mode.pop_mode()

    def tick(self):
        pass
