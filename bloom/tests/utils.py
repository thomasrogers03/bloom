# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import cv2
import numpy
from panda3d import core

from .. import map_data
from ..editor import map_objects
from ..editor.operations import sector_draw

_IMAGE_SIZE = 512


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

def save_sector_images(
    base_name: str, 
    sector: map_objects.EditorSector,
    all_sectors: map_objects.SectorCollection
):
    rectangle = core.Point4(65536, -65536, 65536, -65536)
    for wall in sector.walls:
        if wall.point_1.x < rectangle.x:
            rectangle.x = wall.point_1.x
        if wall.point_1.x > rectangle.y:
            rectangle.y = wall.point_1.x
        
        if wall.point_1.y < rectangle.z:
            rectangle.z = wall.point_1.y
        if wall.point_1.y > rectangle.w:
            rectangle.w = wall.point_1.y

    x_offset = (rectangle.y - rectangle.x) * 0.35
    y_offset = (rectangle.w - rectangle.z) * 0.35
    rectangle.x -= x_offset
    rectangle.y += x_offset
    rectangle.z -= y_offset
    rectangle.w += y_offset

    offset = -core.Vec2(rectangle.x, rectangle.z)

    scale_x = _IMAGE_SIZE / (rectangle.y - rectangle.x)
    scale_y = _IMAGE_SIZE / (rectangle.w - rectangle.z)

    if scale_y < scale_x:
        scale = scale_y
    else:
        scale = scale_x

    image = numpy.zeros((_IMAGE_SIZE, _IMAGE_SIZE, 3), 'uint8')
    image = cv2.putText(
        image, 
        str(all_sectors.sectors.index(sector)), 
        (_IMAGE_SIZE // 2, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    for wall in sector.walls:
        image = _draw_wall(wall, offset, scale, (255, 255, 255), 4, image)

    for wall in sector.walls:
        point_1 = _image_point(wall.point_1, offset, scale)
        if wall.other_side_sector is not None:
            image = _draw_wall(wall.other_side_wall, offset, scale, (0, 0, 255), 2, image)

            text = str(all_sectors.sectors.index(wall.other_side_sector))
            text_point = wall.origin_2d + wall.get_direction() / 2
            text_point = text_point + wall.get_normal() * 0.25
            text_point = _image_point(text_point, offset, scale)
            image = cv2.putText(
                image, 
                text, 
                text_point,
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

    path = f'test_results/{base_name}.png'
    cv2.imwrite(path, image)

def _draw_wall(wall: map_objects.EditorWall, offset: core.Vec2, scale: float, colour, thickness, image):
    point_1 = _image_point(wall.point_1, offset, scale)
    point_2 = _image_point(wall.point_2, offset, scale)

    image = cv2.arrowedLine(image, point_1, point_2, colour, thickness)
    
    centre = wall.point_1 + wall.get_direction() / 2
    normal = centre - (wall.get_normal() * 16) / scale

    centre = _image_point(centre, offset, scale)
    normal = _image_point(normal, offset, scale)

    return cv2.arrowedLine(image, centre, normal, colour, thickness)

def _image_point(point: core.Point2, offset: core.Vec2, scale: float) -> typing.Tuple[int, int]:
    x = (point.x + offset.x) * scale
    y = _IMAGE_SIZE - (point.y + offset.y) * scale - 1

    return (int(x), int(y))

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
    