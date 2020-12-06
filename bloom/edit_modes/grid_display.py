# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import cameras, constants, editor
from ..editor import grid_snapper, map_objects
from ..utils import shapes


class GridDisplay:
    _LARGE_GRID_SIZE = 1024

    def __init__(self, camera_collection: cameras.Cameras, map_scene: core.NodePath):
        self._camera_collection = camera_collection

        self._grid_parent: core.NodePath = map_scene.attach_new_node('grid_3d')
        self._grid_parent.set_transparency(True)

        self._small_grid = shapes.make_grid(
            self._camera_collection,
            'movement_grid',
            2,
            100,
            core.Vec4(0.5, 0.55, 0.8, 0.85)
        )
        self._small_grid.reparent_to(self._grid_parent)

        self._big_grid = shapes.make_grid(
            self._camera_collection,
            'big_movement_grid',
            4,
            100,
            core.Vec4(1, 0, 0, 0.95)
        )
        self._big_grid.reparent_to(self._grid_parent)
        self._big_grid.set_scale(self._LARGE_GRID_SIZE)

        self._vertical_grid = shapes.make_z_grid(
            self._camera_collection,
            'big_movement_grid',
            2,
            100,
            core.Vec4(0, 0, 1, 0.95)
        )
        self._vertical_grid.reparent_to(self._grid_parent)

        self._grid_parent.set_depth_offset(constants.DEPTH_OFFSET, 1)
        self._grid_parent.hide()

        self.set_color_scale = self._grid_parent.set_color_scale
        self.show = self._grid_parent.show
        self.hide = self._grid_parent.hide
        self.is_hidden = self._grid_parent.is_hidden

    @property
    def small_grid(self):
        return self._small_grid

    @property
    def big_grid(self):
        return self._big_grid

    @property
    def vertical_grid(self):
        return self._vertical_grid

    def update(
        self,
        snapper: grid_snapper.GridSnapper,
        position: core.Point3,
        sector: map_objects.EditorSector
    ):
        snapped_hit_2d = snapper.snap_to_grid_2d(position.xy)

        if sector is None:
            snapped_z = 0.0
            slope = core.Vec2(0, 0)
        else:
            snapped_z = sector.floor_z_at_point(snapped_hit_2d)
            slope = sector.floor_slope_direction()

        snapped_hit = core.Point3(
            snapped_hit_2d.x,
            snapped_hit_2d.y,
            snapped_z
        )

        shapes.align_grid_to_angle(
            self._camera_collection.scene,
            self._small_grid,
            snapper.grid_size,
            slope
        )
        shapes.align_grid_to_angle(
            self._camera_collection.scene,
            self._big_grid,
            self._LARGE_GRID_SIZE,
            slope
        )

        self._vertical_grid.set_scale(snapper.grid_size)

        self._small_grid.set_pos(snapped_hit)
        self._vertical_grid.set_pos(snapped_hit)

        big_snap_x = editor.snap_to_grid(snapped_hit.x, self._LARGE_GRID_SIZE)
        big_snap_y = editor.snap_to_grid(snapped_hit.y, self._LARGE_GRID_SIZE)
        self._big_grid.set_pos(big_snap_x, big_snap_y, snapped_hit.z)
