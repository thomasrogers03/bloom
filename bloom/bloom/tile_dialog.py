# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from . import edit_mode


class TileDialog:
    _TASK_CHAIN = 'tiles'

    def __init__(
        self,
        parent: core.NodePath,
        get_tile_async: typing.Callable[[int, typing.Callable[[core.Texture], None]], None],
        tile_count: int,
        edit_mode: edit_mode.EditMode,
        task_manager: Task.TaskManager
    ):
        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            frameSize=(-1.1, 1.1, -0.9, 0.9)
        )
        self._dialog.hide()
        self._frame = DirectGui.DirectScrolledFrame(
            parent=self._dialog,
            canvasSize=(0, 1, -1, 0),
            frameSize=(-1.05, 1.05, -0.8, 0.88),
            frameColor=(0.65, 0.65, 0.65, 1),
            relief=DirectGuiGlobals.SUNKEN,
            scrollBarWidth=0.04
        )
        self._canvas = self._frame.getCanvas()

        self._task_manager = task_manager
        self._task_manager.setupTaskChain(self._TASK_CHAIN, numThreads=1)

        self._edit_mode = edit_mode
        self._selected_tile: DirectGui.DirectFrame = None
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
                self._tile_frames[picnum] = frame

                callback = self._make_tile_callback(frame, left, self._top, picnum)
                get_tile_async(picnum, callback)

        frame_size = list(self._frame['canvasSize'])
        frame_size[2] = self._top
        self._frame['canvasSize'] = frame_size

        self._edit_mode['tiles'].append(self._tick)

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

            DirectGui.DirectButton(
                parent=parent_frame,
                frameSize=(0.01, frame_width - 0.01, -0.01, -(frame_height - 0.01)),
                frameTexture=texture,
                relief=DirectGuiGlobals.FLAT,
                command=self._select_tile,
                extraArgs=[picnum]
            )

        return _callback

    def _select_tile(self, picnum: int):
        if self._selected_tile is not None:
            self._selected_tile['frameColor'] = (0, 0, 0, 0)
        self._selected_tile = self._tile_frames[picnum]
        self._selected_tile['frameColor'] = (0, 0, 1, 1)
        self._selected_picnum = picnum

    def show(self, picnum: int):
        self._dialog.show()
        self._edit_mode.push_mode('tiles')

        if picnum < 0:
            picnum = 0

        self._select_tile(picnum)

        scroll_bar: DirectGui.DirectScrollBar = self._frame.verticalScroll
        value = self._selected_tile.get_z() / self._top
        scroll_bar.setValue(value)

    def hide(self):
        self._dialog.hide()
        self._edit_mode.pop_mode('tiles')

        return self._selected_picnum

    def _tick(self):
        pass
