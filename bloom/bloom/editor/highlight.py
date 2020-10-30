# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math

from panda3d import core

from . import empty_selector


class Highlight:

    def __init__(self, colour: core.Vec3, item, part: str, selector: empty_selector.Selector):
        self.colour = colour
        self.item = item
        self._part = part
        self.selector = selector

        self._start_colour = self._display.get_color_scale()
        if self._start_colour.w < 1:
            self._highlight_alpha = 0.25
        else:
            self._highlight_alpha = 1.0

    def __eq__(self, obj):
        return isinstance(obj, Highlight) and obj.item == self.item and obj._part == self._part

    def tick(self, ticks):
        if self._display.is_empty():
            return

        colour_scale = ((math.sin(ticks / 6.0) + 1) / 8) + 0.75
        self._display.set_color_scale(
            self.colour.x * colour_scale,
            self.colour.y * colour_scale,
            self.colour.z * colour_scale,
            self._highlight_alpha
        )

    def remove(self):
        if not self._display.is_empty():
            self._display.set_color_scale(self._start_colour)
            self.item.hide_debug()

    @property
    def _display(self) -> core.NodePath:
        return self.item.get_geometry_part(self._part)
