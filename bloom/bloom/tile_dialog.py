# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from . import constants, edit_mode


class TileDialog:
    def __init__(
        self,
        parent: core.NodePath,
        get_tile_async: typing.Callable[[int, typing.Callable[[core.Texture], None]], None],
        tile_count: int,
        edit_mode: edit_mode.EditMode,
        task_manager: Task.TaskManager,
        tile_selected: typing.Callable[[int], None]
    ):
        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            frameSize=(-1.1, 1.1, -0.9, 0.9)
        )
        self._dialog.hide()

        self._tile_selected = tile_selected
        DirectGui.DirectButton(
            parent=self._dialog,
            text='Ok',
            scale=0.05,
            pos=core.Vec3(0.81, -0.85),
            command=self._confirm
        )
        DirectGui.DirectButton(
            parent=self._dialog,
            text='Cancel',
            scale=0.05,
            pos=core.Vec3(0.95, -0.85),
            command=self._hide
        )

        self._frame = DirectGui.DirectScrolledFrame(
            parent=self._dialog,
            canvasSize=(0, 1, -1, 0),
            frameSize=(-1.05, 1.05, -0.8, 0.88),
            frameColor=(0.65, 0.65, 0.65, 1),
            relief=DirectGuiGlobals.SUNKEN,
            scrollBarWidth=0.04,
            state=DirectGuiGlobals.NORMAL
        )
        self._bind_scroll(self._frame)
        self._canvas = self._frame.getCanvas()

        self._task_manager = task_manager

        self._edit_mode = edit_mode
        self._selected_tile: DirectGui.DirectFrame = None
        self._clicked_tile: DirectGui.DirectFrame = None
        self._tile_frames: typing.List[DirectGui.DirectFrame] = [None] * tile_count

        self._top = 0.2
        for y in range(int(tile_count / 10)):
            self._top -= 0.2
            for x in range(10):
                left = x * 0.2
                picnum = y * 10 + x

                frame = DirectGui.DirectButton(
                    parent=self._canvas,
                    pos=core.Vec3(left, 0, self._top),
                    frameSize=(0, 0.2, 0, -0.2),
                    frameColor=(0, 0, 0, 0),
                    relief=DirectGuiGlobals.FLAT,
                    command=self._select_tile,
                    extraArgs=[picnum]
                )
                self._bind_scroll(frame)
                self._tile_frames[picnum] = frame

                callback = self._make_tile_callback(frame, left, self._top, picnum)
                get_tile_async(picnum, callback)

        frame_size = list(self._frame['canvasSize'])
        frame_size[2] = self._top
        self._frame['canvasSize'] = frame_size

    def _bind_scroll(self, control):
        control.bind(DirectGuiGlobals.WHEELUP, self._scroll_up)
        control.bind(DirectGuiGlobals.WHEELDOWN, self._scroll_down)

    def _scroll_up(self, event):
        new_value = self._scroll_bar.getValue() - 0.01
        if new_value < 0:
            new_value = 0
        self._scroll_bar.setValue(new_value)

    def _scroll_down(self, event):
        new_value = self._scroll_bar.getValue() + 0.01
        if new_value > 1:
            new_value = 1
        self._scroll_bar.setValue(new_value)

    def _make_tile_callback(self, parent_frame: DirectGui.DirectFrame, left: float, top: float, picnum: int):
        def _callback(texture: core.Texture):
            width = texture.get_x_size()
            height = texture.get_y_size()
            if width < 1 or height < 1:
                return

            if width > height:
                frame_height = (height / width) * 0.2
                frame_width = 0.2
            else:
                frame_height = 0.2
                frame_width = (width / height) * 0.2

            tile = DirectGui.DirectButton(
                parent=parent_frame,
                frameSize=(0.01, frame_width - 0.01, -0.01, -(frame_height - 0.01)),
                frameTexture=texture,
                relief=DirectGuiGlobals.FLAT,
                command=self._select_tile,
                extraArgs=[picnum]
            )
            self._bind_scroll(tile)

        return _callback

    def _select_tile(self, picnum: int):
        if self._selected_tile is not None:
            self._selected_tile['frameColor'] = (0, 0, 0, 0)
        self._selected_tile = self._tile_frames[picnum]
        self._selected_tile['frameColor'] = (0, 0, 1, 1)
        self._selected_picnum = picnum

        if self._selected_tile == self._clicked_tile:
            self._confirm()

        self._clicked_tile = self._selected_tile
        self._task_manager.do_method_later(
            constants.DOUBLE_CLICK_TIMEOUT, self._reset_clicked_tile, 'reset_double_click_tile')

    def _reset_clicked_tile(self, task):
        self._clicked_tile = None
        return task.done

    def show(self, picnum: int):
        self._dialog.show()
        self._edit_mode.push_mode(self)

        if picnum < 0:
            picnum = 0

        self._select_tile(picnum)

        value = self._selected_tile.get_z() / self._top
        self._scroll_bar.setValue(value)

    def enter_mode(self):
        pass

    def exit_mode(self):
        self._dialog.hide()

    @property
    def _scroll_bar(self) -> DirectGui.DirectScrollBar:
        return self._frame.verticalScroll

    def _confirm(self):
        self._hide()
        self._tile_selected(self._selected_picnum)

    def _hide(self):
        self._edit_mode.pop_mode()

    def tick(self):
        pass
