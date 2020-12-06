# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from ... import constants
from ...tiles import manager
from ...utils import gui
from ..descriptors import sprite_type_descriptor


class SpriteTypeList:
    _SPRITE_FRAME_SIZE = 0.16
    _PADDING = 0.01

    def __init__(
        self,
        parent: core.NodePath,
        tile_manager: manager.Manager,
        handle_type_selected: typing.Callable[[sprite_type_descriptor.SpriteTypeDescriptor], None]
    ):
        self._tile_manager = tile_manager
        self._handle_type_selected = handle_type_selected

        self._frame = DirectGui.DirectScrolledFrame(
            parent=parent,
            pos=core.Vec3(0.04, 0),
            canvasSize=(0, 0.54, -1, 0),
            frameSize=(0, 0.6, 0.05, 1.68),
            frameColor=(0.65, 0.65, 0.65, 1),
            relief=DirectGuiGlobals.SUNKEN,
            scrollBarWidth=0.04,
            state=DirectGuiGlobals.NORMAL
        )
        self._selected_frame: DirectGui.DirectButton = None
        self._sprite_frames: typing.List[DirectGui.DirectButton] = []
        self._bind_scroll(self._frame)
        self._top = 0

    def clear(self):
        self._top = 0
        for frame in self._sprite_frames:
            frame.destroy()
        self._sprite_frames.clear()
        self._selected_frame = None

    def add_sprite_type(self, descriptor: sprite_type_descriptor.SpriteTypeDescriptor):
        frame = DirectGui.DirectButton(
            parent=self._canvas,
            pos=core.Vec3(0, self._top),
            frameColor=(0, 0, 0, 0),
            frameSize=(0, 0.54, -self._SPRITE_FRAME_SIZE, 0),
            relief=DirectGuiGlobals.FLAT,
            command=self._select_sprite_type,
        )
        frame['extraArgs'] = [frame]
        self._bind_scroll(frame)
        frame.set_python_tag('descriptor', descriptor)

        texture = self._tile_manager.get_tile(
            descriptor.default_tile,
            descriptor.palette or 0
        )

        texture_frame_size = gui.size_inside_square_for_texture(
            texture,
            self._SPRITE_FRAME_SIZE
        )

        if texture_frame_size is None:
            return

        y_offset = (texture_frame_size.y - self._SPRITE_FRAME_SIZE) / 2

        sprite_frame = DirectGui.DirectButton(
            parent=frame,
            pos=core.Vec3(0, y_offset),
            frameSize=(0, texture_frame_size.x, 0, -texture_frame_size.y),
            frameTexture=texture,
            relief=DirectGuiGlobals.FLAT,
            command=self._select_sprite_type,
            extraArgs=[frame]
        )
        sprite_frame.set_transparency(True)
        self._bind_scroll(sprite_frame)

        word_wrap = (0.54 - texture_frame_size.x) / constants.LARGE_TEXT_SIZE
        frame_size = core.Vec4(
            0,
            0.54 - texture_frame_size.x - 0.02,
            self._SPRITE_FRAME_SIZE / 2,
            -self._SPRITE_FRAME_SIZE / 2
        ) / constants.LARGE_TEXT_SIZE
        label_frame = DirectGui.DirectButton(
            parent=frame,
            pos=core.Vec3(texture_frame_size.x + 0.02, -self._SPRITE_FRAME_SIZE / 2),
            scale=constants.LARGE_TEXT_SIZE,
            text=descriptor.name,
            relief=DirectGuiGlobals.FLAT,
            frameSize=frame_size,
            frameColor=(0, 0, 0, 0),
            text_align=core.TextNode.A_left,
            text_wordwrap=word_wrap,
            command=self._select_sprite_type,
            extraArgs=[frame]
        )
        self._bind_scroll(label_frame)

        self._top -= self._SPRITE_FRAME_SIZE + self._PADDING
        self._update_canvas_size()

        self._sprite_frames.append(frame)

    def set_current_type(self, descriptor: sprite_type_descriptor.SpriteTypeDescriptor):
        for frame in self._sprite_frames:
            frame_descriptor = self._get_frame_descriptor(frame)
            if frame_descriptor == descriptor:
                self._set_selected_frame(frame)
                break

        if self._selected_frame is not None:
            value = self._selected_frame.get_z() / self._top
            self._scroll_bar.setValue(value)

    def _select_sprite_type(self, frame: DirectGui.DirectButton):
        if self._selected_frame is not None:
            self._selected_frame['frameColor'] = (0, 0, 0, 0)

        self._set_selected_frame(frame)
        self._handle_type_selected(self._get_frame_descriptor(frame))

    def _set_selected_frame(self, frame: DirectGui.DirectButton):
        self._selected_frame = frame
        self._selected_frame['frameColor'] = (0, 0, 1, 1)

    @staticmethod
    def _get_frame_descriptor(frame: core.NodePath) -> sprite_type_descriptor.SpriteTypeDescriptor:
        return frame.get_python_tag('descriptor')

    def _update_canvas_size(self):
        frame_size = list(self._frame['canvasSize'])
        frame_size[2] = self._top
        self._frame['canvasSize'] = frame_size

    def _bind_scroll(self, control):
        gui.bind_scroll(control, self._scroll_up, self._scroll_down)

    def _scroll_up(self, event):
        new_value = self._scroll_bar.getValue() - 0.03
        if new_value < 0:
            new_value = 0
        self._scroll_bar.setValue(new_value)

    def _scroll_down(self, event):
        new_value = self._scroll_bar.getValue() + 0.03
        if new_value > 1:
            new_value = 1
        self._scroll_bar.setValue(new_value)

    @property
    def _canvas(self):
        return self._frame.getCanvas()

    @property
    def _scroll_bar(self) -> DirectGui.DirectScrollBar:
        return self._frame.verticalScroll
