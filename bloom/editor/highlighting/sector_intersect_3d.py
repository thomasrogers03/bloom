# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from ... import constants
from .. import map_objects


class SectorIntersect3D:

    def __init__(self, sector: map_objects.EditorSector):
        self._sector = sector

    def closest_object_intersecting_line(self, point: core.Point3, direction: core.Vec3):
        normalized_direction = direction.normalized()

        normal_2d_length = core.Vec2(
            normalized_direction.x,
            normalized_direction.y
        ).length()

        closest_object = None
        closest_part: str = None
        closest_distance_squared = constants.REALLY_BIG_NUMBER * constants.REALLY_BIG_NUMBER
        closest_hit: core.Point3 = None

        part = self._sector.part_for_direction(normalized_direction)
        if part == map_objects.EditorSector.FLOOR_PART:
            hit = self._sector.floor_plane.intersect_line(point, normalized_direction)
        else:
            hit = self._sector.ceiling_plane.intersect_line(
                point, normalized_direction)
        if hit is not None and self._sector.point_in_sector(core.Point2(hit.x, hit.y)):
            closest_object = self._sector
            closest_part = part
            closest_hit = hit
            closest_distance_squared = (hit - point).length_squared()

        for editor_wall in self._sector.walls:
            intersection = editor_wall.intersect_line(
                point,
                normalized_direction
            )
            if intersection is not None:
                hit, distance_squared = self._hit_3d_and_squared_distance_from_hit_2d(
                    intersection,
                    point,
                    normal_2d_length,
                    normalized_direction
                )
                if hit is not None:
                    if distance_squared < closest_distance_squared:
                        part = editor_wall.get_part_at_point(hit)
                        closest_hit = hit
                        closest_distance_squared = distance_squared
                        closest_object = editor_wall
                        closest_part = part

        for editor_sprite in self._sector.sprites:
            intersection = editor_sprite.intersect_line(
                point,
                direction
            )
            if intersection is not None:
                hit, distance_squared = self._hit_3d_and_squared_distance_from_hit_2d(
                    intersection,
                    point,
                    normal_2d_length,
                    normalized_direction
                )
                if hit is not None:
                    if distance_squared < closest_distance_squared:
                        part = editor_sprite.get_part_at_point(hit)
                        if part is not None:
                            closest_hit = hit
                            closest_distance_squared = distance_squared
                            closest_object = editor_sprite
                            closest_part = part

        return closest_object, closest_part, closest_hit

    def _hit_3d_and_squared_distance_from_hit_2d(
        self,
        intersection_2d: core.Point2,
        point: core.Point3,
        normal_2d_length: float,
        normal: core.Vec3
    ):
        point_2d = core.Point2(point.x, point.y)
        line_portion = (intersection_2d - point_2d).length() / normal_2d_length

        hit = core.Point3(
            intersection_2d.x,
            intersection_2d.y,
            point.z + normal.z * line_portion
        )

        above_floor = hit.z <= self._sector.floor_z_at_point(intersection_2d)
        below_ceiling = hit.z >= self._sector.ceiling_z_at_point(intersection_2d)
        if above_floor and below_ceiling:
            return hit, (hit - point).length_squared()
        return None, None

