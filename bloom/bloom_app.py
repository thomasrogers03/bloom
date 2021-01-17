# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import distutils.spawn
import logging
import os.path
import tkinter
import tkinter.filedialog
import tkinter.messagebox

import yaml
from direct.showbase.ShowBase import ShowBase
from panda3d import bullet, core
from panda3d.direct import init_app_for_gui

from . import (addon, audio, auto_save, cameras, clicker, constants, dialogs,
               edit_menu, edit_mode, editor, game_map, tile_dialog, utils)
from .audio import midi_to_wav
from .edit_modes import edit_mode_2d, edit_mode_3d
from .editor import map_editor
from .rff import RFF
from .tiles import manager

logger = logging.getLogger(__name__)


class Bloom(ShowBase):
    _CONFIG_PATH = 'config.yaml'
    _META_PATH = 'meta.yaml'
    _AUTO_SAVE_TIMEOUT = 1 * 60

    def __init__(self, path: str):
        self._setup_window()
        self._setup_menu()
        self._path = path
        self._auto_save: auto_save.AutoSave = None

        if not os.path.isdir(constants.CACHE_PATH):
            os.mkdir(constants.CACHE_PATH)

        if os.path.exists(self._CONFIG_PATH):
            with open(self._CONFIG_PATH, 'r') as file:
                self._config = yaml.safe_load(file.read())
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

        if os.path.exists(self._META_PATH):
            with open(self._META_PATH, 'r') as file:
                self._bloom_meta = yaml.safe_load(file.read())
        else:
            self._bloom_meta = {}

        if 'fluid_synth_path' not in self._config:
            fluid_synth_path = distutils.spawn.find_executable("fluidsynth.exe")
            if not fluid_synth_path:
                fluid_synth_path = distutils.spawn.find_executable("fluidsynth")

            if not fluid_synth_path:
                fluid_synth_path = tkinter.filedialog.askopenfilename(
                    initialdir=self._blood_path,
                    title='Path to fluidsynth executable',
                    filetypes=(('Executable Files', '*.EXE'),)
                )

            if not fluid_synth_path:
                message = 'Unable to play music without fluid synth, it will be disabled'
                tkinter.messagebox.showwarning(
                    title='Cannot play music',
                    message=message
                )
                fluid_synth_path = None

            self._config['fluid_synth_path'] = fluid_synth_path

        if 'sound_font_path' not in self._config:
            sound_font_path = tkinter.filedialog.askopenfilename(
                initialdir=self._blood_path,
                title='Specify Sound Font Path to Use for Conversion',
                filetypes=(('Sound Font Files', '*.SF2'),)
            )

            if not sound_font_path:
                message = 'Unable to play music without a sound font, it will be disabled'
                tkinter.messagebox.showwarning(
                    title='Cannot play music',
                    message=message
                )
                sound_font_path = None

            self._config['sound_font_path'] = sound_font_path
    
        if self._current_addon_path is None:
            self._current_addon_path = f'{self._blood_path}/BLOOD.INI'

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

        self._open_from_rff_menu = tkinter.Menu(file_menu, tearoff=0)
        self._open_recent_menu = tkinter.Menu(file_menu, tearoff=0)

        file_menu.add_command(label="New (ctrl+n)", command=self._new_map)
        file_menu.add_command(label="Open (ctrl+o)", command=self._open_map)
        file_menu.add_cascade(label="Open Recent", menu=self._open_recent_menu)
        file_menu.add_cascade(label="Open From RFF", menu=self._open_from_rff_menu)
        file_menu.add_command(label="Save (ctrl+s)", command=self._save_map)
        file_menu.add_command(label="Save As", command=self._save_map_as)
        file_menu.add_separator()
        file_menu.add_command(label="Edit Mod", command=self._edit_mod)
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
        self._rff = RFF(f'{self._blood_path}/BLOOD.RFF')
        self._sounds_rff = RFF(f'{self._blood_path}/SOUNDS.RFF')
        self._addon = addon.Addon(self._current_addon_path)
        self._meta_data = {}

        for path in self._recent:
            self._add_recent_menu_item(path)

        for map_name in self._rff.find_matching_entries('*.MAP'):
            map_name = map_name[:constants.MAP_EXTENSION_SKIP]
            self._open_from_rff_menu.add_command(
                label=map_name,
                command=self._open_map_from_rff(map_name)
            )

        self._scene: core.NodePath = self.render.attach_new_node('scene')
        self._scene.set_scale(constants.SCENE_SCALE)

        self._camera_collection = cameras.Cameras(
            self.loader,
            self.win,
            self.render,
            self.render2d,
            self.aspect2d,
            self.a2dTopLeft,
            self._scene,
            cameras.Camera(
                self.cam,
                self.cam.node(),
                self.camLens,
                self.win.get_display_region(0)
            ),
            self.task_mgr
        )

        self._audio_manager = audio.Manager(
            self.loader,
            self.task_mgr,
            self._camera_collection.builder,
            self._sounds_rff,
            self._fluid_synth_path,
            self._sound_font_path
        )

        if self._path is None:
            self._path = self._last_map

        if self._path is None:
            self._make_new_board()

        self._add_recent(self._path)

        self._edit_mode_selector = edit_mode.EditMode(
            self.mouseWatcherNode,
            self.task_mgr
        )

        self._tile_manager = manager.Manager(
            self._blood_path,
            self._rff,
            self._edit_mode_selector
        )
        self._dialogs = dialogs.Dialogs(
            self.aspect2d,
            self._tile_manager,
            self._edit_mode_selector,
            self._audio_manager,
            self.task_mgr,
            lambda: addon.Addon.addons_in_path(self._blood_path)
        )

        self._mode_3d = edit_mode_3d.EditMode(
            self._dialogs,
            camera_collection=self._camera_collection,
            edit_mode_selector=self._edit_mode_selector,
            menu=self._edit_menu
        )

        self._map_editor: map_editor.MapEditor = None
        if not os.path.exists(self._path):
            map_to_load = game_map.Map()
            map_to_load.new()
            self._load_map_into_editor(map_to_load)
        else:
            self._do_open_map()

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
        self.accept('f9', self._run_map)

        self.task_mgr.add(self._update_for_frame, 'frame_update')

        return task.done

    def _make_new_board(self):
        self._path = os.path.join(self._blood_path, 'NEWBOARD.MAP')
        self._last_map = self._path

    def _update_for_frame(self, task):
        if self.mouseWatcherNode.has_mouse() or self.win.get_properties().get_foreground():
            self._audio_manager.unpause()
        else:
            self._audio_manager.pause()

        with self._edit_mode_selector.track_performance_stats('frame_update'):
            self._map_editor.update_for_frame()

        return task.cont

    def _tick_map_editor(self):
        with self._edit_mode_selector.track_performance_stats('map_editor_tick'):
            self._map_editor.tick()

    def _save_screenshot(self):
        self.screenshot('screenshot.png', defaultFilename=False)
        self._log_info('Saved screenshot to screenshot.png')

    def _run_map(self):
        if 'executable_path' not in self._config:
            path: str = tkinter.filedialog.askopenfilename(
                initialdir=self._blood_path,
                title='Path to Blood Executable',
                filetypes=(('Executable Files', '*.EXE'),)
            )
            if not path:
                return

            if not path.upper().endswith('.MAP'):
                path += '.MAP'

            self._config['executable_path'] = path
        raise NotImplementedError()

    def _load_map_into_editor(self, map_to_load: game_map.Map):
        if self._auto_save is not None:
            self._auto_save.stop()
            self._auto_save = None

        if self._map_editor is not None:
            self._map_editor.unload()
            self._map_editor = None

        self._audio_manager.clear()

        self._meta_data = {}
        if self._meta_data_path is not None and os.path.exists(self._meta_data_path):
            with open(self._meta_data_path, 'r') as file:
                self._meta_data = yaml.safe_load(file.read())

        self._map_editor = map_editor.MapEditor(
            self._camera_collection,
            map_to_load,
            self._audio_manager,
            self._tile_manager
        )

        self._setup_auto_save()
        self._mode_3d.set_editor(self._map_editor)

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

        builder_sector = self._map_editor.builder_sector
        if builder_sector is not None:
            position_2d = self._camera_collection.builder_2d.get_pos().xy
            builder_z = self._camera_collection.builder.get_z()
            floor_z = builder_sector.floor_z_at_point(position_2d)
            if builder_z > floor_z:
                self._camera_collection.builder.set_z(floor_z)
            ceiling_z = builder_sector.ceiling_z_at_point(position_2d)
            if builder_z < ceiling_z:
                self._camera_collection.builder.set_z(ceiling_z)

    def _setup_auto_save(self):
        if self._auto_save is not None:
            return

        if self._path:
            self._auto_save = auto_save.AutoSave(
                self._map_editor,
                self._meta_data,
                self._camera_collection,
                self._path
            )
            self.task_mgr.do_method_later(
                self._AUTO_SAVE_TIMEOUT,
                self._auto_save.perform_save,
                'auto-save'
            )

    @property
    def _last_map(self):
        return self._bloom_meta.get('last_map', None)

    @_last_map.setter
    def _last_map(self, value: str):
        self._bloom_meta['last_map'] = value

    @property
    def _recent(self):
        if 'recent' not in self._bloom_meta:
            self._bloom_meta['recent'] = []
        return self._bloom_meta['recent']

    @property
    def _blood_path(self):
        return self._config['blood_path']

    @property
    def _fluid_synth_path(self):
        return self._config.get('fluid_synth_path', None)

    @property
    def _sound_font_path(self):
        return self._config.get('sound_font_path', None)

    @property
    def _current_addon_path(self):
        return self._config.get('addon_path', None)
    
    @_current_addon_path.setter
    def _current_addon_path(self, value: str):
        self._config['addon_path'] = value

    @property
    def _meta_data_path(self):
        if self._path is None:
            return None

        base = self._path[:constants.MAP_EXTENSION_SKIP]
        return f'{base}.YAML'

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
            self._open_map_from_path(path)

    def _open_map_from_path_callback(self, path: str):
        def _callback():
            self._open_map_from_path(path)
        return _callback

    def _open_map_from_path(self, path: str):
        self._path = path
        self._last_map = self._path
        self._add_recent(self._path)
        self._do_open_map()

    def _add_recent(self, path: str):
        if not path:
            return

        path = self._full_path(path)
        if path not in self._recent:
            self._recent.append(path)
            self._open_recent_menu.add_command(
                label=path,
                command=self._open_map_from_path_callback(path)
            )

    def _add_recent_menu_item(self, path: str):
        path = self._full_path(path)
        self._open_recent_menu.add_command(
            label=path,
            command=self._open_map_from_path_callback(path)
        )

    @staticmethod
    def _full_path(path: str):
        path = os.path.expanduser(path)
        return os.path.abspath(path)

    def _open_map_from_rff(self, map_name: str):
        def _callback():
            self._path = None
            map_to_load, crc = game_map.Map.load(
                map_name,
                self._rff.data_for_entry(f'{map_name}.MAP')
            )
            self._load_map_into_editor(map_to_load)

            self._log_info(f'Loaded map {self._path} (hash: {hex(crc)})')

            song_name = self._addon.song_for_map(map_name)
            self._audio_manager.load_song(song_name)

        return _callback

    def _do_open_map(self):
        with open(self._path, 'rb') as file:
            map_to_load, crc = game_map.Map.load(self._path, file.read())
        self._load_map_into_editor(map_to_load)
        self._log_info(f'Loaded map {self._path} (hash: {hex(crc)})')

        map_name = os.path.basename(self._path)[:constants.MAP_EXTENSION_SKIP]
        song_name = self._addon.song_for_map(map_name)
        self._audio_manager.load_song(song_name)

    def _save_map_as(self):
        path = tkinter.filedialog.asksaveasfilename(
            initialdir=self._blood_path,
            title='Save map to...',
            filetypes=(('Map files', '*.MAP'),)
        )
        self._last_map = path
        if not path:
            return

        self._path = path
        self._save_map()
        self._setup_auto_save()

    def _save_map(self):
        if not self._path:
            self._save_map_as()
            return

        position = self._camera_collection.get_builder_position()
        map_to_save = self._map_editor.to_game_map(position)
        result, crc = map_to_save.save(self._path)
        with open(self._path, 'w+b') as file:
            file.write(result)

        with open(self._meta_data_path, 'w+') as file:
            file.write(yaml.dump(self._meta_data))

        self._log_info(f'Saved map to {self._path} (hash: {hex(crc)})')

    def _edit_mod(self):
        self._dialogs.mod_editor.show(self._map_editor, self._path)

    def _handle_exit(self):
        logger.info('Shutting down...')
        with open(self._CONFIG_PATH, 'w+') as file:
            file.write(yaml.dump(self._config))
        with open(self._META_PATH, 'w+') as file:
            file.write(yaml.dump(self._bloom_meta))
        self.tkRoot.destroy()

    def _log_info(self, message: str):
        logger.info(message)
        self._camera_collection.set_info_text(message)
