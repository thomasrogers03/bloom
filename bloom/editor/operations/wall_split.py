# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from ..geometry import wall_repeat_adjust
from ..map_objects import wall
from .. import undo_stack


class WallSplit:
    def __init__(self, wall_to_split: wall.EditorWall, where: core.Point2):
        self._wall_to_split = wall_to_split
        self._where = where

    def split(self):
        if (
            self._where == self._wall_to_split.point_1
            or self._where == self._wall_to_split.point_2
        ):
            return

        with self._wall_to_split.undos.multi_step_undo("Wall Split"):
            self._do_split()
            if self._wall_to_split.other_side_wall is not None:
                other_side_wall = self._wall_to_split.other_side_wall
                other_side_wall.unlink()
                WallSplit(other_side_wall, self._where).split()

                self._wall_to_split.link(other_side_wall.wall_point_2)

                point_2 = self._wall_to_split.wall_point_2
                point_2.link(other_side_wall)

    def _do_split(self):
        self._wall_to_split.invalidate_geometry()
        repeat_adjust = wall_repeat_adjust.WallRepeatAdjust(self._wall_to_split)

        new_blood_wall = self._wall_to_split.blood_wall.copy()
        new_blood_wall.wall.position_x = int(self._where.x)
        new_blood_wall.wall.position_y = int(self._where.y)

        new_wall_point_2 = self._wall_to_split.sector.add_wall(new_blood_wall)
        new_wall_point_2.set_wall_point_2(self._wall_to_split.wall_point_2)

        self._wall_to_split.set_wall_point_2(new_wall_point_2)

        new_wall_point_2.reset_panning_and_repeats(None)
        repeat_adjust.adjust()

        return new_wall_point_2
