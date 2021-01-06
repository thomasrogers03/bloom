# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import cameras, constants, dialogs
from ..editor import highlighter, map_objects, operations
from ..editor.highlighting import find_in_marquee, highlight_finder_2d
from . import (base_edit_mode, drawing_mode_2d, keyboard_camera,
               moving_clicker, navigation_mode_2d, object_editor, wall_bevel)


class EditMode(navigation_mode_2d.EditMode):

    def __init__(
        self,
        editor_dialogs: dialogs.Dialogs,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._drawing_mode = drawing_mode_2d.EditMode(
            *args,
            **kwargs
        )
        self._highlighter: highlighter.Highlighter = None

        self._object_editor = object_editor.ObjectEditor(
            editor_dialogs,
            self._make_clicker,
            self._camera_collection,
            self._edit_mode_selector,
            self._menu
        )
        self._moving_clicker: moving_clicker.MovingClicker = None
        self._marquee_start = core.Point2()
        self._marquee_end = core.Point2()
        self._marquee_display: core.NodePath = None

        self._wall_bevel_editor = wall_bevel.EditMode(*args, **kwargs)
        self._sector_prefab: operations.sector_copy.SectorCopy = None

        self._make_clicker(
            [core.KeyboardButton.alt(), core.MouseButton.one()],
            on_mouse_down=self._start_selection_marquee,
            on_click_move=self._move_selection_marquee,
            on_click_after_move=self._select_from_marquee,
        )

        self._tickers.append(self._mouse_collision_tests)
        self._tickers.append(self._update_mover)

    def set_editor(self, editor):
        super().set_editor(editor)
        self._highlighter = highlighter.Highlighter(editor)
        self._object_editor.setup(self._editor, self._highlighter)

        self._wall_bevel_editor.set_editor(editor)
        self._drawing_mode.set_editor(editor)

        self._moving_clicker = moving_clicker.MovingClicker(
            self._editor._scene,
            self._camera_collection,
            self._transform_to_camera_delta,
            self._highlighter,
            self._clicker_factory,
            self._editor.snapper,
            self._editor.sectors,
            self._editor.undo_stack
        )

    def enter_mode(self, state: dict):
        super().enter_mode(state)
        self._object_editor.setup_commands(self, self._context_menu)

        self.accept('tab', lambda: self._edit_mode_selector.pop_mode())
        self.accept('insert', self._start_drawing)
        self.accept('c', self._bevel_wall)

        self._moving_clicker.setup_keyboard(self)

        self._context_menu.add_command('Copy Sectors', self._copy_sectors)
        self._context_menu.add_command('Paste Sectors', self._paste_sectors)
        self._context_menu.add_command('Flip Sectors Vertically', self._flip_sectors_vertically)
        self._context_menu.add_command('Flip Sectors Horizontally', self._flip_sectors_horizontally)

        if 'grid_visible' in state:
            if state['grid_visible']:
                self._moving_clicker.show_grid()
        else:
            self._moving_clicker.show_grid()
    
    def exit_mode(self):
        state = super().exit_mode()
        state['grid_visible'] = self._moving_clicker.grid_visible

        self._moving_clicker.hide_grid()
        self._highlighter.clear()
        return state

    def set_copy_sprite(self, sprite: map_objects.EditorSprite):
        self._object_editor.set_copy_sprite(sprite)

    def _copy_sectors(self):
        sectors = self._gather_selected_sectors()
        if len(sectors) < 1:
            return

        self._sector_prefab = operations.sector_copy.SectorCopy(
            list(sectors),
            self._editor.sectors
        )
    
    def _paste_sectors(self):
        if self._sector_prefab is None:
            return

        source, _ = self._extrude_mouse_to_scene_transform(check_buttons=True)
        if source is None:
            return

        target = self._editor.snapper.snap_to_grid_2d(source.xy)
        new_sectors = self._sector_prefab.copy(target)
        self._highlighter.clear()
        self._highlighter.set_selected_objects(new_sectors)

    def _flip_sectors_vertically(self):
        sectors = self._gather_selected_sectors()
        operations.sector_flip.SectorFlip(sectors).flip(True, False)

    def _flip_sectors_horizontally(self):
        sectors = self._gather_selected_sectors()
        operations.sector_flip.SectorFlip(sectors).flip(False, True)

    def _gather_selected_sectors(self) -> typing.List:
        sectors: typing.Set[map_objects.EditorSector] = set()
        for selected_item in self._highlighter.selected:
            if selected_item.is_sector:
                sectors.add(selected_item.map_object)

        return list(sectors)

    def _start_drawing(self):
        selected = self._highlighter.select()
        if selected is None:
            self._start_drawing_new_sector()
            return

        if isinstance(selected.map_object, map_objects.EditorSector):
            insert = True
        elif isinstance(selected.map_object, map_objects.EditorWall):
            insert = False
        else:
            insert = True

        self._drawing_mode.start_drawing(
            selected.map_object.get_sector(),
            selected.hit_position,
            insert
        )

    def _start_drawing_new_sector(self):
        source, target = self._extrude_mouse_to_scene_transform(check_buttons=True)
        if source is None:
            return

        self._drawing_mode.start_drawing(
            None,
            target,
            True
        )

    def _start_selection_marquee(self, mouse_down_point: core.Point2):
        self._marquee_start = mouse_down_point

    def _move_selection_marquee(self, total_delta: core.Vec2, delta: core.Vec2):
        self._clear_marquee_display()
        self._marquee_end = self._marquee_start + total_delta
        
        start, end = self._get_marquee()

        card_maker = core.CardMaker('marquee')
        card_maker.set_frame(
            core.Point3(start.x, start.y, -constants.REALLY_BIG_NUMBER),
            core.Point3(start.x, end.y, -constants.REALLY_BIG_NUMBER),
            core.Point3(end.x, end.y, -constants.REALLY_BIG_NUMBER),
            core.Point3(end.x, start.y, -constants.REALLY_BIG_NUMBER)
        )
        card_maker.set_color(1, 1, 0, 0.5)
        
        marquee_node = card_maker.generate()
        self._marquee_display: core.NodePath = self._camera_collection.scene.attach_new_node(marquee_node)
        self._marquee_display.set_transparency(True)

    def _select_from_marquee(self):
        self._highlighter.deselect_all()

        self._clear_marquee_display()
        start, end = self._get_marquee()

        finder = find_in_marquee.FindInMarquee(
            self._editor.sectors.sectors, 
            start.xy,
            end.xy
        )

        self._highlighter.update_selection(finder.get_objects())

    def _clear_marquee_display(self):
        if self._marquee_display is not None:
            self._marquee_display.remove_node()
            self._marquee_display = None

    def _get_marquee(self):
        start_2d = core.Point3()
        far = core.Point3()
        self._camera.lens.extrude(self._marquee_start, start_2d, far)

        end_2d = core.Point3()
        far = core.Point3()
        self._camera.lens.extrude(self._marquee_end, end_2d, far)
        
        start = self._camera_collection.scene.get_relative_point(self._camera.camera, start_2d)
        end = self._camera_collection.scene.get_relative_point(self._camera.camera, end_2d)

        left = min(start.x, end.x)
        right = max(start.x, end.x)
        bottom = min(start.y, end.y)
        top = max(start.y, end.y)

        return core.Point2(left, bottom), core.Point2(right, top)

    def _bevel_wall(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return

        self._wall_bevel_editor.set_wall(selected.map_object)
        self._edit_mode_selector.push_mode(self._wall_bevel_editor)

    def _update_mover(self):
        self._moving_clicker.tick()

    def _transform_to_camera_delta(self, mouse_delta: core.Vec2):
        scale = self._camera_scale() / moving_clicker.MovingClicker.MOVE_SCALE
        return core.Vec3(
            (mouse_delta.x * scale.x) / 2,
            -(mouse_delta.y * scale.y) / 2,
            -mouse_delta.y
        )

    def _mouse_collision_tests(self):
        with self._edit_mode_selector.track_performance_stats('mouse_collision_tests_2d'):
            highlight_finder = self._make_highlight_finder_callback()
            self._highlighter.update(highlight_finder)
            self._highlighter.update_displays(self._editor.ticks)

    def _make_highlight_finder_callback(self):
        source, _ = self._extrude_mouse_to_scene_transform(check_buttons=True)
        if source is None:
            return lambda highlight, _: highlight

        return highlight_finder_2d.HighlightFinder2D(self._editor, source.xy, self._camera_scale()).find_highlight

    def _camera_scale(self):
        film_size = self._camera.lens.get_film_size()
        scale = self._camera.camera.get_scale()
        return core.Vec2(film_size.x * scale.x, film_size.y * scale.y)
