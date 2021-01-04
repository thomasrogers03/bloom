# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.showbase import DirectObject
from panda3d import core

from .. import cameras
from ..editor import map_editor, map_objects, operations
from . import drawing_display


class SectorDrawer:

    def __init__(
        self,
        camera_collection: cameras.Camera,
        tickers: typing.List[typing.Callable[[], None]],
        make_clicker,
        extrude_mouse_to_scene_transform: typing.Callable[[bool], core.Point3]
    ): 
        self._camera_collection = camera_collection
        self._extrude_mouse_to_scene_transform = extrude_mouse_to_scene_transform

        self._editor: map_editor.MapEditor = None
        self._done_callback: typing.Callable[[], None] = None
        self._sector: map_objects.EditorSector = None
        self._insert = True
        self._points: typing.List[core.Point2] = []
        self._display = drawing_display.DrawingDisplay(
            self._camera_collection
        )
        self._current_point: core.Point2 = None

        make_clicker(
            [core.MouseButton.one()],
            on_click=self._insert_point,
        )

        tickers.append(self._show_next_point)

    def start_drawing(
        self, 
        editor: map_editor.MapEditor, 
        sector: map_objects.EditorSector, 
        hit_point: core.Point3, 
        insert: bool
    ):
        self._editor = editor
        self._sector = sector

        if insert and self._sector is not None:
            for editor_wall in self._sector.walls:
                distance_to_wall = editor_wall.line_segment.get_point_distance(
                    hit_point.xy
                )
                if distance_to_wall is not None and \
                        distance_to_wall < self._editor.snapper.grid_size:
                    insert = False
                    projected_point = editor_wall.line_segment.project_point(
                        hit_point.xy
                    )
                    hit_point.x = projected_point.x
                    hit_point.y = projected_point.y
                    break

        self._insert = insert

        position_2d = self._editor.snapper.snap_to_grid_2d(hit_point.xy)
        if not self._insert:
            point_neat_wall = self._point_near_wall(hit_point.xy)
            if point_neat_wall is not None:
                position_2d = point_neat_wall
        
        self._current_point = position_2d
        self._points[:] = [self._current_point]

        grid_position = core.Point3(
            position_2d.x,
            position_2d.y,
            self._floor_z_at_point(position_2d)
        )
        self._display.start_drawing(
            self._sector,
            grid_position,
            self._editor.snapper
        )
        self._update_debug_display()

    def _floor_z_at_point(self, point: core.Point2):
        if self._sector is None:
            return 0
        return self._sector.floor_z_at_point(point)

    def show(self, acceptor: DirectObject.DirectObject, done_callback: typing.Callable[[], None]):
        self._display.show_grid()
        self._done_callback = done_callback

        acceptor.accept('backspace', self._remove_last_point)
        acceptor.accept('space', self._insert_point)
        acceptor.accept('enter', self._finish_shape)

    def hide(self):
        self._display.hide_grid()
        self._display.clear_debug()

    def _finish_shape(self):
        self._done_callback()

        if len(self._points) < 1:
            return

        if self._insert:
            operations.sector_insert.SectorInsert(
                self._sector,
                self._editor.sectors
            ).insert(self._points)
        else:
            operations.sector_split.SectorSplit(
                self._sector,
                self._editor.sectors
            ).split(self._points)

        self._editor.invalidate_view_clipping()

    def _remove_last_point(self):
        if len(self._points) > 0:
            self._points.pop()

    def _show_next_point(self):
        point = self._get_next_point()
        self._current_point = point
        self._update_debug_display()

    def _insert_point(self):
        point = self._get_next_point()
        if point is not None:
            if len(self._points) > 0 and (point - self._points[0]).length_squared() < 1:
                self._finish_shape()
            else:
                self._points.append(point)
                self._update_debug_display()

    def _get_next_point(self):
        source, target = self._extrude_mouse_to_scene_transform(True)
        if source is None or target is None:
            return None

        if self._sector is None:
            position = target
        else:
            position = self._sector.floor_plane.intersect_line(
                source,
                target - source
            )
            if position is None:
                return None

        if not self._insert:
            point_neat_wall = self._point_near_wall(position.xy)
            if point_neat_wall is not None:
                return point_neat_wall

        return self._editor.snapper.snap_to_grid_2d(position.xy)

    def _point_near_wall(self, point: core.Point2) -> core.Point2:
        vertex_near_point = self._vertex_near_point(point)
        if vertex_near_point is not None:
            return vertex_near_point.point_1

        wall_near_point = self._wall_near_point(point)
        if wall_near_point is not None:
            point = wall_near_point.line_segment.project_point(point)
            snapped_point = self._editor.snapper.snap_to_grid_2d(point)
            if wall_near_point.line_segment.point_on_line(snapped_point, tolerance=0):
                return snapped_point
            return point

        return None

    def _vertex_near_point(self, point: core.Point2) -> map_objects.EditorWall:
        result: map_objects.EditorWall = None
        closest_distance_squared = self._editor.snapper.grid_size * self._editor.snapper.grid_size
        for wall in self._sector.walls:
            distance_squared = (point - wall.point_1).length_squared()
            if distance_squared < closest_distance_squared:
                result = wall
                closest_distance_squared = distance_squared

        return result

    def _wall_near_point(self, point: core.Point2) -> map_objects.EditorWall:
        result: map_objects.EditorWall = None
        closest_distance = self._editor.snapper.grid_size
        for wall in self._sector.walls:
            distance = wall.line_segment.get_point_distance(point)
            if distance is not None and distance < closest_distance:
                result = wall
                closest_distance = distance

        return result

    def _update_debug_display(self):
        self._display.update(
            self._current_point,
            self._points,
            self._insert
        )
