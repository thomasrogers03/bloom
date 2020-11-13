# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math
import typing

from panda3d import bullet, core

from .. import clicker, constants
from ..editor import operations
from ..editor.map_objects.sector import EditorSector
from ..utils import grid
from . import navigation_mode_3d


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._sector: EditorSector = None
        self._insert = True
        self._points: typing.List[core.Point2] = None
        self._current_point: core.Point2 = None
        self._debug_view: core.NodePath = None
        self._grid = grid.make_grid(
            self._camera_collection,
            'drawing_grid',
            2,
            100,
            core.Vec4(0.5, 0.55, 0.6, 0.85)
        )
        self._grid.hide()

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self._insert_point,
        )

        self._tickers.append(self._show_next_point)

    def start_drawing(self, sector: EditorSector, hit_point: core.Point3, insert: bool):
        self._sector = sector
        self._insert = insert

        position_2d = self._editor.snapper.snap_to_grid_2d(hit_point.xy)
        self._current_point = position_2d
        self._points = [self._current_point]

        grid.angle_grid(
            self._camera_collection,
            self._grid,
            self._editor.snapper.grid_size,
            self._sector.floor_slope_direction()
        )
        self._grid.set_pos(
            position_2d.x,
            position_2d.y,
            self._sector.floor_z_at_point(position_2d)
        )
        self._edit_mode_selector.push_mode(self)
        self._update_debug_view()

    def enter_mode(self, state: dict):
        super().enter_mode(state)
        self._grid.show()

        self.accept('backspace', self._remove_last_point)
        self.accept('space', self._insert_point)
        self.accept('enter', self._finish_shape)

    def exit_mode(self):
        self._grid.hide()
        self._clear_debug()
        return super().exit_mode()

    def _finish_shape(self):
        if len(self._points) < 1:
            return

        if self._insert:
            operations.sector_insert.SectorInsert(self._sector).insert(self._points)
        else:
            raise NotImplementedError()
        self._edit_mode_selector.pop_mode()
        self._editor.invalidate_view_clipping()

    def _remove_last_point(self):
        if len(self._points) > 0:
            self._points.pop()

    def _show_next_point(self):
        point = self._get_next_point()
        self._current_point = point
        self._update_debug_view()

    def _insert_point(self):
        point = self._get_next_point()
        if point is not None:
            if len(self._points) > 0 and (point - self._points[0]).length_squared() < 1:
                self._finish_shape()
            else:
                self._points.append(point)
                self._update_debug_view()

    def _get_next_point(self):
        source, target = self._extrude_mouse_to_scene_transform(True)
        if source is None or target is None:
            return None

        position = self._sector.floor_plane.intersect_line(
            source,
            target - source
        )
        if position is None:
            return None

        return self._editor.snapper.snap_to_grid_2d(position.xy)

    def _update_debug_view(self):
        self._clear_debug()

        segments = core.LineSegs()
        segments.set_thickness(4)

        points = self._points
        if self._current_point is not None:
            points = points + [self._current_point]

        if not points:
            return

        walls = zip(points, (points[1:] + points[:1]))

        for point_1, point_2 in walls:
            point_3d_1 = core.Point3(
                point_1.x,
                point_1.y,
                self._sector.floor_z_at_point(point_1)
            )
            segments.draw_to(point_3d_1)

            point_3d = core.Point3(
                point_1.x,
                point_1.y,
                self._sector.ceiling_z_at_point(point_1)
            )
            segments.draw_to(point_3d)

            point_3d = core.Point3(
                point_2.x,
                point_2.y,
                self._sector.ceiling_z_at_point(point_2)
            )
            segments.draw_to(point_3d)

            point_3d = core.Point3(
                point_2.x,
                point_2.y,
                self._sector.floor_z_at_point(point_2)
            )
            segments.draw_to(point_3d)

            segments.draw_to(point_3d_1)

        debug_view_node = segments.create('debug')

        self._debug_view = self._camera_collection.scene.attach_new_node(debug_view_node)
        self._debug_view.set_depth_write(False)
        self._debug_view.set_depth_test(False)
        self._debug_view.set_bin('fixed', constants.FRONT_MOST)

    def _clear_debug(self):
        if self._debug_view is not None:
            self._debug_view.remove_node()
            self._debug_view = None
