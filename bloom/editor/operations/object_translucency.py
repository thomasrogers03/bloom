# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects


class ObjectTranslucency:
    def __init__(self, map_object: map_objects.EmptyObject, part: str):
        self._map_object = map_object
        self._part = part

    def toggle(self):
        self._map_object.invalidate_geometry()

        stat = self._map_object.get_stat_for_part(self._part)
        if stat.translucent:
            stat.translucent = 0
        elif stat.translucent_rev:
            stat.translucent_rev = 0
            stat.translucent = 1
        else:
            stat.translucent_rev = 1

        if (
            isinstance(self._map_object, map_objects.EditorWall)
            and self._map_object.other_side_wall is not None
        ):
            other_side_wall: map_objects.EditorWall = self._map_object.other_side_wall
            other_side_wall.invalidate_geometry()
            other_side_stat = other_side_wall.get_stat_for_part(None)
            other_side_stat.blocking = stat.blocking
            other_side_stat.blocking2 = stat.blocking2
