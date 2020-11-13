# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from .. import cameras, clicker_factory, constants, editor
from ..editor import grid_snapper, highlighter, map_objects
from ..editor.geometry import move
from ..utils import grid


class MovingClicker3D:
    _MOVE_SCALE = constants.TICK_SCALE
    _LARGE_GRID_SIZE = 1024

    def __init__(
        self,
        map_scene: core.NodePath,
        camera_collection: cameras.Cameras,
        transform_to_camera_delta: typing.Callable[[core.Vec2], core.Vec3],
        object_highlighter: highlighter.Highlighter,
        clickers: clicker_factory.ClickerFactory,
        snapper: grid_snapper.GridSnapper,
        all_sectors: map_objects.SectorCollection
    ):
        self._camera_collection = camera_collection
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

        self._grid_parent: core.NodePath = map_scene.attach_new_node('grid_3d')
        self._grid_parent.set_transparency(True)
        self._hide_grids()

        self._small_grid = grid.make_grid(
            self._camera_collection,
            'movement_grid',
            2,
            100,
            core.Vec4(0.5, 0.55, 0.8, 0.85)
        )
        self._small_grid.reparent_to(self._grid_parent)

        self._big_grid = grid.make_grid(
            self._camera_collection,
            'big_movement_grid',
            4,
            100,
            core.Vec4(1, 0, 0, 0.95)
        )
        self._big_grid.reparent_to(self._grid_parent)
        self._big_grid.set_scale(self._LARGE_GRID_SIZE)

        self._vertical_grid = grid.make_z_grid(
            camera_collection,
            'big_movement_grid',
            2,
            100,
            core.Vec4(0, 0, 1, 0.95)
        )
        self._vertical_grid.reparent_to(self._grid_parent)

        self._grid_parent.set_depth_offset(constants.DEPTH_OFFSET, 1)
        self._mover: move.Move = None

    def tick(self):
        self._move_clicker.tick()
        self._move_clicker_modified.tick()
        self._update_grids()

    def toggle_grid(self):
        if self._grid_parent.is_hidden():
            self._grid_parent.show()
        else:
            self._grid_parent.hide()

    def _end_move_selection(self):
        if self._mover is None:
            return

        self._mover.end_move()
        self._mover = None
        self._hide_grids()

    def _move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        if self._initialize_mover():
            total_camera_delta = self._transform_to_camera_delta(total_delta)
            self._mover.move(total_camera_delta * self._MOVE_SCALE)

    def _move_selected_modified(self, total_delta: core.Vec2, delta: core.Vec2):
        if self._initialize_mover():
            total_camera_delta = self._transform_to_camera_delta(total_delta)
            self._mover.move_modified(total_camera_delta * self._MOVE_SCALE)

    def _initialize_mover(self):
        if self._mover is None:
            selected = self._object_highlighter.select_append(no_append_if_not_selected=True)
            if len(selected) < 1:
                return False

            highlight = selected[-1]
            self._mover = move.Move(
                self._object_highlighter.selected,
                highlight,
                self._snapper,
                self._all_sectors
            )
            self._show_grids()
        return True

    def _update_grids(self):
        if len(self._object_highlighter.selected) > 0:
            highlight = self._object_highlighter.selected[-1]
        else:
            highlight = self._object_highlighter.highlighted

        if highlight is None:
            return

        snapped_hit_2d = self._snapper.snap_to_grid_2d(highlight.hit_position.xy)
        snapped_hit = core.Point3(
            snapped_hit_2d.x,
            snapped_hit_2d.y,
            highlight.map_object.get_sector().floor_z_at_point(snapped_hit_2d)
        )

        sector = highlight.map_object.get_sector()
        slope = sector.floor_slope_direction()
        grid.angle_grid(
            self._camera_collection,
            self._small_grid,
            self._snapper.grid_size,
            slope
        )
        grid.angle_grid(
            self._camera_collection,
            self._big_grid,
            self._LARGE_GRID_SIZE,
            slope
        )

        self._vertical_grid.set_scale(self._snapper.grid_size)

        self._small_grid.set_pos(snapped_hit)
        self._vertical_grid.set_pos(snapped_hit)

        big_snap_x = editor.snap_to_grid(snapped_hit.x, self._LARGE_GRID_SIZE)
        big_snap_y = editor.snap_to_grid(snapped_hit.y, self._LARGE_GRID_SIZE)
        self._big_grid.set_pos(big_snap_x, big_snap_y, snapped_hit.z)

    def _show_grids(self):
        self._grid_parent.set_color_scale(1, 1, 1, 1)

    def _hide_grids(self):
        self._grid_parent.set_color_scale(1, 1, 1, 0.35)
