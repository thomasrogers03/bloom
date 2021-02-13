# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects


class SwapWallPeg:
    def __init__(self, wall: map_objects.EditorWall, part: str):
        self._wall = wall
        self._stat = self._wall.get_stat_for_part(part)

    def toggle(self):
        self._wall.invalidate_geometry()
        self._stat.align = (self._stat.align + 1) % 2
