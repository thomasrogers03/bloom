# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import re
import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from ... import constants
from ...audio import sound_view
from ...utils import gui
from ..descriptors.object_property import Property
from ..descriptors.sprite_type import SpriteType

_PROPERTY_LIST_TYPE = typing.List[typing.Tuple[str, Property]]


class SpritePropertyView:
    _PROPERTY_WIDTH = 0.7
    _PROPERTY_PADDING = 0.02

    def __init__(
        self,
        parent: core.NodePath,
        default_tile: int,
        properties: typing.Dict[str, Property],
        sound_browser: sound_view.SoundView,
        update_tile: typing.Callable[[int], None],
        canvas_height: float,
        frame_width: float,
        frame_height: float,
        alpha=1,
    ):
        self._canvas_height = canvas_height
        self._frame_width = frame_width
        self._frame_height = frame_height

        self._frame = DirectGui.DirectScrolledFrame(
            parent=parent,
            frameSize=(0, self._frame_width, 0.05, self._frame_height + 0.05),
            frameColor=(0.65, 0.65, 0.65, alpha),
            state=DirectGuiGlobals.NORMAL,
            scrollBarWidth=0.04,
            relief=DirectGuiGlobals.SUNKEN,
        )
        self._bind_scroll(self._frame)
        self._canvas = self._frame.getCanvas()
        self._default_tile = default_tile
        self._properties = properties
        self._sound_browser = sound_browser
        self._update_tile = update_tile
        self.get_current_tile: typing.Callable[[], int] = lambda: None

        property_list: _PROPERTY_LIST_TYPE = list(self._properties.items())
        property_count = len(property_list)
        columns = math.ceil(property_count / self._property_rows)

        self._frame["canvasSize"] = (
            0,
            columns * self._padded_property_width + 0.2,
            -self._canvas_height,
            0,
        )

        self._value_setters: typing.Dict[str, typing.Any] = {}
        for column in range(columns):
            for row in range(self._property_rows):
                index = column * self._property_rows + row
                if index >= property_count:
                    break

                name, descriptor = property_list[index]

                x = column * (self._padded_property_width) + self._PROPERTY_PADDING / 4
                y = -(row + 1) * self._property_height

                label = DirectGui.DirectLabel(
                    parent=self._canvas,
                    pos=core.Vec3(x, y),
                    text=name,
                    scale=constants.TEXT_SIZE,
                    text_align=core.TextNode.A_left,
                    frameColor=(0, 0, 0, 0),
                )
                self._bind_scroll(label)

                label_size = label.node().get_frame() * constants.TEXT_SIZE
                label_width = (label_size[1] - label_size[0]) + self._PROPERTY_PADDING
                width_left = (self._PROPERTY_WIDTH - label_width) / constants.TEXT_SIZE

                if descriptor.property_type == Property.INTEGER_PROPERTY:
                    setter = DirectGui.DirectEntry(
                        parent=self._canvas,
                        pos=core.Vec3(x + label_width, y),
                        width=width_left,
                        frameColor=(1, 1, 1, 1),
                        relief=DirectGuiGlobals.SUNKEN,
                        scale=constants.TEXT_SIZE,
                        initialText=str(descriptor.value - descriptor.offset),
                    )
                elif descriptor.property_type == Property.BOOLEAN_PROPERTY:
                    setter = DirectGui.DirectCheckButton(
                        parent=self._canvas,
                        pos=core.Vec3(
                            x + self._PROPERTY_WIDTH, y + constants.TEXT_SIZE / 2
                        ),
                        scale=constants.TEXT_SIZE,
                        indicatorValue=descriptor.value ^ descriptor.offset,
                    )
                elif descriptor.property_type == Property.SOUND_PROPERTY:
                    setter = DirectGui.DirectButton(
                        parent=self._canvas,
                        pos=core.Vec3(
                            x + self._PROPERTY_WIDTH, y + constants.TEXT_SIZE / 2
                        ),
                        scale=constants.TEXT_SIZE,
                        text="Browse",
                        command=self._browse_sounds,
                        text_align=core.TextNode.A_right,
                    )
                    setter.set_python_tag("sound_index", descriptor.value)
                elif descriptor.property_type == Property.ENUM_PROPERTY:
                    items = list(descriptor.enum_values.keys())
                    setter = DirectGui.DirectOptionMenu(
                        parent=self._canvas,
                        pos=core.Vec3(x + label_width, y),
                        scale=constants.TEXT_SIZE,
                        items=items,
                    )
                    setter.set(descriptor.reverse_enum_values[descriptor.value])
                    setter.set_python_tag("enum_values", descriptor.enum_values)
                else:
                    raise ValueError(
                        f"Invalid property type {descriptor.property_type}"
                    )

                self._bind_scroll(setter)
                self._value_setters[name] = setter

                setter["state"] = DirectGuiGlobals.NORMAL
                setter["extraArgs"] = [setter, descriptor]
                if descriptor.tile_link_type == Property.TILE_LINK_OFFSET:
                    self._setup_tile_link_offset_setter(setter, descriptor)

    def get_values(self):
        new_values: typing.Dict[str, typing.Union[bool, int]] = {}
        for property_name, setter in self._value_setters.items():
            descriptor = self._properties[property_name]
            if descriptor.property_type == Property.INTEGER_PROPERTY:
                value = self._validate_setter_integer_value(setter) + descriptor.offset
            elif descriptor.property_type == Property.BOOLEAN_PROPERTY:
                value = bool(setter["indicatorValue"]) ^ descriptor.offset
            elif descriptor.property_type == Property.SOUND_PROPERTY:
                value = setter.get_python_tag("sound_index") + descriptor.offset
            elif descriptor.property_type == Property.ENUM_PROPERTY:
                enum_name = setter.get()
                value = (
                    setter.get_python_tag("enum_values")[enum_name] + descriptor.offset
                )
            new_values[property_name] = value

        return new_values

    def destroy(self):
        self._frame.destroy()

    def _validate_setter_integer_value(self, setter):
        value = setter.get()
        if not re.match("^-?[0-9]+$", value):
            setter.set("0")
            return 0
        return int(value)

    @property
    def _property_height(self):
        return constants.TEXT_SIZE + 0.04

    @property
    def _padded_property_width(self):
        return self._PROPERTY_WIDTH + self._PROPERTY_PADDING

    @property
    def _property_rows(self):
        return int(self._canvas_height / self._property_height)

    def _browse_sounds(self, setter: DirectGui.DirectButton, descriptor: Property):
        def _update_sound(sound_index):
            setter.set_python_tag("sound_index", sound_index)

        current_sound_index = setter.get_python_tag("sound_index")
        self._sound_browser.show(current_sound_index, _update_sound)

    def _setup_tile_link_offset_setter(
        self, setter: DirectGui.DirectEntry, descriptor: Property
    ):
        if descriptor.property_type != Property.INTEGER_PROPERTY:
            message = (
                f"Invalid property type for tile offset {descriptor.property_type}"
            )
            raise ValueError(message)

        def _update():
            self._update_with_offset(setter.get(), setter, descriptor)

        def _get_tile():
            return self._get_offset_tile(setter.get(), descriptor)

        setter["command"] = self._update_with_offset
        setter["focusOutCommand"] = _update
        self.get_current_tile = _get_tile

    def _update_with_offset(
        self, value: str, setter: DirectGui.DirectEntry, descriptor: Property
    ):
        value = self._get_offset_tile(value, descriptor)
        self._update_tile(value)

    def _get_offset_tile(self, value: str, descriptor: Property):
        return self._default_tile + int(value) + descriptor.offset

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
    def _scroll_bar(self) -> DirectGui.DirectScrollBar:
        return self._frame.verticalScroll
