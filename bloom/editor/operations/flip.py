# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects
from .undo_stack import SimplyUndoableOperation, UndoStack

class Flip:

    def __init__(self, undo_stack: UndoStack, map_object: map_objects.EmptyObject, part: str):
        self._undo_stack = undo_stack
        self._map_object = map_object
        self._stat = map_object.get_stat_for_part(part)

    def flip(self):
        self._map_object.invalidate_geometry()

        previous_xflip = self._stat.xflip
        previous_yflip = self._stat.yflip
        
        if self._stat.xflip and self._stat.yflip:
            self._stat.xflip = 0
        elif self._stat.xflip:
            self._stat.xflip = 1
            self._stat.yflip = 1
        elif self._stat.yflip:
            self._stat.yflip = 0
        else:
            self._stat.xflip = 1

        new_xflip = self._stat.xflip
        new_yflip = self._stat.yflip

        def _undo():
            self._map_object.invalidate_geometry()
            self._stat.xflip = previous_xflip
            self._stat.yflip = previous_yflip

        def _redo():
            self._map_object.invalidate_geometry()
            self._stat.xflip = new_xflip
            self._stat.yflip = new_yflip

        operation = SimplyUndoableOperation(
            'Sprite/Wall Flip', 
            _undo,
            _redo
        )
        self._undo_stack.add_operation(operation)
