# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from .. import cameras, constants
from ..editor import map_objects, operations
from . import base_edit_mode


class EditMode(base_edit_mode.EditMode):

    def __init__(self, *args, **kwargs):
        super().__init__(*args ,**kwargs)
        self._wall: map_objects.EditorWall = None
        self._display: core.NodePath = None

        self._tickers.append(self._update_curve_size)

        self._point_count = 3
        self._curve_size = 512
        self._split_points: typing.List[core.Point2] = []

    def set_wall(self, wall: map_objects.EditorWall):
        self._wall = wall

    def enter_mode(self, state: dict):
        super().enter_mode(state)

        self._menu.add_separator()
        self._menu.add_command(
            label="Decrease point count (-)",
            command=self._decrease_point_count
        )
        self._menu.add_command(
            label="Increase point count (=)",
            command=self._increase_point_count
        )
        self._menu.add_command(
            label="Commit bevel (space)",
            command=self._do_split
        )

        self.accept('-', self._decrease_point_count)
        self.accept('=', self._increase_point_count)
        self.accept('space', self._do_split)

        self._setup_curve()
        self._camera.display_region.set_active(True)

    def exit_mode(self):
        self._clear_curve()
        self._camera.display_region.set_active(False)
        return super().exit_mode()

    def _update_curve_size(self):
        source, _ = self._extrude_mouse_to_scene_transform(check_buttons=True)
        if source is None:
            return

        curve_size = self._wall.line_segment.get_point_distance(source.xy)
        if curve_size is None:
            return

        curve_size = self._editor.snapper.snap_to_grid(curve_size)
        if self._wall.side_of_line(source.xy) < 0:
            curve_size = -curve_size

        if curve_size != self._curve_size:
            self._curve_size = curve_size
            self._setup_curve()

    def _do_split(self):
        split = operations.wall_split.WallSplit(self._wall)
        for point in self._split_points:
            split.split(point)
        self._edit_mode_selector.pop_mode()

    def _decrease_point_count(self):
        self._point_count -= 1
        self._setup_curve()

    def _increase_point_count(self):
        self._point_count += 1
        self._setup_curve()

    def _clear_curve(self):
        if self._display is not None:
            self._display.remove_node()
            self._display = None

    def _setup_curve(self):
        self._clear_curve()
        points = self._get_curve_points()
        self._split_points = [point.xy for point in points[1:-1]]

        segments = core.LineSegs('curve')
        segments.set_color(1, 1, 0, 1)
        segments.set_thickness(2)
        for point in points:
            segments.draw_to(point.x, point.y, -constants.REALLY_BIG_NUMBER)
        self._display = self._camera_collection.scene.attach_new_node(segments.create())

    def _get_curve_points(self):
        direction = self._wall.get_direction()
        centre = self._wall.get_centre_2d()
        orthogonal = self._wall.get_normal() * self._curve_size

        result: typing.List[core.Point2] = [self._wall.point_2]
        for index in range(self._point_count):
            portion = (index + 1) / (self._point_count + 1)
            angle = portion * math.pi

            portion = math.cos(angle)
            offset = math.sin(angle)

            point = centre + direction * portion / 2 + orthogonal * offset
            result.append(point)

        result.append(self._wall.point_1)
        return result

    @property
    def _camera(self) -> cameras.Camera:
        return self._camera_collection['editor_2d']
