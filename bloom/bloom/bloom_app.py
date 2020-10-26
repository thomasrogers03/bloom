# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import math
import os.path
import sys
import typing
from glob import glob

from direct.showbase.ShowBase import ShowBase
from panda3d import bullet, core

from . import art, clicker, constants, edit_mode, editor, game_map
from .editor import map_editor
from .rff import RFF

logger = logging.getLogger(__name__)


class Bloom(ShowBase):
    _TICK_RATE = 1 / 120.0

    def __init__(self, path: str):
        ShowBase.__init__(self)
        self._path = path
        self._collision_world = bullet.BulletWorld()
        self.task_mgr.add(self._initialize, 'initialize')

    def _initialize(self, task):
        blood_path = 'J:/Games/DOSBox-0.73/Games/Blood/ouwblood'
        self._rff = RFF(f'{blood_path}/BLOOD.RFF')

        art_paths = glob(f'{blood_path}/*.[aA][rR][tT]')
        self._art_manager = art.ArtManager(self._rff, art_paths)
        self._tiles: typing.Dict[int, core.Texture] = {}

        if self._path is None or not os.path.exists(self._path):
            map_to_load = game_map.Map()
            map_to_load.new()
        else:
            with open(self._path, 'rb') as file:
                map_to_load = game_map.Map.load(file.read())

        self._scene: core.NodePath = self.render.attach_new_node('scene')
        self._scene.set_scale(1.0 / 100)
        self._collision_world.set_gravity(core.Vec3(0, 0, -9.81 / 100.0))

        self._sectors: core.NodePath = self._scene.attach_new_node('sectors')
        self._map_editor = map_editor.MapEditor(
            self.render,
            self._sectors,
            map_to_load,
            self._get_tile,
            self._collision_world
        )

        self._tickers = edit_mode.EditMode()
        self.task_mgr.add(self._tick, 'tick')

        self._builder_2d: core.NodePath = self._scene.attach_new_node('builder')
        position = core.Vec3(*map_to_load.start_position)
        self._builder_2d.set_pos(position.x, position.y, 0)
        self._builder_2d.set_scale(-1, 1, -1)

        self._builder: core.NodePath = self._builder_2d.attach_new_node('builder')
        self._builder.set_z(editor.to_height(position.z))
        self._builder.set_h(editor.to_degrees(map_to_load.start_theta))

        builder_camera: core.NodePath = self.loader.load_model('camera')
        builder_camera.reparent_to(self._builder)
        builder_camera.hide(constants.SCENE_3D)
        builder_camera.set_depth_write(False)
        builder_camera.set_depth_test(False)
        builder_camera.set_bin('fixed', 1000)
        builder_camera.set_scale(500)

        self._tickers.always_run(self._update_builder_sector)
        self._tickers.always_run(self._map_editor.hide_sectors)
        self._tickers.always_run(self._show_traceable_sectors)

        self.camera.reparent_to(self._builder)
        self.cam.node().set_camera_mask(constants.SCENE_3D)
        self.disable_mouse()

        self.camLens.set_fov(90)
        self.camLens.set_near_far(1, 1 << 17)

        self._lens_2d = core.OrthographicLens()
        film_size = self.camLens.get_film_size()
        self._lens_2d.set_film_size(film_size.x * 1280, film_size.y * 1280)
        self._lens_2d.set_near_far(16, 1_024_000)
        camera_2d_node = core.Camera('camera_2d')
        camera_2d_node.set_scene(self._scene)
        camera_2d_node.set_lens(self._lens_2d)
        camera_2d_node.set_camera_mask(constants.SCENE_2D)
        self._camera_2d: core.NodePath = self._builder_2d.attach_new_node(
            camera_2d_node)
        self._camera_2d.set_scale(32)
        self._camera_2d.set_hpr(180, -90, 0)
        self._camera_2d.set_z(512_000)

        window: core.GraphicsWindow = self.win
        self._display_region_2d: core.DisplayRegion = window.make_display_region(
            0, 1, 0, 1
        )
        self._display_region_2d.set_camera(self._camera_2d)
        self._display_region_2d.set_sort(1000)
        self._display_region_2d.set_active(False)
        self.accept('tab', self._toggle_2d_view)

        debug_node = bullet.BulletDebugNode('Debug')
        debug_node.show_wireframe(True)
        debug_node.show_constraints(True)
        debug_node.show_bounding_boxes(False)
        debug_node.show_normals(False)
        self._collision_debug: core.NodePath = self.render.attach_new_node(
            debug_node
        )
        self._collision_world.set_debug_node(debug_node)

        self._tickers.always_run(
            lambda: self._collision_world.do_physics(self._TICK_RATE)
        )
        self.accept('1', self._toggle_collision_debug)

        self._tickers['3d'].append(self._mouse_collision_tests)
        self._tickers.always_run(self._map_editor.tick)

        self.mouseWatcherNode.setModifierButtons(core.ModifierButtons())

        left_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.MouseButton.one()],
            on_click=self._select_object,
            on_click_move=self._pan_camera,
        )
        self._tickers['3d'].append(left_clicker.tick)

        left_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.MouseButton.one()],
            on_click=self._select_object,
            on_click_move=self._pan_camera_2d,
        )
        self._tickers['2d'].append(left_clicker.tick)

        left_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click_after_move=self._map_editor.end_move_selection,
            on_click_move=self._move_selected,
        )
        self._tickers['3d'].append(left_clicker.tick)

        left_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.KeyboardButton.shift(), core.MouseButton.one()],
            on_click_after_move=self._map_editor.end_move_selection,
            on_click_move=self._modified_move_selected,
        )
        self._tickers['3d'].append(left_clicker.tick)

        right_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.MouseButton.three()],
            on_click_move=self._rotate_camera,
        )
        self._tickers['3d'].append(right_clicker.tick)

        left_and_right_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click_move=self._strafe_camera,
        )
        self._tickers['3d'].append(left_and_right_clicker.tick)

        left_and_right_clicker = clicker.Clicker(
            self.mouseWatcherNode,
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click_move=self._strafe_camera_2d,
        )
        self._tickers['2d'].append(left_and_right_clicker.tick)

        self._tickers.set_mode('3d')

        self.accept('control-s', self._save_map)
        self.accept('control-p', lambda: self.screenshot('screenshot.png', defaultFilename=False))
        self.accept('space', lambda: self._map_editor.split_highlight(False))
        self.accept('shift-space', lambda: self._map_editor.split_highlight(True))

        return task.done

    def _save_map(self):
        position = self._builder.get_pos(self._scene)
        sectors, walls, sprites, builder_sector_index = self._map_editor.prepare_to_persist(position)
        map_to_save = game_map.Map()
        map_to_save.sectors[:] = sectors
        map_to_save.walls[:] = walls
        map_to_save.sprites[:] = sprites

        position_x = int(position.x)
        position_y = int(position.y)
        position_z = editor.to_build_height(position.z)
        theta = editor.to_build_angle(self._builder.get_h())
        result = map_to_save.save(
            position_x,
            position_y,
            position_z,
            theta,
            builder_sector_index
        )
        with open(self._path, 'w+b') as file:
            file.write(result)

        logger.info(f'Saved map to {self._path}')

    def _select_object(self):
        self._map_editor.perform_select()

    def _move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._do_move_selected(total_delta, delta, False)

    def _modified_move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._do_move_selected(total_delta, delta, True)

    def _do_move_selected(self, total_delta: core.Vec2, delta: core.Vec2, modified: bool):
        heading = self._builder.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))

        x_direction = sin_theta * delta.y + cos_theta * -delta.x
        y_direction = cos_theta * delta.y - sin_theta * -delta.x
        camera_delta = core.Vec2(x_direction, y_direction)

        x_direction = sin_theta * total_delta.y + cos_theta * -total_delta.x
        y_direction = cos_theta * total_delta.y - sin_theta * -total_delta.x
        total_camera_delta = core.Vec2(x_direction, y_direction)

        scale = 5120
        self._map_editor.move_selection(
            total_delta * scale, 
            delta * scale, 
            total_camera_delta * scale, 
            camera_delta * scale, modified
        )

    def _pan_camera_2d(self, total_delta: core.Vec2, delta: core.Vec2):
        x_direction = (delta.x * self._camera_2d.get_sx()) / 4
        y_direction = (delta.y * self._camera_2d.get_sx()) / 4

        self._builder_2d.set_x(self._builder_2d, x_direction * 5120)
        self._builder_2d.set_y(self._builder_2d, y_direction * 5120)

    def _pan_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        heading = self._builder.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = -sin_theta * delta.y + cos_theta * delta.x
        y_direction = cos_theta * delta.y + sin_theta * delta.x

        self._builder_2d.set_x(self._builder_2d, x_direction * 5120)
        self._builder_2d.set_y(self._builder_2d, y_direction * 5120)

    def _strafe_camera_2d(self, total_delta: core.Vec2, delta: core.Vec2):
        delta *= 100

        scale_grid = 1.0 / 8
        delta_y_scaled = delta.y / 2
        zoom_amount = int(delta_y_scaled / scale_grid) * scale_grid

        zoom_scale = math.pow(2, zoom_amount)
        current_zoom = self._camera_2d.get_sx()
        new_zoom = current_zoom * zoom_scale

        if new_zoom > 128:
            new_zoom = 128
        if new_zoom < 1:
            new_zoom = 1

        self._camera_2d.set_scale(new_zoom)
        self._builder_2d.set_x(self._builder_2d, delta.x * 512)

    def _strafe_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        delta *= 100

        heading = self._builder.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = cos_theta * delta.x
        y_direction = sin_theta * delta.x

        self._builder.set_z(self._builder.get_z() + delta.y * 512)

        self._builder_2d.set_x(self._builder_2d, x_direction * 512)
        self._builder_2d.set_y(self._builder_2d, y_direction * 512)

    def _rotate_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        hpr = self._builder.get_hpr()
        hpr = core.Vec3(hpr.x - delta.x * 90, hpr.y + delta.y * 90, 0)

        if hpr.y < -90:
            hpr.y = -90
        if hpr.y > 90:
            hpr.y = 90

        self._builder.set_hpr(hpr)

    def _is_editing_2d(self) -> bool:
        return self._tickers.current_mode == '2d'

    def _toggle_2d_view(self):
        if self._is_editing_2d():
            self._tickers.set_mode('3d')
            self._display_region_2d.set_active(False)
        else:
            self._tickers.set_mode('2d')
            self._display_region_2d.set_active(True)

    def _mouse_collision_tests(self):
        if self.mouseWatcherNode.has_mouse():
            if any(self.mouseWatcherNode.is_button_down(button) for button in clicker.Clicker.ALL_BUTTONS):
                return

            mouse = self.mouseWatcherNode.get_mouse()
            source = core.Point3()
            target = core.Point3()

            lens: core.Lens = self.camLens
            camera: core.NodePath = self.cam
            lens.extrude(mouse, source, target)

            source = self.render.get_relative_point(camera, source)
            target = self.render.get_relative_point(camera, target)

            source = core.TransformState.make_pos(source)
            target = core.TransformState.make_pos(target)

            self._map_editor.highlight_mouse_hit(source, target)

    def _toggle_collision_debug(self):
        if self._collision_debug.is_hidden():
            self._collision_debug.show()
        else:
            self._collision_debug.hide()

    def _update_builder_sector(self):
        self._map_editor.update_builder_sector(self._builder.get_pos(self._scene))

    def _show_traceable_sectors(self):
        self._map_editor.show_traceable_sectors(self._project_point)

    def _project_point(self, point: core.Vec2) -> core.Point3:
        camera_point = self.cam.get_relative_point(
            self._scene,
            core.Point3(point.x, point.y, self._builder.get_z())
        )
        projected_point = core.Point3()
        self.camLens.project(camera_point, projected_point)

        if projected_point.z > 1:
            projected_point.x = -projected_point.x

        return projected_point

    def _tick(self, task):
        self._tickers.tick()

        self.task_mgr.do_method_later(self._TICK_RATE, self._tick, 'tick')
        return task.done

    def _get_tile(self, picnum: int):
        if picnum not in self._tiles:
            image = self._art_manager.get_tile_image(picnum)
            buffer = image.tobytes()

            self._tiles[picnum] = core.Texture()
            self._tiles[picnum].setup_2d_texture(
                image.shape[1],
                image.shape[0],
                core.Texture.T_unsigned_byte,
                core.Texture.F_rgba8
            )
            self._tiles[picnum].set_ram_image(buffer)

        return self._tiles[picnum]
