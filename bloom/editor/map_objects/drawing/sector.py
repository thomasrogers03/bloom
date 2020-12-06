# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ... import segment
from ..wall import EditorWall


class SubSector(typing.NamedTuple):
    outer_wall: EditorWall
    inner_walls: typing.List[EditorWall]

class Sector:

    def __init__(self, walls: typing.List[EditorWall]):
        self._walls = walls

    @staticmethod
    def point_in_shape(shape: typing.List[core.Point2], point: core.Point2):
        ray_start = core.Point2(-(1 << 31), point.y)
        intersecting = 0
        for point_1, point_2 in zip(shape, shape[1:] + shape[:1]):
            max_y = max(point_1.y, point_2.y)
            min_y = min(point_1.y, point_2.y)
            if min_y <= point.y and max_y > point.y:
                wall_segment = segment.Segment(point_1, point_2)
                start_side = wall_segment.side_of_line(ray_start)
                side = wall_segment.side_of_line(point)
                if start_side != side:
                    intersecting += 1

        return intersecting % 2 == 1

    @staticmethod
    def are_points_clockwise(points: typing.List[core.Point2]):
        winding = 0
        segments = zip(points, (points[1:] + points[:1]))
        for point_1, point_2 in segments:
            winding += (point_2.x - point_1.x) * (point_2.y + point_1.y)

        return winding > 0

    @staticmethod
    def is_sector_section_clockwise(start_wall: EditorWall):
        points = Sector.get_wall_bunch_points(start_wall)
        return Sector.are_points_clockwise(points)

    @staticmethod
    def get_wall_bunch_points(start_wall: EditorWall):
        points: typing.List[core.Point2] = []
        current_wall = start_wall.wall_point_2
        
        while current_wall != start_wall:
            points.append(current_wall.point_1)
            current_wall = current_wall.wall_point_2
        points.append(current_wall.point_1)

        return points

    def get_sub_sectors(self):
        handled: typing.Set[EditorWall] = set()
        inner_walls = self._get_inner_walls()
        result: typing.List[SubSector] = []

        for outer_wall in self._iterate_outer_walls():
            bunch_points = self.get_wall_bunch_points(outer_wall)
            sub_sector = SubSector(outer_wall, [])
            result.append(sub_sector)
            for inner_wall in inner_walls:
                if inner_wall in handled:
                    continue
                
                if self.point_in_shape(bunch_points, inner_wall.point_1):
                    sub_sector.inner_walls.append(inner_wall)
                    for wall in inner_wall.iterate_wall_bunch():
                        handled.add(wall)

        return result

    def _iterate_outer_walls(self):
        seen: typing.Set[EditorWall] = set()

        for wall in self._walls:
            if wall in seen:
                continue

            if not self.is_sector_section_clockwise(wall):
                yield wall

            for sub_wall in wall.iterate_wall_bunch():
                seen.add(sub_wall)

    def _get_inner_walls(self):
        seen: typing.Set[EditorWall] = set()
        result: typing.List[EditorWall] = []

        for wall in self._walls:
            if wall in seen:
                continue

            if self.is_sector_section_clockwise(wall):
                result.append(wall)

            for sub_wall in wall.iterate_wall_bunch():
                seen.add(sub_wall)

        return result
