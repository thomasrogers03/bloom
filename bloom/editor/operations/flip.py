# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects
from ..undo_stack import SimpleUndoableOperation, UndoStack


class Flip:
    def __init__(
        self, undo_stack: UndoStack, map_object: map_objects.EmptyObject, part: str
    ):
        self._undo_stack = undo_stack
        self._map_object = map_object
        self._part = part

    def flip(self):
        self._map_object.invalidate_geometry()

        with self._undo_stack.property_change(
            "Sprite/Wall Flip", self._map_object, self._part, "xflip", "yflip"
        ):
            if self._stat.xflip and self._stat.yflip:
                self._stat.xflip = 0
            elif self._stat.xflip:
                self._stat.xflip = 1
                self._stat.yflip = 1
            elif self._stat.yflip:
                self._stat.yflip = 0
            else:
                self._stat.xflip = 1

    @property
    def _stat(self):
        return self._map_object.get_stat_for_part(self._part)
