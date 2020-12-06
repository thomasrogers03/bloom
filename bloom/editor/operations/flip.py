# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class Flip:

    def __init__(self, map_object: map_objects.EmptyObject, part: str):
        self._map_object = map_object
        self._stat = map_object.get_stat_for_part(part)

    def flip(self):
        self._map_object.invalidate_geometry()
        
        if self._stat.xflip and self._stat.yflip:
            self._stat.xflip = 0
        elif self._stat.xflip:
            self._stat.xflip = 1
            self._stat.yflip = 1
        elif self._stat.yflip:
            self._stat.yflip = 0
        else:
            self._stat.xflip = 1