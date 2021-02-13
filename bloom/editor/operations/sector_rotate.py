# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import map_objects


class SectorRotate:
    def __init__(self, sector: map_objects.EditorSector):
        self._sector = sector

    def rotate(self, amount_in_degrees: float):
        self._sector.invalidate_geometry()

        centre = core.Point2(0, 0)
        for wall in self._sector.walls:
            centre += wall.point_1
        centre /= len(self._sector.walls)

        rotation: core.Mat3 = core.Mat3.rotate_mat(amount_in_degrees)
        for wall in self._sector.walls:
            offset_point = wall.point_1 - centre
            new_point = rotation.xform_point(offset_point) + centre

            walls_at_point = wall.all_walls_at_point_1()
            for other_wall in walls_at_point:
                other_wall.teleport_point_1_to(new_point)
