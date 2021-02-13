# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from ... import editor
from .. import map_objects


class WallRepeatAdjust:
    def __init__(self, wall: map_objects.EditorWall):
        self._wall = wall
        self._previous_length = wall.get_length()

    def adjust(self):
        self._wall.invalidate_geometry()

        with self._wall.change_blood_object():
            new_length = self._wall.get_length()
            if self._previous_length > 0:
                ratio = self._wall.x_repeat / self._previous_length
            else:
                ratio = 8

            self._wall.blood_wall.wall.repeat_x = editor.to_build_repeat_x(
                ratio * new_length
            )
