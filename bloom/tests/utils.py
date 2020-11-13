# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import cv2
from panda3d import core

from .. import map_data
from ..editor import map_objects
from ..editor.operations import sector_draw


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
    point_2.teleport_point_1_to(core.Point2(right, bottom))

    point_3 = sector.add_wall(map_data.wall.Wall())
    point_3.teleport_point_1_to(core.Point2(right, top))

    point_4 = sector.add_wall(map_data.wall.Wall())
    point_4.teleport_point_1_to(core.Point2(left, top))

    point_1.set_wall_point_2(point_2)
    point_2.set_wall_point_2(point_3)
    point_3.set_wall_point_2(point_4)
    point_4.set_wall_point_2(point_1)

    return sector

def assert_wall_bunch_not_clockwise(
    sector: map_objects.EditorSector, 
    start_point: core.Point2
):
    first_wall = find_wall_on_point(sector, start_point)
    if sector_draw.is_sector_section_clockwise(first_wall):
        directions = _get_wall_bunch_directions(first_wall)
        directions_string = _join_lines(directions)
        message = f'Sector wall bunch starting at {start_point} was clockwise:\n{directions_string}'
        raise AssertionError(message)


def assert_wall_bunch_clockwise(
    sector: map_objects.EditorSector, 
    start_point: core.Point2
):
    first_wall = find_wall_on_point(sector, start_point)
    if not sector_draw.is_sector_section_clockwise(first_wall):
        directions = _get_wall_bunch_directions(first_wall)
        directions_string = _join_lines(directions)
        message = f'Sector wall bunch starting at {start_point} was not clockwise:\n{directions_string}'
        raise AssertionError(message)

def assert_sector_has_shape(
    sector: map_objects.EditorSector, 
    *points: typing.List[core.Point2]
):
    wall_count = len(sector.walls)
    point_count = len(points)
    if wall_count != point_count:
        raise AssertionError(f'Sector wall count ({wall_count}) did not match expected ({point_count})')

    for point in points:
        assert_sector_has_point(sector, point)

def assert_sector_has_point(sector: map_objects.EditorSector, point: core.Point2):
    points: typing.List[core.Point2] = []
    for wall in sector.walls:
        points.append(wall.point_1)
        if wall.point_1 == point:
            return

    raise AssertionError(f'Point, {point}, not found in {points}')

def _get_wall_bunch_directions(start_wall: map_objects.EditorWall):
    result: typing.List[core.Vec2] = []
    
    current_wall = start_wall.wall_point_2
    while current_wall != start_wall:
        result.append(current_wall.get_direction())
        current_wall = current_wall.wall_point_2
    result.append(current_wall.point_1)

    return result

def _join_lines(values: list):
    values = [str(value) for value in values]
    return '\n'.join(values)
    