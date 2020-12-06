# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import typing

from panda3d import bullet, core

from .. import cameras, clicker, constants
from ..editor import grid_snapper, map_objects, operations
from ..editor.map_objects.sector import EditorSector
from ..utils import shapes
from . import grid_display, navigation_mode_3d


class DrawingDisplay:

    def __init__(
        self,
        camera_collection: cameras.Cameras
    ):
        self._camera_collection = camera_collection
        self._sector: map_objects.EditorSector = None
        self._debug_view: core.NodePath = None
        self._grid = grid_display.GridDisplay(self._camera_collection, self._camera_collection.scene)
        self._grid.hide()

        self.show_grid = self._grid.show
        self.hide_grid = self._grid.hide

    def start_drawing(
        self, 
        sector: map_objects.EditorSector, 
        hit_position: core.Point3, 
        snapper: grid_snapper.GridSnapper
    ):
        self._sector = sector
        self._grid.update(snapper, hit_position, sector)

    def update(self, current_point: core.Point2, drawing_points: typing.List[core.Point2], insert: bool):
        self.clear_debug()

        segments = core.LineSegs()
        segments.set_thickness(4)

        points = drawing_points
        if current_point is not None:
            points = points + [current_point]

        if not points:
            return

        second_points = points[1:]
        if insert:
            second_points += points[:1]
        walls = zip(points, second_points)

        for point_1, point_2 in walls:
            point_3d_1 = core.Point3(
                point_1.x,
                point_1.y,
                self._floor_z_at_point(point_1)
            )
            segments.draw_to(point_3d_1)

            point_3d = core.Point3(
                point_1.x,
                point_1.y,
                self._ceiling_z_at_point(point_1)
            )
            segments.draw_to(point_3d)

            point_3d = core.Point3(
                point_2.x,
                point_2.y,
                self._ceiling_z_at_point(point_2)
            )
            segments.draw_to(point_3d)

            point_3d = core.Point3(
                point_2.x,
                point_2.y,
                self._floor_z_at_point(point_2)
            )
            segments.draw_to(point_3d)

            segments.draw_to(point_3d_1)

        debug_view_node = segments.create('draw_debug')

        self._debug_view = self._camera_collection.scene.attach_new_node(
            debug_view_node
        )
        self._debug_view.set_depth_write(False)
        self._debug_view.set_depth_test(False)
        self._debug_view.set_bin('fixed', constants.FRONT_MOST)

    def clear_debug(self):
        if self._debug_view is not None:
            self._debug_view.remove_node()
            self._debug_view = None

    def _floor_z_at_point(self, point: core.Point2):
        if self._sector is None:
            return 0
        return self._sector.floor_z_at_point(point)

    def _ceiling_z_at_point(self, point: core.Point2):
        if self._sector is None:
            return 0
        return self._sector.ceiling_z_at_point(point)

    def _floor_slope_direction(self):
        if self._sector is None:
            return core.Vec2(0, 0)
        return self._sector.floor_slope_direction()
