# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0



from panda3d import core

from .. import clicker, constants, dialogs
from ..editor import (event_grouping, geometry, highlighter, map_objects,
                      operations)
from . import (drawing_mode_3d, edit_mode_2d, moving_clicker,
               navigation_mode_3d, object_editor)


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        editor_dialogs: dialogs.Dialogs,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._dialogs = editor_dialogs
        self._object_editor = object_editor.ObjectEditor(
            self._dialogs,
            self._make_clicker,
            self._camera_collection,
            self._edit_mode_selector,
            self._menu
        )
        self._copy_picnum: int = None
        self._highlighter: highlighter.Highlighter = None
        self._drawing_mode = drawing_mode_3d.EditMode(
            *args,
            **kwargs
        )
        self._moving_clicker: moving_clicker.MovingClicker = None
        
        self._mode_2d = edit_mode_2d.EditMode(
            self._dialogs,
            camera_collection=self._camera_collection,
            edit_mode_selector=self._edit_mode_selector,
            menu=self._menu
        )

        self._tickers.append(self._mouse_collision_tests)
        self._tickers.append(self._update_mover)

        self._make_clicker(
            [core.KeyboardButton.shift(), core.MouseButton.one()],
            on_click=self._select_sector_geometry,
        )

        self._make_clicker(
            [core.KeyboardButton.control(), core.MouseButton.three()],
            on_click=self._copy_selected_picnum,
        )

        self._make_clicker(
            [core.KeyboardButton.shift(), core.MouseButton.three()],
            on_click=self._paste_selected_picnum,
        )

    def _select_sector_geometry(self):
        selected_sector = self._highlighter.select(
            selected_type_or_types=map_objects.EditorSector
        )
        if selected_sector is None:
            return

        selected_objects = [selected_sector.map_object]
        for wall in selected_sector.map_object.walls:
            selected_objects.append(wall)
        self._highlighter.set_selected_objects(selected_objects)
        self._highlighter.update_displays(self._editor.ticks)

    def _copy_selected_picnum(self):
        selected = self._highlighter.select()
        if selected is not None:
            if isinstance(selected.map_object, map_objects.EditorSprite):
                self._object_editor.set_copy_sprite(selected.map_object)
                self._mode_2d.set_copy_sprite(selected.map_object)
            else:
                self._copy_picnum = selected.map_object.get_picnum(selected.part)
        self._camera_collection.set_info_text('Copied')

    def _paste_selected_picnum(self):
        if self._copy_picnum is not None:
            selected = self._highlighter.select()
            if selected is not None:
                selected.map_object.set_picnum(selected.part, self._copy_picnum)
        self._camera_collection.set_info_text('Pasted')

    def set_editor(self, editor):
        super().set_editor(editor)
        self._mode_2d.set_editor(editor)
        self._drawing_mode.set_editor(editor)
        
        self._highlighter = highlighter.Highlighter(editor)
        self._object_editor.setup(self._editor, self._highlighter)
        
        self._moving_clicker = moving_clicker.MovingClicker(
            self._editor._scene,
            self._camera_collection,
            self._camera_collection.transform_to_camera_delta,
            self._highlighter,
            self._clicker_factory,
            self._editor.snapper,
            self._editor.sectors
        )

    def enter_mode(self, state: dict):
        super().enter_mode(state)

        self._menu.add_command(
            label="Enter 2d edit mode (tab)",
            command=self._enter_2d_mode
        )
        self._menu.add_separator()
        self._object_editor.setup_commands(self, self._context_menu)
        self._menu.add_separator()
        self._menu.add_command(
            label="Start Drawing (insert)",
            command=self._start_drawing
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="Reset panning/repeats (/)",
            command=self._reset_panning_and_repeats
        )
        self._menu.add_command(
            label="Toggle sky (parallax) (p)",
            command=self._swap_parallax
        )

        self.accept('tab', self._enter_2d_mode)
        self.accept('insert', self._start_drawing)
        self.accept('/', self._reset_panning_and_repeats)
        self.accept('p', self._swap_parallax)
        
        self.accept('shift-arrow_right', self._increase_panning_x)
        self.accept('shift-arrow_right-repeat', self._increase_panning_x)
        self.accept('shift-arrow_left', self._decrease_panning_x)
        self.accept('shift-arrow_left-repeat', self._decrease_panning_x)
        self.accept('shift-arrow_up', self._increase_panning_y)
        self.accept('shift-arrow_up-repeat', self._increase_panning_y)
        self.accept('shift-arrow_down', self._decrease_panning_y)
        self.accept('shift-arrow_down-repeat', self._decrease_panning_y)
        
        self.accept('control-arrow_right', self._increase_repeats_x)
        self.accept('control-arrow_right-repeat', self._increase_repeats_x)
        self.accept('control-arrow_left', self._decrease_repeats_x)
        self.accept('control-arrow_left-repeat', self._decrease_repeats_x)
        self.accept('control-arrow_up', self._increase_repeats_y)
        self.accept('control-arrow_up-repeat', self._increase_repeats_y)
        self.accept('control-arrow_down', self._decrease_repeats_y)
        self.accept('control-arrow_down-repeat', self._decrease_repeats_y)
    
        self.accept('shift-.', self._align_walls)

        self.accept('escape', self._highlighter.deselect_all)
        self._moving_clicker.setup_keyboard(self)

        if constants.PORTALS_DEBUGGING_ENABLED:
            self.accept('0', self._toggle_view_clipping)

        if 'selected' in state:
            self._highlighter.clear()
            self._highlighter.set_selected(state['selected'])
            self._highlighter.update_displays(self._editor.ticks)
        if 'highlighted' in state:
            self._highlighter.set_highlighted(state['highlighted'])
        if 'grid_visible' in state:
            if state['grid_visible']:
                self._moving_clicker.show_grid()
        else:
            self._moving_clicker.show_grid()

        self._highlighter.update_selected_target_view()

    def exit_mode(self):
        state = super().exit_mode()
        state['selected'] = list(self._highlighter.selected)
        state['highlighted'] = self._highlighter.highlighted
        state['grid_visible'] = self._moving_clicker.grid_visible
        
        self._moving_clicker.hide_grid()
        self._highlighter.clear()
        return state

    def _increase_panning_x(self):
        self._increment_panning(core.Vec2(1, 0))

    def _decrease_panning_x(self):
        self._increment_panning(core.Vec2(-1, 0))

    def _increase_panning_y(self):
        self._increment_panning(core.Vec2(0, 1))

    def _decrease_panning_y(self):
        self._increment_panning(core.Vec2(0, -1))

    def _increment_panning(self, amount: core.Vec2):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True
        )

        for selected_item in selected:
            operations.increment_panning.IncrementPanning(
                selected_item.map_object, 
                selected_item.part
            ).increment(amount)

    def _increase_repeats_x(self):
        self._increment_repeats(core.Vec2(1, 0))

    def _decrease_repeats_x(self):
        self._increment_repeats(core.Vec2(-1, 0))

    def _increase_repeats_y(self):
        self._increment_repeats(core.Vec2(0, 1))

    def _decrease_repeats_y(self):
        self._increment_repeats(core.Vec2(0, -1))

    def _increment_repeats(self, amount: core.Vec2):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True
        )

        for selected_item in selected:
            operations.increment_repeats.IncrementRepeats(
                selected_item.map_object, 
                selected_item.part
            ).increment(amount)

    def _align_walls(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorWall
        )
        if selected is None:
            return

        operations.wall_align.WallAlign(selected.map_object).align()

    def _update_mover(self):
        if self._moving_clicker is not None:
            self._moving_clicker.tick()

    def _toggle_view_clipping(self):
        self._editor.toggle_view_clipping()

    def _swap_parallax(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorSector)
        if selected is None:
            return

        selected.map_object.swap_parallax(selected.part)

    def _reset_panning_and_repeats(self):
        selected = self._highlighter.select_append(no_append_if_not_selected=True)
        for selected_item in selected:
            selected_item.map_object.reset_panning_and_repeats(selected_item.part)

    def _start_drawing(self):
        selected = self._highlighter.select()
        if selected is None:
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

    def _enter_2d_mode(self):
        self._edit_mode_selector.push_mode(self._mode_2d)

    def _mouse_collision_tests(self):
        with self._edit_mode_selector.track_performance_stats('mouse_collision_tests'):
            highlight_finder = self._make_highlight_finder_callback()
            self._highlighter.update(highlight_finder)
            self._highlighter.update_displays(self._editor.ticks)

    def _select_sprites(self):
        yield from self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=map_objects.EditorSprite
        )
