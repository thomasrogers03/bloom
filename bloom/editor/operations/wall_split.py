# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from ..map_objects import wall


class WallSplit:

    def __init__(self, wall_to_split: wall.EditorWall):
        self._wall_to_split = wall_to_split

    def split(self, where: core.Point2):
        if where == self._wall_to_split.point_1 or where == self._wall_to_split.point_2:
            raise ValueError('Invalid split!')

        self._do_split(self._wall_to_split, where)
        if self._wall_to_split.other_side_wall is not None:
            split = self._do_split(
                self._wall_to_split.other_side_wall, 
                where
            )
            self._wall_to_split.link(split, force=True)

    def _do_split(self, wall_to_split: wall.EditorWall, where: core.Point2):
        wall_to_split.invalidate_geometry()

        new_blood_wall = wall_to_split.blood_wall.copy()
        new_blood_wall.wall.position_x = int(where.x)
        new_blood_wall.wall.position_y = int(where.y)

        new_wall_point_2 = wall_to_split.sector.add_wall(new_blood_wall)
        new_wall_point_2.wall_previous_point = wall_to_split
        new_wall_point_2.setup(
            wall_to_split.wall_point_2,
            wall_to_split.other_side_wall,
            []
        )

        wall_to_split.wall_point_2.wall_previous_point = new_wall_point_2
        wall_to_split.set_wall_point_2(new_wall_point_2)

        return new_wall_point_2
