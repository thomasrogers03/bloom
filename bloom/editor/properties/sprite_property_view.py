# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from ... import constants
from .sprite_type_descriptor import SpriteProperty, SpriteTypeDescriptor

_PROPERTY_LIST_TYPE = typing.List[
    typing.Tuple[
        str,
        SpriteProperty
    ]
]


class SpritePropertyView:
    _FRAME_HEIGHT = 1.25
    _PROPERTY_HEIGHT = constants.TEXT_SIZE + 0.04
    _PROPERTY_WIDTH = 0.5
    _PROPERTY_ROWS = int(_FRAME_HEIGHT / _PROPERTY_HEIGHT)

    def __init__(
        self,
        parent: core.NodePath,
        default_tile: int,
        properties: typing.Dict[str, SpriteProperty],
        update_tile: typing.Callable[[int], None]
    ):
        self._frame = DirectGui.DirectFrame(
            parent=parent,
            pos=core.Vec3(0.66, 0),
            frameSize=(0, self._FRAME_HEIGHT, 0.05, 1.68),
            frameColor=(0, 0, 0, 0),
        )
        self._default_tile = default_tile
        self._properties = properties
        self._update_tile = update_tile

        property_list: _PROPERTY_LIST_TYPE = list(self._properties.items())
        property_count = len(property_list)
        columns = math.ceil(property_count / self._PROPERTY_ROWS)

        self._value_setters = {}
        for column in range(columns):
            for row in range(self._PROPERTY_ROWS):
                index = column * self._PROPERTY_ROWS + row
                if index >= property_count:
                    break

                name, descriptor = property_list[index]

                x = column * (self._PROPERTY_WIDTH + 0.02)
                y = 1.68 - (row + 1) * self._PROPERTY_HEIGHT

                label = DirectGui.DirectLabel(
                    parent=self._frame,
                    pos=core.Vec3(x, y),
                    text=name,
                    scale=constants.TEXT_SIZE,
                    text_align=core.TextNode.A_left
                )

                if descriptor.property_type == SpriteTypeDescriptor.INTEGER_PROPERTY:
                    label_size = label.node().get_frame() * constants.TEXT_SIZE
                    label_width = (label_size[1] - label_size[0]) + 0.02
                    width_left = (
                        self._PROPERTY_WIDTH - label_width
                    ) / constants.TEXT_SIZE
                    setter = DirectGui.DirectEntry(
                        parent=self._frame,
                        pos=core.Vec3(x + label_width, y),
                        width=width_left,
                        frameColor=(1, 1, 1, 1),
                        relief=DirectGuiGlobals.SUNKEN,
                        scale=constants.TEXT_SIZE,
                        initialText=str(descriptor.value - descriptor.offset)
                    )
                elif descriptor.property_type == SpriteTypeDescriptor.BOOLEAN_PROPERTY:
                    setter = DirectGui.DirectCheckButton(
                        parent=self._frame,
                        pos=core.Vec3(
                            x + self._PROPERTY_WIDTH,
                            y + constants.TEXT_SIZE / 2
                        ),
                        scale=constants.TEXT_SIZE,
                        indicatorValue=descriptor.value ^ descriptor.offset
                    )
                else:
                    raise ValueError(
                        f'Invalid property type {descriptor.property_type}'
                    )

                self._value_setters[name] = setter

                setter['state'] = DirectGuiGlobals.NORMAL
                setter['extraArgs'] = [descriptor]
                if descriptor.tile_link_type == SpriteTypeDescriptor.TILE_LINK_OFFSET:
                    if descriptor.property_type != SpriteTypeDescriptor.INTEGER_PROPERTY:
                        message = f'Invalid property type for tile offset {descriptor.property_type}'
                        raise ValueError(message)

                    setter['command'] = self._update_with_offset
                    setter['focusOutCommand'] = lambda: self._update_with_offset(setter.get(), descriptor)

    def _update_with_offset(self, value, descriptor: SpriteProperty):
        value = int(value) + descriptor.offset
        self._update_tile(self._default_tile + value)

    def get_values(self):
        new_values: typing.Dict[str, typing.Union[bool, int]] = {}
        for property_name, setter in self._value_setters.items():
            descriptor = self._properties[property_name]
            if descriptor.property_type == SpriteTypeDescriptor.INTEGER_PROPERTY:
                value = int(setter.get()) + descriptor.offset
            elif descriptor.property_type == SpriteTypeDescriptor.BOOLEAN_PROPERTY:
                value = bool(setter['indicatorValue']) ^ descriptor.offset
            new_values[property_name] = value

        return new_values

    def destroy(self):
        self._frame.destroy()
