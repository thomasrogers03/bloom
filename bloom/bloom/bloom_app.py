# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import importlib
import logging
import math
import os.path
import queue
import sys
import time
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import typing
from glob import glob

import yaml
from direct.showbase.ShowBase import ShowBase
from panda3d import bullet, core
from panda3d.direct import init_app_for_gui

from . import (art, clicker, constants, edit_mode, editor, game_map,
               tile_dialog, utils)
from .edit_modes import edit_mode_2d, edit_mode_3d
from .editor import map_editor
from .rff import RFF

logger = logging.getLogger(__name__)


class Bloom(ShowBase):
    _CONFIG_PATH = 'config.yaml'

    def __init__(self, path: str):
        self._setup_window()
        self._setup_menu()
        self._path = path
        self._collision_world = bullet.BulletWorld()

        if not os.path.isdir(constants.CACHE_PATH):
            os.mkdir(constants.CACHE_PATH)

        if os.path.exists(self._CONFIG_PATH):
            with open(self._CONFIG_PATH, 'r') as file:
                self._config = yaml.load(file.read())
        else:
            self._config = {}
            blood_path = tkinter.filedialog.askdirectory(
                initialdir=os.getcwd(),
                title='Specify Blood Game Path',
            )
            if not (blood_path and os.path.exists(os.path.join(blood_path, 'BLOOD.RFF'))):
                message = 'Unable to proceed without a valid blood path'
                tkinter.messagebox.showerror(title='Cannot load', message=message)
                raise ValueError(message)

            self._config['blood_path'] = blood_path

            with open(self._CONFIG_PATH, 'w+') as file:
                file.write(yaml.dump(self._config))

        self.task_mgr.do_method_later(0.1, self._initialize, 'initialize')

    def _setup_window(self):
        ShowBase.__init__(self, windowType='none')

        frame = tkinter.Tk()

        frame.state("zoomed")
        frame.title("Bloom")
        frame.bind("<Configure>", self._handle_resize)

        self.wantTk = True
        self.tkRoot = frame
        init_app_for_gui()

        tk_frame_rate = core.ConfigVariableDouble('tk-frame-rate', 60.0)
        self._tk_delay = int(1000.0 / tk_frame_rate.get_value())
        self.tkRoot.after(self._tk_delay, self._tk_timer_callback)

        self.run = self.tkRun
        self.taskMgr.run = self.tkRun
        if self.appRunner:
            self.appRunner.run = self.tkRun

        props = self._window_props()

        self.make_default_pipe()
        self.open_default_window(props=props)

    def _setup_menu(self):
        menu_bar = tkinter.Menu(self.tkRoot)

        file_menu = tkinter.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open (ctrl+o)", command=self._open_map)
        file_menu.add_command(label="Save (ctrl+s)", command=self._save_map)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.tkRoot.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tkinter.Menu(menu_bar, tearoff=0)
        # edit_menu.add_command(label="Split (space)", command=self._split_selection)
        # edit_menu.add_command(label="Extrude (shift+space)",
        #                       command=self._extrude_selection)
        edit_menu.add_separator()
        # edit_menu.add_command(label="Change tile (v)", command=self._change_tile)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tkinter.Menu(menu_bar, tearoff=0)
        view_menu.add_command(
            label="Debug (1)", command=self._toggle_collision_debug)
        view_menu.add_command(label="Screenshot (ctrl+p)",
                              command=self._save_screenshot)
        menu_bar.add_cascade(label="View", menu=view_menu)

        self.tkRoot.config(menu=menu_bar)

    def _tk_timer_callback(self):
        if not core.Thread.get_current_thread().get_current_task():
            self.task_mgr.step()

        self.tkRoot.after(self._tk_delay, self._tk_timer_callback)

    def _window_props(self):
        self.tkRoot.update()
        window_id = self.tkRoot.winfo_id()
        width = self.tkRoot.winfo_width()
        height = self.tkRoot.winfo_height()

        props = core.WindowProperties()
        props.set_parent_window(window_id)
        props.set_origin(0, 50)
        props.set_size(width, height - 80)

        return props

    def _handle_resize(self, event):
        if self.win is not None:
            props = self._window_props()
            self.win.request_properties(props)

    def _initialize(self, task):
        blood_path = self._config['blood_path']
        self._rff = RFF(f'{blood_path}/BLOOD.RFF')

        art_paths = glob(f'{blood_path}/*.[aA][rR][tT]')
        self._art_manager = art.ArtManager(self._rff, art_paths)
        self._tiles: typing.Dict[int, core.Texture] = {}

        if self._path is None or not os.path.exists(self._path):
            map_to_load = game_map.Map()
            map_to_load.new()
        else:
            with open(self._path, 'rb') as file:
                map_to_load = game_map.Map.load(self._path, file.read())

        self._scene: core.NodePath = self.render.attach_new_node('scene')
        self._scene.set_scale(1.0 / 100)
        self._collision_world.set_gravity(core.Vec3(0, 0, -9.81 / 100.0))

        self._edit_mode_selector = edit_mode.EditMode(
            self.mouseWatcherNode,
            self.task_mgr
        )

        self._sectors: core.NodePath = self._scene.attach_new_node('sectors')
        self._map_editor = map_editor.MapEditor(
            self.render,
            self._sectors,
            map_to_load,
            self._get_tile,
            self._collision_world
        )

        self._tile_loads = queue.Queue()
        self._tile_dialog = tile_dialog.TileDialog(
            self.aspect2d,
            self._get_tile_async,
            self._art_manager.tile_count,
            self._edit_mode_selector,
            self.task_mgr,
            self._update_selected_tile
        )

        self._builder_2d: core.NodePath = self._scene.attach_new_node('builder')
        position = core.Vec3(*map_to_load.start_position)
        self._builder_2d.set_pos(position.x, position.y, 0)
        self._builder_2d.set_scale(-1, 1, -1)

        self._builder: core.NodePath = self._builder_2d.attach_new_node('builder')
        self._builder.set_z(editor.to_height(position.z))
        self._builder.set_h(editor.to_degrees(map_to_load.start_theta))

        builder_camera: core.NodePath = self._builder.attach_new_node(
            'builder_camera'
        )
        builder_camera.hide(constants.SCENE_3D)
        builder_camera.set_depth_write(False)
        builder_camera.set_depth_test(False)
        builder_camera.set_bin('fixed', 1000)
        builder_camera.set_scale(500)

        self._edit_mode_selector.always_run(self._update_builder_sector)
        self._edit_mode_selector.always_run(lambda: self._map_editor.hide_sectors())
        self._edit_mode_selector.always_run(self._show_traceable_sectors)
        self._edit_mode_selector.always_run(self._process_loading_tiles)

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
            camera_2d_node
        )
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

        debug_node = bullet.BulletDebugNode('Debug')
        debug_node.show_wireframe(True)
        debug_node.show_constraints(True)
        debug_node.show_bounding_boxes(False)
        debug_node.show_normals(False)
        self._collision_debug: core.NodePath = self.render.attach_new_node(
            debug_node
        )
        self._collision_world.set_debug_node(debug_node)

        self._edit_mode_selector.always_run(
            lambda: self._collision_world.do_physics(constants.TICK_RATE)
        )
        self.accept('1', self._toggle_collision_debug)

        self._edit_mode_selector.always_run(lambda: self._map_editor.tick())

        self.mouseWatcherNode.setModifierButtons(core.ModifierButtons())

        self._mode_2d = edit_mode_2d.EditMode(
            self._camera_2d,
            self._display_region_2d,
            render=self.render, 
            scene=self._scene,
            builder_camera_2d=self._builder_2d,
            builder_camera=self._builder,
            edit_mode_selector=self._edit_mode_selector
        )
        self._mode_2d.set_editor(self._map_editor)

        self._mode_3d = edit_mode_3d.EditMode(
            self._tile_dialog,
            self.cam,
            self.camLens,
            self._mode_2d,
            render=self.render, 
            scene=self._scene,
            builder_camera_2d=self._builder_2d,
            builder_camera=self._builder,
            edit_mode_selector=self._edit_mode_selector
        )
        self._mode_3d.set_editor(self._map_editor)

        self._edit_mode_selector.push_mode(self._mode_3d)

        self.accept('control-s', self._save_map)
        self.accept('control-o', self._open_map)
        self.accept('control-p', self._save_screenshot)

        return task.done

    def _update_selected_tile(self, picnum: int):
        self._map_editor.set_selected_picnum(picnum)

    def _save_screenshot(self):
        self.screenshot('screenshot.png', defaultFilename=False)

    def _open_map(self):
        path = tkinter.filedialog.askopenfilename(
            initialdir=self._config['blood_path'],
            title='Open map',
            filetypes=(('Map files', '*.MAP'),)
        )
        if path:
            self._path = path
            self._sectors.remove_node()
            self._map_editor = None
            for body in self._collision_world.get_rigid_bodies():
                self._collision_world.remove(body)
            self._sectors: core.NodePath = self._scene.attach_new_node('sectors')
            with open(self._path, 'rb') as file:
                map_to_load = game_map.Map.load(self._path, file.read())
            self._map_editor = map_editor.MapEditor(
                self.render,
                self._sectors,
                map_to_load,
                self._get_tile,
                self._collision_world
            )
            self._mode_3d.set_editor(self._map_editor)
            self._mode_2d.set_editor(self._map_editor)

    def _save_map(self):
        if not self._path:
            self._path = tkinter.filedialog.asksaveasfilename(
                initialdir=self._config['blood_path'],
                title='Save map to...',
                filetypes=(('Map files', '*.MAP'),)
            )
            if not self._path:
                return

        position = self._builder.get_pos(self._scene)
        sectors, walls, sprites, builder_sector_index = self._map_editor.prepare_to_persist(
            position
        )
        map_to_save = game_map.Map()
        map_to_save.sectors[:] = sectors
        map_to_save.walls[:] = walls
        map_to_save.sprites[:] = sprites

        position_x = int(position.x)
        position_y = int(position.y)
        position_z = editor.to_build_height(position.z)
        theta = editor.to_build_angle(self._builder.get_h())
        result = map_to_save.save(
            self._path,
            position_x,
            position_y,
            position_z,
            theta,
            builder_sector_index
        )
        with open(self._path, 'w+b') as file:
            file.write(result)

        logger.info(f'Saved map to {self._path}')

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

    def _get_tile(self, picnum: int):
        if picnum not in self._tiles:
            image = self._art_manager.get_tile_image(picnum)
            buffer = image.tobytes()

            tile = core.Texture()
            tile.setup_2d_texture(
                image.shape[1],
                image.shape[0],
                core.Texture.T_unsigned_byte,
                core.Texture.F_rgba8
            )
            tile.set_ram_image(buffer)
            self._tiles[picnum] = tile

        return self._tiles[picnum]

    def _get_tile_async(self, picnum: int, callback: typing.Callable[[core.Texture], None]):
        self._tile_loads.put((picnum, callback))

    def _process_loading_tiles(self):
        now = time.time()
        while (time.time() - now) < constants.TICK_RATE / 4:
            if self._tile_loads.empty():
                break

            tile_to_load, callback = self._tile_loads.get_nowait()
            callback(self._get_tile(tile_to_load))
