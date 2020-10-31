# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math

from panda3d import core

from .. import clicker, constants, tile_dialog
from . import drawing_mode_3d, edit_mode_2d, navigation_mode_3d

from ..utils import grid

class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        tile_selector: tile_dialog.TileDialog,
        mode_2d: edit_mode_2d.EditMode,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._grid = grid.make_grid(
            self._camera_collection.scene,
            'drawing_grid',
            2,
            100,
            core.Vec4(0.5, 0.55, 0.6, 0.85)
        )
        self._grid.hide()

        self._tile_selector = tile_selector
        self._mode_2d = mode_2d
        self._drawing_mode = drawing_mode_3d.EditMode(
            *args,
            **kwargs
        )

        self._tickers.append(self._mouse_collision_tests)
        self._tickers.append(self._grid.hide)

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self._select_object,
            on_double_click=self._show_tile_selector,
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

    def _select_object(self):
        self._editor.perform_select()

    def set_editor(self, editor):
        super().set_editor(editor)
        self._drawing_mode.set_editor(editor)

    def enter_mode(self):
        super().enter_mode()

        self._menu.add_command(label="Split (space)", command=self._split_selection)
        self._menu.add_command(
            label="Extrude (shift+space)",
            command=self._extrude_selection
        )
        self._menu.add_command(
            label="Start Drawing (insert)",
            command=self._start_drawing
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="Change tile (v)",
            command=self._show_tile_selector
        )

        self.accept('tab', self._enter_2d_mode)
        self.accept('space', self._split_selection)
        self.accept('shift-space', self._extrude_selection)
        self.accept('insert', self._start_drawing)
        self.accept('v', self._change_tile)
        self.accept('/', self._reset_panning_and_repeats)
        self.accept('p', self._swap_parallax)

    def _swap_parallax(self):
        self._editor.perform_select()
        selector = self._editor.get_selector()
        if selector is None:
            return

        selector.swap_parallax()

    def _reset_panning_and_repeats(self):
        self._editor.perform_select()
        selected, _ = self._editor.get_selected_and_last_hit_position()
        if selected is None:
            return

        selected.reset_panning_and_repeats()

    def _start_drawing(self):
        self._editor.perform_select()
        selected, hit_point = self._editor.get_selected_and_last_hit_position()
        if selected is None or not selected.is_geometry:
            return

        self._drawing_mode.start_drawing(selected, hit_point)

    def _extrude_selection(self):
        self._editor.split_highlight(True)

    def _split_selection(self):
        self._editor.split_highlight(False)

    def _enter_2d_mode(self):
        self._edit_mode_selector.push_mode(self._mode_2d)

    def _change_tile(self):
        self._select_object()
        self._show_tile_selector()

    def _show_tile_selector(self):
        self._tile_selector.show(self._editor.get_selected_picnum())

    def _mouse_collision_tests(self):
        source, target = self._extrude_mouse_to_render_transform(True)
        if source is None or target is None:
            return

        self._editor.highlight_mouse_hit(source, target)

    def _move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._do_move_selected(total_delta, delta, False)

    def _modified_move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        self._do_move_selected(total_delta, delta, True)

    def _do_move_selected(self, total_delta: core.Vec2, delta: core.Vec2, modified: bool):
        self._grid.set_scale(self._editor.snapper.grid_size)
        self._grid.set_pos(self._editor.get_selected_and_last_hit_position()[1])
        self._grid.show()

        camera_delta = self._transform_to_camera_delta(delta)
        total_camera_delta = self._transform_to_camera_delta(total_delta)

        self._editor.move_selection(
            total_delta * constants.TICK_SCALE,
            delta * constants.TICK_SCALE,
            total_camera_delta,
            camera_delta, 
            modified
        )