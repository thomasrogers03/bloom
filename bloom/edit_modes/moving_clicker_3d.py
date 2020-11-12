# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from .. import cameras, clicker_factory, constants
from ..editor import grid_snapper, highlighter, map_objects
from ..editor.geometry import move
from ..utils import grid


class MovingClicker3D:
    _MOVE_SCALE = constants.TICK_SCALE

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        transform_to_camera_delta: typing.Callable[[core.Vec2], core.Vec3],
        object_highlighter: highlighter.Highlighter,
        clickers: clicker_factory.ClickerFactory,
        snapper: grid_snapper.GridSnapper,
        all_sectors: map_objects.SectorCollection
    ):
        self._transform_to_camera_delta = transform_to_camera_delta
        self._object_highlighter = object_highlighter
        self._snapper = snapper
        self._all_sectors = all_sectors

        self._move_clicker = clickers.make_clicker(
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click_after_move=self._end_move_selection,
            on_click_move=self._move_selected,
        )
        self._move_clicker_modified = clickers.make_clicker(
            [core.KeyboardButton.shift(), core.MouseButton.one()],
            on_click_after_move=self._end_move_selection,
            on_click_move=self._move_selected_modified,
        )

        self._grid_parent: core.NodePath = camera_collection.scene.attach_new_node('grid_3d')
        self._grid_parent.set_transparency(True)
        self._grid_parent.set_depth_offset(constants.HIGHLIGHT_DEPTH_OFFSET, 1)
        self._hide_grids()

        self._small_grid = grid.make_grid(
            camera_collection,
            'movement_grid',
            2,
            100,
            core.Vec4(0.5, 0.55, 0.8, 0.85)
        )
        self._small_grid.reparent_to(self._grid_parent)

        self._big_grid = grid.make_grid(
            camera_collection,
            'big_movement_grid',
            4,
            100,
            core.Vec4(1, 0, 0, 0.95)
        )
        self._big_grid.reparent_to(self._grid_parent)
        self._big_grid.set_scale(1024)

        self._vertical_grid = grid.make_z_grid(
            camera_collection,
            'big_movement_grid',
            2,
            100,
            core.Vec4(0, 0, 1, 0.95)
        )
        self._vertical_grid.reparent_to(self._grid_parent)

        self._mover: move.Move = None

    def tick(self):
        self._move_clicker.tick()
        self._move_clicker_modified.tick()
        self._update_grids()

    def _end_move_selection(self):
        if self._mover is None:
            return

        self._mover.end_move()
        self._mover = None
        self._hide_grids()

    def _move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._initialize_mover()

        total_camera_delta = self._transform_to_camera_delta(total_delta)
        self._mover.move(total_camera_delta * self._MOVE_SCALE)

    def _move_selected_modified(self, total_delta: core.Vec2, delta: core.Vec2):
        self._initialize_mover()

        total_camera_delta = self._transform_to_camera_delta(total_delta)
        self._mover.move_modified(total_camera_delta * self._MOVE_SCALE)

    def _initialize_mover(self):
        if self._mover is None:
            self._object_highlighter.select_append(no_append_if_not_selected=True)
            highlight = self._object_highlighter.selected[-1]
            self._mover = move.Move(
                self._object_highlighter.selected,
                highlight,
                self._snapper,
                self._all_sectors
            )
            self._show_grids()

    def _update_grids(self):
        if len(self._object_highlighter.selected) > 0:
            highlight = self._object_highlighter.selected[-1]
        else:
            highlight = self._object_highlighter.highlighted

        if highlight is None:
            return

        hit_2d = core.Point2(
            highlight.hit_position.x,
            highlight.hit_position.y
        )
        snapped_hit_2d = self._snapper.snap_to_grid_2d(hit_2d)
        snapped_hit = core.Point3(
            snapped_hit_2d.x,
            snapped_hit_2d.y,
            highlight.map_object.get_sector().floor_z_at_point(snapped_hit_2d)
        )

        self._small_grid.set_scale(self._snapper.grid_size)
        self._vertical_grid.set_scale(self._snapper.grid_size)

        self._grid_parent.set_pos(snapped_hit)

    def _show_grids(self):
        self._grid_parent.set_color_scale(1, 1, 1, 1)

    def _hide_grids(self):
        self._grid_parent.set_color_scale(1, 1, 1, 0.35)
