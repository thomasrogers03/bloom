# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects


class ToggleWallMiddle:

    def __init__(self, wall: map_objects.EditorWall, part: str):
        self._wall = wall
        self._part = part
        self._stat = self._wall.get_stat_for_part(self._part)

    def toggle(self):
        self._toggle_single_wall()
        if self._wall.other_side_wall is not None:
            self._wall.other_side_wall.invalidate_geometry()
            stat = self._wall.other_side_wall.get_stat_for_part(self._part)
            stat.masking = self._stat.masking

    def _toggle_single_wall(self):
        self._wall.invalidate_geometry()
        if self._stat.masking == 1:
            self._stat.masking = 0
        else:
            self._stat.masking = 1
            self._wall.blood_wall.wall.over_picnum = 0
