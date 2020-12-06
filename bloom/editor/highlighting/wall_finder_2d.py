# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import map_objects


class WallFinder2D:
    _MIN_DISTANCE = 1 / 128

    def __init__(self, sector: map_objects.EditorSector, position: core.Point2, view_scale: float):
        self._sector = sector
        self._position = position
        self._min_distance = self._MIN_DISTANCE * view_scale

    def closest_wall(self):
        closest_distance = self._min_distance
        closest_wall: map_objects.EditorWall = None

        for wall in self._sector.walls:
            projected_point = wall.line_segment.project_point(self._position)
            if projected_point is None:
                continue

            distance_to_wall = (self._position - projected_point).length()
            if distance_to_wall < closest_distance:
                closest_distance = distance_to_wall
                closest_wall = wall

        return closest_wall, closest_distance

    def closest_vertex(self):
        closest_distance = self._min_distance
        closest_wall: map_objects.EditorWall = None

        for wall in self._sector.walls:
            distance_to_point = (self._position - wall.point_1).length()
            if distance_to_point < closest_distance:
                closest_distance = distance_to_point
                closest_wall = wall

        return closest_wall, closest_distance
