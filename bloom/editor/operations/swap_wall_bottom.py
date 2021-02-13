# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects


class SwapWallBottom:
    def __init__(self, wall: map_objects.EditorWall):
        self._wall = wall
        self._stat = self._wall.get_stat_for_part(None)

    def toggle(self):
        self._wall.invalidate_geometry()
        self._stat.bottom_swap = (self._stat.bottom_swap + 1) % 2
