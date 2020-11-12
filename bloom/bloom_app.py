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

from . import (cameras, clicker, constants, dialogs, edit_menu, edit_mode,
               editor, game_map, tile_dialog, utils)
from .edit_modes import edit_mode_2d, edit_mode_3d
from .editor import map_editor
from .rff import RFF
from .tiles import manager

logger = logging.getLogger(__name__)


class Bloom(ShowBase):
    _CONFIG_PATH = 'config.yaml'

    def __init__(self, path: str):
        self._setup_window()
        self._setup_menu()
        self._path = path

        if not os.path.isdir(constants.CACHE_PATH):
            os.mkdir(constants.CACHE_PATH)

        if os.path.exists(self._CONFIG_PATH):
            with open(self._CONFIG_PATH, 'r') as file:
                self._config = yaml.load(file.read(), Loader=yaml.SafeLoader)
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

            self._blood_path = blood_path

            with open(self._CONFIG_PATH, 'w+') as file:
                file.write(yaml.dump(self._config))

        self.task_mgr.do_method_later(0.1, self._initialize, 'initialize')

    def _setup_window(self):
        ShowBase.__init__(self, windowType='none')

        frame = tkinter.Tk()

        try:
            frame.state("zoomed")
        except:
            frame.attributes('-zoomed', True)
        frame.title("Bloom")
        frame.bind("<Configure>", self._handle_resize)
        frame.protocol("WM_DELETE_WINDOW", self._handle_exit)

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
        file_menu.add_command(label="New (ctrl+n)", command=self._new_map)
        file_menu.add_command(label="Open (ctrl+o)", command=self._open_map)
        file_menu.add_command(label="Save (ctrl+s)", command=self._save_map)
        file_menu.add_command(label="Save As", command=self._save_map_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.tkRoot.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        self._edit_menu = edit_menu.EditMenu(menu_bar)

        view_menu = tkinter.Menu(menu_bar, tearoff=0)
        view_menu.add_command(
            label="Screenshot (ctrl+p)",
            command=self._save_screenshot
        )
        menu_bar.add_cascade(label="View", menu=view_menu)

        self.tkRoot.config(menu=menu_bar)

    def _tk_timer_callback(self):
        if not core.Thread.get_current_thread().get_current_task():
            try:
                self.task_mgr.step()
            except Exception as error:
                message = f'Error running application: {error}'
                logger.error(message, exc_info=error)
                tkinter.messagebox.showerror("Error running Bloom", message)
                self.tkRoot.quit()

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
        blood_path = self._blood_path
        self._rff = RFF(f'{blood_path}/BLOOD.RFF')

        self._scene: core.NodePath = self.render.attach_new_node('scene')
        self._scene.set_scale(1.0 / 100)
        
        self._camera_collection = cameras.Cameras(
            self.loader,
            self.win,
            self.render,
            self.render2d,
            self._scene,
            cameras.Camera(
                self.cam,
                self.cam.node(),
                self.camLens,
                self.win.get_display_region(0)
            )
        )

        if self._path is None:
            self._path = self._config.get('last_map', None)

        if self._path is None:
            self._make_new_board()
            
        if not os.path.exists(self._path):
            map_to_load = game_map.Map()
            map_to_load.new()
        else:
            with open(self._path, 'rb') as file:
                map_to_load = game_map.Map.load(self._path, file.read())

        self._edit_mode_selector = edit_mode.EditMode(
            self.mouseWatcherNode,
            self.task_mgr
        )

        self._tile_manager = manager.Manager(blood_path, self._rff, self._edit_mode_selector)
        self._dialogs = dialogs.Dialogs(
            self.aspect2d,
            self._tile_manager,
            self._edit_mode_selector,
            self.task_mgr
        )

        self._mode_2d = edit_mode_2d.EditMode(
            camera_collection=self._camera_collection,
            edit_mode_selector=self._edit_mode_selector,
            menu=self._edit_menu
        )

        self._mode_3d = edit_mode_3d.EditMode(
            self._dialogs,
            self._mode_2d,
            camera_collection=self._camera_collection,
            edit_mode_selector=self._edit_mode_selector,
            menu=self._edit_menu
        )

        self._map_editor: map_editor.MapEditor = None
        self._load_map_into_editor(map_to_load)

        self.disable_mouse()

        camera = self._camera_collection.make_2d_camera('editor_2d')
        camera.camera.reparent_to(self._camera_collection.builder_2d)

        self._edit_mode_selector.always_run(self._tick_map_editor)

        self.mouseWatcherNode.setModifierButtons(core.ModifierButtons())

        self._edit_mode_selector.push_mode(self._mode_3d)

        self.accept('control-n', self._new_map)
        self.accept('control-o', self._open_map)
        self.accept('control-s', self._save_map)
        self.accept('control-p', self._save_screenshot)

        self.task_mgr.add(self._update_for_frame, 'frame_update')

        return task.done

    def _make_new_board(self):
        self._path = os.path.join(self._blood_path, 'NEWBOARD.MAP')
        self._config['last_map'] = self._path

    def _update_for_frame(self, task):
        with self._edit_mode_selector.track_performance_stats('frame_update'):
            self._map_editor.update_for_frame()

        return task.cont

    def _tick_map_editor(self):
        with self._edit_mode_selector.track_performance_stats('map_editor_tick'):
            self._map_editor.tick()

    def _save_screenshot(self):
        self.screenshot('screenshot.png', defaultFilename=False)

    def _load_map_into_editor(self, map_to_load: game_map.Map):
        if self._map_editor is not None:
            self._map_editor.unload()
            self._map_editor = None

        self._map_editor = map_editor.MapEditor(
            self._camera_collection,
            map_to_load,
            self._tile_manager,
        )
        self._mode_3d.set_editor(self._map_editor)
        self._mode_2d.set_editor(self._map_editor)

        position = core.Vec3(*map_to_load.start_position)
        self._camera_collection.builder_2d.set_pos(position.x, position.y, 0)
        self._camera_collection.builder_2d.set_scale(-1, 1, -1)

        self._camera_collection.builder.set_z(editor.to_height(position.z))
        self._camera_collection.builder.set_h(
            editor.to_degrees(map_to_load.start_theta)
        )

        self._map_editor.update_builder_sector(
            self._camera_collection.get_builder_position()
        )

    @property
    def _blood_path(self):
        return self._config['blood_path']

    def _new_map(self):
        self._make_new_board()
        
        map_to_load = game_map.Map()
        map_to_load.new()
        self._load_map_into_editor(map_to_load)

    def _open_map(self):
        path = tkinter.filedialog.askopenfilename(
            initialdir=self._blood_path,
            title='Open map',
            filetypes=(('Map files', '*.MAP'),)
        )
        if path:
            self._path = path
            self._config['last_map'] = self._path
            with open(self._path, 'rb') as file:
                map_to_load = game_map.Map.load(self._path, file.read())

            self._load_map_into_editor(map_to_load)

    def _save_map_as(self):
        path = tkinter.filedialog.asksaveasfilename(
            initialdir=self._blood_path,
            title='Save map to...',
            filetypes=(('Map files', '*.MAP'),)
        )
        self._config['last_map'] = path
        if not path:
            return

        self._path = path
        self._save_map()

    def _save_map(self):
        position = self._camera_collection.get_builder_position()
        sky_offsets, sectors, walls, sprites, builder_sector_index = self._map_editor.prepare_to_persist(
            position
        )
        map_to_save = game_map.Map()
        map_to_save.sectors[:] = sectors
        map_to_save.walls[:] = walls
        map_to_save.sprites[:] = sprites

        position_x = round(position.x)
        position_y = round(position.y)
        position_z = editor.to_build_height(position.z)
        theta = editor.to_build_angle(self._camera_collection.builder.get_h())
        result = map_to_save.save(
            self._path,
            sky_offsets,
            position_x,
            position_y,
            position_z,
            theta,
            builder_sector_index
        )
        with open(self._path, 'w+b') as file:
            file.write(result)

        logger.info(f'Saved map to {self._path}')

    def _handle_exit(self):
        logger.info('Shutting down...')
        with open(self._CONFIG_PATH, 'w+') as file:
            file.write(yaml.dump(self._config))
        self.tkRoot.destroy()
