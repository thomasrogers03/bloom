# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import map_data
from ..editor import map_objects


def find_wall_on_point(sector: map_objects.EditorSector, point: core.Point2):
    for wall in sector.walls:
        if wall.point_1 == point:
            return wall

    raise ValueError('Point not found')

def build_rectangular_sector(
    all_sectors: map_objects.SectorCollection,
    left: float,
    right: float,
    bottom: float,
    top: float
):
    sector = all_sectors.new_sector(map_data.sector.Sector())

    point_1 = sector.add_wall(map_data.wall.Wall())
    point_1.teleport_point_1_to(core.Point2(left, bottom))

    point_2 = sector.add_wall(map_data.wall.Wall())
    point_2.teleport_point_1_to(core.Point2(left, top))

    point_3 = sector.add_wall(map_data.wall.Wall())
    point_3.teleport_point_1_to(core.Point2(right, top))

    point_4 = sector.add_wall(map_data.wall.Wall())
    point_4.teleport_point_1_to(core.Point2(right, bottom))

    point_1.set_wall_point_2(point_2)
    point_2.set_wall_point_2(point_3)
    point_3.set_wall_point_2(point_4)
    point_4.set_wall_point_2(point_1)

    return sector
