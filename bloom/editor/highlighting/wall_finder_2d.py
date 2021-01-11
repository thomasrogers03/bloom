# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects


class WallFinder2D:
    _MIN_DISTANCE = 1 / 32768

    def __init__(self, position: core.Point2, grid_size: float, view_scale: float):
        self._position = position
        self._min_distance = self._MIN_DISTANCE * grid_size * view_scale

    def closest_wall(self, walls: typing.List[map_objects.EditorWall]):
        closest_distance = self._min_distance
        closest_wall: map_objects.EditorWall = None

        for wall in walls:
            projected_point = wall.line_segment.project_point(self._position)
            if projected_point is None:
                continue

            distance_to_wall = (self._position - projected_point).length()
            if distance_to_wall < closest_distance:
                closest_distance = distance_to_wall
                closest_wall = wall

        return closest_wall, closest_distance

    def closest_vertex(self, walls: typing.List[map_objects.EditorWall]):
        closest_distance = self._min_distance
        closest_wall: map_objects.EditorWall = None

        for wall in walls:
            distance_to_point = (self._position - wall.point_1).length()
            if distance_to_point < closest_distance:
                closest_distance = distance_to_point
                closest_wall = wall

        return closest_wall, closest_distance
