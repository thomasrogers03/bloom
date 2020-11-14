# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math
import typing

from panda3d import core

from .. import clicker, constants, dialogs
from ..editor import geometry, highlighter, map_objects, operations
from . import (drawing_mode_3d, edit_mode_2d, moving_clicker_3d,
               navigation_mode_3d)


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        editor_dialogs: dialogs.Dialogs,
        mode_2d: edit_mode_2d.EditMode,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._dialogs = editor_dialogs
        self._mode_2d = mode_2d
        self._copy_picnum: int = None
        self._copy_sprite: map_objects.EditorSprite = None
        self._highlighter: highlighter.Highlighter = None
        self._drawing_mode = drawing_mode_3d.EditMode(
            *args,
            **kwargs
        )
        self._moving_clicker_3d: moving_clicker_3d.MovingClicker3D = None

        self._tickers.append(self._mouse_collision_tests)
        self._tickers.append(self._update_mover)

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self._select_object,
            on_double_click=self._edit_object_properties
        )

        self._make_clicker(
            [core.MouseButton.two()],
            on_click=self._copy_selected_picnum,
        )

        self._make_clicker(
            [core.MouseButton.three()],
            on_click=self._paste_selected_picnum,
        )

        self._make_clicker(
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click=self._select_object_append,
        )

    def _copy_selected_picnum(self):
        selected = self._highlighter.select()
        if selected is not None:
            if isinstance(selected.map_object, map_objects.EditorSprite):
                self._copy_sprite = selected.map_object
            else:
                self._copy_picnum = selected.map_object.get_picnum(selected.part)

    def _paste_selected_picnum(self):
        if self._copy_picnum is not None:
            selected = self._highlighter.select()
            if selected is not None:
                selected.map_object.set_picnum(selected.part, self._copy_picnum)

    def _edit_object_properties(self):
        selected = self._highlighter.select()
        if selected is None:
            return

        if isinstance(selected.map_object, map_objects.sprite.EditorSprite):
            self._dialogs.sprite_properties.show(selected.map_object)

    def _select_object(self):
        self._highlighter.select()

    def _select_object_append(self):
        self._highlighter.select_append()

    def set_editor(self, editor):
        super().set_editor(editor)
        self._drawing_mode.set_editor(editor)
        self._highlighter = highlighter.Highlighter(editor)
        self._moving_clicker_3d = moving_clicker_3d.MovingClicker3D(
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
        self._menu.add_command(
            label="Reset panning/repeats (/)",
            command=self._reset_panning_and_repeats
        )
        self._menu.add_command(
            label="Toggle sky (parallax) (p)",
            command=self._swap_parallax
        )

        self.accept('tab', self._enter_2d_mode)
        self.accept('space', self._split_selection)
        self.accept('shift-space', self._extrude_selection)
        self.accept('insert', self._start_drawing)
        self.accept('v', self._change_tile)
        self.accept('s', self._add_sprite)
        self.accept('delete', self._delete_selected)
        self.accept('/', self._reset_panning_and_repeats)
        self.accept('p', self._swap_parallax)
        self.accept('j', self._join_sectors)

        self.accept('[', self._decrease_grid)
        self.accept(']', self._increase_grid)

        self.accept('-', self._decrease_shade)
        self.accept('--repeat', self._decrease_shade)
        self.accept('=', self._increase_shade)
        self.accept('=-repeat', self._increase_shade)

        self.accept(';', self._decrease_slope)
        self.accept(';-repeat', self._decrease_slope)
        self.accept("'", self._increase_slope)
        self.accept("'-repeat", self._increase_slope)

        self.accept('home', self._move_sprite_to_ceiling)
        self.accept('end', self._move_sprite_to_floor)

        self.accept('r', self._change_sprite_facing)
        self.accept('f', self._flip_sprite)

        self.accept('escape', self._highlighter.deselect_all)
        self.accept('g', self._toggle_grid)

        self.accept(',', self._decrease_sprite_angle)
        self.accept('.', self._increase_sprite_angle)

        if constants.PORTALS_DEBUGGING_ENABLED:
            self.accept('1', self._toggle_view_clipping)

    def _toggle_grid(self):
        self._moving_clicker_3d.toggle_grid()

    def _decrease_sprite_angle(self):
        for selected_item in self._select_sprites():
            operations.sprite_angle_update.SpriteAngleUpdate(selected_item.map_object).increment(-15)

    def _increase_sprite_angle(self):
        for selected_item in self._select_sprites():
            operations.sprite_angle_update.SpriteAngleUpdate(selected_item.map_object).increment(15)

    def _update_mover(self):
        self._moving_clicker_3d.tick()

    def _decrease_grid(self):
        self._editor.snapper.decrease_grid()

    def _increase_grid(self):
        self._editor.snapper.increase_grid()

    def _decrease_shade(self):
        self._increment_shade(-0.01)

    def _increase_shade(self):
        self._increment_shade(0.01)

    def _increment_shade(self, amount):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True
        )

        for selected_item in selected:
            shade = selected_item.map_object.get_shade(selected_item.part)
            selected_item.map_object.set_shade(selected_item.part, shade + amount)

    def _decrease_slope(self):
        self._increment_slope(-0.01)

    def _increase_slope(self):
        self._increment_slope(0.01)

    def _increment_slope(self, amount):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type=map_objects.EditorSector
        )

        for selected_item in selected:
            heinum = selected_item.map_object.get_heinum(selected_item.part)
            selected_item.map_object.set_heinum(selected_item.part, heinum + amount)

    def _move_sprite_to_floor(self):
        for selected_item in self._select_sprites():
            selected_object = selected_item.map_object
            editor_sector = selected_object.get_sector()
            new_z = editor_sector.floor_z_at_point(selected_object.origin_2d)
            new_z -= selected_object.size.y / 2

            selected_object.move_to(
                core.Point3(
                    selected_object.origin_2d.x,
                    selected_object.origin_2d.y,
                    new_z
                )
            )

    def _move_sprite_to_ceiling(self):
        for selected_item in self._select_sprites():
            selected_object = selected_item.map_object
            editor_sector = selected_object.get_sector()
            new_z = editor_sector.ceiling_z_at_point(selected_object.origin_2d)
            new_z += selected_object.size.y / 2

            selected_object.move_to(
                core.Point3(
                    selected_object.origin_2d.x,
                    selected_object.origin_2d.y,
                    new_z
                )
            )

    def _change_sprite_facing(self):
        for selected_item in self._select_sprites():
            operations.sprite_facing.SpriteFacing(selected_item.map_object).change_facing()

    def _flip_sprite(self):
        for selected_item in self._select_sprites():
            operations.sprite_flip.SpriteFlip(selected_item.map_object).flip()

    def _join_sectors(self):
        selected = self._highlighter.select_append(
            selected_type=map_objects.EditorSector
        )
        if len(selected) == 2:
            self._do_join(selected[0].map_object, selected[1].map_object)

    def _do_join(self, sector_1: map_objects.EditorSector, sector_2: map_objects.EditorSector):
        operations.sector_join.SectorJoin(sector_1, sector_2).join()
        self._editor.update_builder_sector(
            self._camera_collection.get_builder_position(),
            force=True
        )
        self._highlighter.clear()

    def _toggle_view_clipping(self):
        self._editor.toggle_view_clipping()

    def _swap_parallax(self):
        selected = self._highlighter.select(selected_type=map_objects.EditorSector)
        if selected is None:
            return

        selected.map_object.swap_parallax(selected.part)

    def _add_sprite(self):
        selected = self._highlighter.select(selected_type=map_objects.EditorSector)
        if selected is None:
            return

        if self._copy_sprite is None:
            selected.map_object.add_new_sprite(selected.hit_position)
        else:
            blood_sprite = self._copy_sprite.sprite.copy()
            sprite = selected.map_object.add_sprite(blood_sprite)
            sprite.move_to(selected.hit_position)

    def _delete_selected(self):
        selected = self._highlighter.select_append(no_append_if_not_selected=True)

        for selected_item in selected:
            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                selected_item.map_object.sector.remove_sprite(selected_item.map_object)
            elif isinstance(selected_item.map_object, map_objects.EditorWall):
                operations.wall_delete.WallDelete(selected_item.map_object).delete()
            else:
                operations.sector_delete.SectorDelete(
                    selected_item.map_object,
                    self._editor.sectors
                ).delete()

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

    def _extrude_selection(self):
        selected = self._highlighter.select()
        if selected is None:
            return

        if isinstance(selected.map_object, map_objects.EditorWall):
            operations.wall_extrude.WallExtrude(
                selected.map_object,
                self._editor.sectors
            ).extrude()
        elif isinstance(selected.map_object, map_objects.EditorSector):
            extrustion = operations.sector_extrude.SectorExtrude(
                selected.map_object,
                selected.part
            )
            extrustion.extrude(self._editor.find_unused_sprite_data_1())
        self._editor.invalidate_view_clipping()

    def _split_selection(self):
        selected = self._highlighter.select(selected_type=map_objects.EditorWall)
        if selected is None:
            return

        where = self._editor.snapper.snap_to_grid_2d(selected.hit_position.xy)
        operations.wall_split.WallSplit(selected.map_object).split(where)

    def _enter_2d_mode(self):
        self._edit_mode_selector.push_mode(self._mode_2d)

    def _change_tile(self):
        self._highlighter.select_append(no_append_if_not_selected=True)
        self._show_tile_selector()

    def _show_tile_selector(self):
        if len(self._highlighter.selected) < 1:
            return

        last_selected = self._highlighter.selected[-1]
        picnum = last_selected.map_object.get_picnum(last_selected.part)
        self._dialogs.tile_dialog.load_tiles()
        self._dialogs.tile_dialog.show(picnum, self._handle_tile_selected)

    def _handle_tile_selected(self, picnum: int):
        for selected in self._highlighter.selected:
            selected.map_object.set_picnum(selected.part, picnum)

    def _mouse_collision_tests(self):
        with self._edit_mode_selector.track_performance_stats('mouse_collision_tests'):
            source, target = self._extrude_mouse_to_scene_transform(True)
            if source is None or target is None:
                return

            self._highlighter.update(source, target)
            self._highlighter.update_displays(self._editor.ticks)

    def _select_sprites(self):
        yield from self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type=map_objects.EditorSprite
        )
