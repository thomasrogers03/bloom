# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math
import typing

from panda3d import core

from .. import clicker, constants, edit_mode, tile_dialog
from ..editor import map_editor
from . import base_edit_mode


class EditMode(base_edit_mode.EditMode):

    def __init__(
        self, 
        tile_selector: tile_dialog.TileDialog,
        camera: core.NodePath,
        lens: core.Lens,
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._tile_selector = tile_selector
        self._camera = camera
        self._lens = lens
        self._mouse_watcher = self._edit_mode_selector.mouse_watcher

        self._tickers.append(self._mouse_collision_tests)

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self.select_object,
            on_double_click=self._show_tile_selector,
            on_click_move=self._pan_camera,
        )

        self._make_clicker(
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click_after_move=lambda: self._editor.end_move_selection(),
            on_click_move=self._move_selected,
        )

        self._make_clicker(
            [core.KeyboardButton.shift(), core.MouseButton.one()],
            on_click_after_move=lambda: self._editor.end_move_selection(),
            on_click_move=self._modified_move_selected,
        )

        self._make_clicker(
            [core.MouseButton.three()],
            on_click_move=self._rotate_camera,
        )

        self._make_clicker(
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click_move=self._strafe_camera,
        )

    def select_object(self):
        self._editor.perform_select()

    def _show_tile_selector(self):
        self._tile_selector.show(self._editor.get_selected_picnum())

    def _mouse_collision_tests(self):
        if self._mouse_watcher.has_mouse():
            if any(self._mouse_watcher.is_button_down(button) for button in clicker.Clicker.ALL_BUTTONS):
                return

            mouse = self._mouse_watcher.get_mouse()
            source = core.Point3()
            target = core.Point3()

            self._lens.extrude(mouse, source, target)

            source = self._render.get_relative_point(self._camera, source)
            target = self._render.get_relative_point(self._camera, target)

            source = core.TransformState.make_pos(source)
            target = core.TransformState.make_pos(target)

            self._editor.highlight_mouse_hit(source, target)

    def _pan_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        heading = self._builder_camera.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = -sin_theta * delta.y + cos_theta * delta.x
        y_direction = cos_theta * delta.y + sin_theta * delta.x

        self._builder_camera_2d.set_x(self._builder_camera_2d, x_direction * constants.TICK_SCALE)
        self._builder_camera_2d.set_y(self._builder_camera_2d, y_direction * constants.TICK_SCALE)

    def _strafe_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        delta *= 100

        heading = self._builder_camera.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = cos_theta * delta.x
        y_direction = sin_theta * delta.x

        self._builder_camera.set_z(self._builder_camera.get_z() + delta.y * 512)

        self._builder_camera_2d.set_x(self._builder_camera_2d, x_direction * 512)
        self._builder_camera_2d.set_y(self._builder_camera_2d, y_direction * 512)

    def _rotate_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        hpr = self._builder_camera.get_hpr()
        hpr = core.Vec3(hpr.x - delta.x * 90, hpr.y + delta.y * 90, 0)

        if hpr.y < -90:
            hpr.y = -90
        if hpr.y > 90:
            hpr.y = 90

        self._builder_camera.set_hpr(hpr)

    def _move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._do_move_selected(total_delta, delta, False)

    def _modified_move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._do_move_selected(total_delta, delta, True)

    def _do_move_selected(self, total_delta: core.Vec2, delta: core.Vec2, modified: bool):
        heading = self._builder_camera.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))

        x_direction = sin_theta * delta.y + cos_theta * -delta.x
        y_direction = cos_theta * delta.y - sin_theta * -delta.x
        camera_delta = core.Vec2(x_direction, y_direction)

        x_direction = sin_theta * total_delta.y + cos_theta * -total_delta.x
        y_direction = cos_theta * total_delta.y - sin_theta * -total_delta.x
        total_camera_delta = core.Vec2(x_direction, y_direction)

        self._editor.move_selection(
            total_delta * constants.TICK_SCALE,
            delta * constants.TICK_SCALE,
            total_camera_delta * constants.TICK_SCALE,
            camera_delta * constants.TICK_SCALE, modified
        )

