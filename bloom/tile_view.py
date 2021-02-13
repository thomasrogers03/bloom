# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from . import constants
from .tiles import manager
from .utils import gui


class TileView:
    def __init__(
        self,
        parent: DirectGui.DirectFrame,
        frame_size: typing.Tuple[float, float, float, float],
        tile_manager: manager.Manager,
        on_tile_selected: typing.Callable[[int], None],
    ):
        self._tile_manager = tile_manager
        self._on_tile_selected = on_tile_selected
        self._tile_indices: typing.Optional[typing.List[int]] = None

        self._frame = DirectGui.DirectScrolledFrame(
            parent=parent,
            canvasSize=(0, 1, -1, 0),
            frameSize=frame_size,
            frameColor=(0.65, 0.65, 0.65, 1),
            relief=DirectGuiGlobals.SUNKEN,
            scrollBarWidth=0.04,
            state=DirectGuiGlobals.NORMAL,
        )
        self._bind_scroll(self._frame)

        self._selected_tile: DirectGui.DirectFrame = None
        self._tile_frames: typing.Dict[int, DirectGui.DirectFrame] = {}

    def load_tiles(self, tile_indices: typing.List[int] = None):
        if tile_indices is None:
            tile_indices = self._tile_manager.get_all_tiles()

        if tile_indices == self._tile_indices:
            return

        self._tile_indices = tile_indices

        for frame in self._tile_frames.values():
            frame.hide()

        tile_count = len(tile_indices)
        row_count = math.ceil(tile_count / 10)

        self._top = 0.2
        for y in range(row_count):
            self._top -= 0.2
            for x in range(10):
                left = x * 0.2
                picnum_index = y * 10 + x
                if picnum_index >= tile_count:
                    break

                picnum = tile_indices[picnum_index]

                frame = self._get_tile_frame(picnum)
                frame.set_pos(core.Vec3(left, 0, self._top))
                frame.show()
        self._top = min(-1, self._top)

        frame_size = list(self._frame["canvasSize"])
        frame_size[2] = self._top
        self._frame["canvasSize"] = frame_size

    def _get_tile_frame(self, picnum: int):
        if picnum not in self._tile_frames:
            frame = DirectGui.DirectButton(
                parent=self._canvas,
                frameSize=(0, 0.2, 0, -0.2),
                frameColor=(0, 0, 0, 0),
                relief=DirectGuiGlobals.FLAT,
                command=self._select_tile,
                extraArgs=[picnum],
            )
            frame.set_python_tag("picnum", picnum)
            self._bind_scroll(frame)
            self._tile_frames[picnum] = frame

            callback = self._make_tile_callback(frame, picnum)
            self._tile_manager.get_tile_async(picnum, 0, callback)

        return self._tile_frames[picnum]

    def set_selected(self, picnum: int):
        self._select_tile(picnum)

        if self._selected_tile is not None:
            value = self._selected_tile.get_z() / self._top
            self._scroll_bar.setValue(value)

    def get_selected(self) -> int:
        return self._selected_tile.get_python_tag("picnum")

    def _bind_scroll(self, control):
        gui.bind_scroll(control, self._scroll_up, self._scroll_down)

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

    def _make_tile_callback(self, parent_frame: DirectGui.DirectFrame, picnum: int):
        def _callback(texture: core.Texture):
            if parent_frame.is_empty():
                return

            frame_size = gui.size_inside_square_for_texture(texture, 0.2)

            if frame_size is None:
                return

            tile = DirectGui.DirectButton(
                parent=parent_frame,
                frameSize=(0.01, frame_size.x - 0.01, -0.01, -(frame_size.y - 0.01)),
                frameTexture=texture,
                relief=DirectGuiGlobals.FLAT,
                command=self._select_tile,
                extraArgs=[picnum],
            )
            self._bind_scroll(tile)

            tile_number = DirectGui.DirectLabel(
                parent=tile,
                pos=core.Vec3(0, 0, -constants.TEXT_SIZE),
                scale=constants.TEXT_SIZE,
                text=str(picnum),
                frameColor=(0, 0, 0, 0),
                text_align=core.TextNode.A_left,
                text_fg=(1, 1, 1, 0.75),
            )
            self._bind_scroll(tile_number)

        return _callback

    def _select_tile(self, picnum: int):
        if self._selected_tile is not None:
            self._selected_tile["frameColor"] = (0, 0, 0, 0)
        self._selected_tile = self._tile_frames[picnum]
        self._selected_tile["frameColor"] = (0, 0, 1, 1)

        self._on_tile_selected(picnum)

    @property
    def _canvas(self):
        return self._frame.getCanvas()

    @property
    def _scroll_bar(self) -> DirectGui.DirectScrollBar:
        return self._frame.verticalScroll
