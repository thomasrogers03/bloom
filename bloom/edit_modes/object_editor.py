# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


from direct.showbase import DirectObject
from panda3d import core

from .. import cameras, dialogs, edit_menu, edit_mode, editor
from ..editor import highlighter, map_editor, map_objects, operations
from .sector_effects import property_editor


class ObjectEditor:

    def __init__(
        self, 
        editor_dialogs: dialogs.Dialogs,
        make_clicker_callback,
        camera_collection: cameras.Cameras,
        edit_mode_selector: edit_mode.EditMode,
        menu: edit_menu.EditMenu
    ):
        self._dialogs = editor_dialogs
        self._editor: map_editor.MapEditor = None
        self._highlighter: highlighter.Highlighter = None
        self._camera_collection = camera_collection
        self._edit_mode_selector = edit_mode_selector
        self._menu = menu

        self._property_editor = property_editor.EditMode(
            camera_collection=self._camera_collection,
            edit_mode_selector=self._edit_mode_selector,
            menu=self._menu
        )

        self._copy_sprite: map_objects.EditorSprite = None

        make_clicker_callback(
            [core.MouseButton.one()],
            on_click=self._select_object,
            on_double_click=self._edit_object_properties
        )

        make_clicker_callback(
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click=self._select_object_append,
        )


    def setup(self, editor: map_editor.MapEditor, object_highlighter: highlighter.Highlighter):
        self._editor = editor
        self._property_editor.set_editor(self._editor)
        self._highlighter = object_highlighter

    def setup_commands(self, event_handler: DirectObject.DirectObject):
        self._menu.add_command(
            label="Join sectors (j)",
            command=self._join_sectors
        )
        self._menu.add_command(label="Split (space)", command=self._split_selection)
        self._menu.add_command(
            label="Extrude (shift+space)",
            command=self._extrude_selection
        )
        self._menu.add_command(
            label="Delete selected object (delete)",
            command=self._delete_selected
        )
        self._menu.add_command(
            label="Bind objects together for actions (b)",
            command=self._bind_objects
        )
        self._menu.add_command(
            label="Decrease shade (-)",
            command=self._decrease_shade
        )
        self._menu.add_command(
            label="Increase shade (+)",
            command=self._increase_shade
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="Change tile (v)",
            command=self._show_tile_selector
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="Insert sprite (s)",
            command=self._add_sprite
        )
        self._menu.add_command(
            label="Move sprite to ceiling (home)",
            command=self._move_selected_sprites_to_ceiling
        )
        self._menu.add_command(
            label="Move sprite to floor (end)",
            command=self._move_selected_sprites_to_floor
        )
        self._menu.add_command(
            label="Decrease sprite angle (,)",
            command=self._decrease_angle
        )
        self._menu.add_command(
            label="Decrease sprite angle (.)",
            command=self._increase_angle
        )
        self._menu.add_command(
            label="Change sprite facing attribute (r)",
            command=self._change_sprite_facing_or_set_relative
        )
        self._menu.add_command(
            label="Toggle sector floor/ceiling relative to first wall (r)",
            command=self._change_sprite_facing_or_set_relative
        )
        self._menu.add_command(
            label="Flip sprite/wall/sector floor/wall (f)",
            command=self._flip
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="Set sector reference wall (1)",
            command=self._set_sector_first_wall
        )
        self._menu.add_command(
            label="Swap wall texture (2)",
            command=self._swap_lower_texture
        )
        self._menu.add_command(
            label="Change wall texture pegging (o)",
            command=self._toggle_wall_peg
        )
        self._menu.add_command(
            label="Decrease sector slope (;)",
            command=self._decrease_slope
        )
        self._menu.add_command(
            label="Increase sector slope (')",
            command=self._increase_slope
        )

        event_handler.accept('j', self._join_sectors)
        event_handler.accept('space', self._split_selection)
        event_handler.accept('shift-space', self._extrude_selection)
        event_handler.accept('v', self._change_tile)
        event_handler.accept('s', self._add_sprite)
        event_handler.accept('delete', self._delete_selected)
        event_handler.accept('b', self._bind_objects)
        event_handler.accept('n', self._toggle_blocking_state)

        event_handler.accept('home', self._move_selected_sprites_to_ceiling)
        event_handler.accept('end', self._move_selected_sprites_to_floor)

        event_handler.accept(',', self._decrease_angle)
        event_handler.accept(',-repeat', self._decrease_angle)
        event_handler.accept('.', self._increase_angle)
        event_handler.accept('.-repeat', self._increase_angle)

        event_handler.accept('1', self._set_sector_first_wall)
        event_handler.accept('2', self._swap_lower_texture)

        event_handler.accept(';', self._decrease_slope)
        event_handler.accept(';-repeat', self._decrease_slope)
        event_handler.accept("'", self._increase_slope)
        event_handler.accept("'-repeat", self._increase_slope)

        event_handler.accept('r', self._change_sprite_facing_or_set_relative)
        event_handler.accept('f', self._flip)
        event_handler.accept('o', self._toggle_wall_peg)

        event_handler.accept('-', self._decrease_shade)
        event_handler.accept('--repeat', self._decrease_shade)
        event_handler.accept('=', self._increase_shade)
        event_handler.accept('=-repeat', self._increase_shade)


    def set_copy_sprite(self, sprite: map_objects.EditorSprite):
        self._copy_sprite = sprite

    def _edit_object_properties(self):
        selected = self._highlighter.select()
        if selected is None:
            return

        if isinstance(selected.map_object, map_objects.sprite.EditorSprite):
            self._dialogs.sprite_properties.show(selected.map_object)
        elif isinstance(selected.map_object, map_objects.EditorSector):
            self._property_editor.set_sector(selected.map_object)
            self._edit_mode_selector.push_mode(self._property_editor)

        self._highlighter.update_selected_target_view()

    def _select_object(self):
        self._highlighter.select()

    def _select_object_append(self):
        self._highlighter.select_append()

    def _decrease_shade(self):
        self._increment_shade(-0.01)

    def _increase_shade(self):
        self._increment_shade(0.01)

    def _increment_shade(self, amount):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True
        )

        original_shades = [
            selected_item.map_object.get_shade(selected_item.part)
            for selected_item in selected
        ]

        for index, selected_item in enumerate(selected):
            shade = original_shades[index]
            selected_item.map_object.set_shade(selected_item.part, shade + amount)
        
        if len(selected) > 0:
            first_selected = selected[0]
            shade = first_selected.map_object.get_shade(first_selected.part)
            build_shade = editor.to_build_shade(shade)
            self._camera_collection.set_info_text(f'Shade: {build_shade}')

    def _change_sprite_facing_or_set_relative(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[map_objects.EditorSprite, map_objects.EditorSector]
        )

        for selected_item in selected:
            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                operations.sprite_facing.SpriteFacing(selected_item.map_object).change_facing()
            else:
                operations.sector_relative_swap.SectorRelativeSwap(
                    selected_item.map_object,
                    selected_item.part
                ).toggle()

    def _flip(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True
        )

        for selected_item in selected:
            operations.flip.Flip(selected_item.map_object, selected_item.part).flip()

    def _bind_objects(self):
        selected = self._highlighter.select_append()
        if len(selected) < 2:
            return

        transmitter = selected[-1]
        receivers = selected[:-1]

        selected_objects = [item.map_object for item in receivers]
        grouping = self._editor.sectors.event_groupings.get_grouping(transmitter.map_object, selected_objects)
        if grouping is None:
            return

        transmitter.map_object.set_target_event_grouping(grouping)

        for selected_object in receivers:
            selected_object.map_object.set_source_event_grouping(grouping)
        self._highlighter.update_selected_target_view()

    def _toggle_blocking_state(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[
                map_objects.EditorWall, 
                map_objects.EditorSprite
            ]
        )

        for selected_item in selected:
            operations.object_blocking.ObjectBlocking(
                selected_item.map_object,
                selected_item.part
            ).toggle()

    def _decrease_slope(self):
        self._increment_slope(-0.01)

    def _increase_slope(self):
        self._increment_slope(0.01)

    def _increment_slope(self, amount):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=map_objects.EditorSector
        )

        for selected_item in selected:
            heinum = selected_item.map_object.get_heinum(selected_item.part)
            selected_item.map_object.set_heinum(selected_item.part, heinum + amount)

        if len(selected) > 0:
            first_selected = selected[0]
            heinum = first_selected.map_object.get_heinum(first_selected.part)
            build_heinum = editor.to_build_heinum(heinum)
            self._camera_collection.set_info_text(f'Heinum: {build_heinum}')

    def _set_sector_first_wall(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return

        selected.map_object.get_sector().set_first_wall(selected.map_object)

    def _swap_lower_texture(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return

        operations.swap_wall_bottom.SwapWallBottom(selected.map_object).toggle()

    def _toggle_wall_peg(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return
        
        operations.swap_wall_peg.SwapWallPeg(selected.map_object, selected.part).toggle()

    def _decrease_angle(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[map_objects.EditorSector, map_objects.EditorSprite]
        )

        for selected_item in selected:
            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                operations.sprite_angle_update.SpriteAngleUpdate(selected_item.map_object).increment(-15)
            elif isinstance(selected_item.map_object, map_objects.EditorSector):
                operations.sector_rotate.SectorRotate(selected_item.map_object).rotate(-15)

    def _increase_angle(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[map_objects.EditorSector, map_objects.EditorSprite]
        )

        for selected_item in selected:
            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                operations.sprite_angle_update.SpriteAngleUpdate(selected_item.map_object).increment(15)
            elif isinstance(selected_item.map_object, map_objects.EditorSector):
                operations.sector_rotate.SectorRotate(selected_item.map_object).rotate(15)

    def _delete_selected(self):
        selected = self._highlighter.select_append(no_append_if_not_selected=True)

        for selected_item in selected:
            if selected_item.map_object.is_marker:
                continue

            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                selected_item.map_object.sector.remove_sprite(selected_item.map_object)
            elif isinstance(selected_item.map_object, map_objects.EditorWall):
                operations.wall_delete.WallDelete(selected_item.map_object).delete()
            else:
                operations.sector_delete.SectorDelete(
                    selected_item.map_object,
                    self._editor.sectors
                ).delete()

    def _add_sprite(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorSector)
        if selected is None:
            return

        hit_position = self._editor.snapper.snap_to_grid_3d(selected.hit_position)
        if self._copy_sprite is None:
            selected.map_object.add_new_sprite(hit_position)
        else:
            blood_sprite = self._copy_sprite.sprite.copy()
            sprite = selected.map_object.add_sprite(blood_sprite)
            sprite.move_to(hit_position)
            sprite.set_source_event_grouping(self._copy_sprite.source_event_grouping)
            self._move_sprite_to_floor(sprite)

    def _move_selected_sprites_to_floor(self):
        for selected_item in self._select_sprites():
            self._move_sprite_to_floor(selected_item.map_object)

    def _move_sprite_to_floor(self, sprite: map_objects.EditorSprite):
        editor_sector = sprite.get_sector()
        new_z = editor_sector.floor_z_at_point(sprite.origin_2d)
        sprite.set_z_at_bottom(new_z)

    def _move_selected_sprites_to_ceiling(self):
        for selected_item in self._select_sprites():
            self._move_sprite_to_ceiling(selected_item.map_object)

    def _move_sprite_to_ceiling(self, sprite: map_objects.EditorSprite):
        editor_sector = sprite.get_sector()
        new_z = editor_sector.ceiling_z_at_point(sprite.origin_2d)
        sprite.set_z_at_top(new_z)

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
            callback = self._extrude_sector_callback(selected.map_object, selected.part)
            self._dialogs.ror_type_selector.show(callback)
        self._editor.invalidate_view_clipping()

    def _extrude_sector_callback(self, map_object: map_objects.EmptyObject, part: str):
        def _callback(extrude_type: str):
            extrustion = operations.sector_extrude.SectorExtrude(
                map_object,
                self._editor.sectors,
                part
            )
            extrustion.extrude(self._editor.find_unused_sprite_data_1(), extrude_type)
            self._editor.invalidate_view_clipping()
        return _callback

    def _split_selection(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return

        where = self._editor.snapper.snap_to_grid_2d(selected.hit_position.xy)
        operations.wall_split.WallSplit(selected.map_object).split(where)

    def _join_sectors(self):
        selected = self._highlighter.select_append(
            selected_type_or_types=map_objects.EditorSector
        )
        if len(selected) == 2:
            self._do_join(selected[0].map_object, selected[1].map_object)

    def _do_join(self, sector_1: map_objects.EditorSector, sector_2: map_objects.EditorSector):
        operations.sector_join.SectorJoin(self._editor.sectors, sector_1, sector_2).join()
        self._editor.update_builder_sector(
            self._camera_collection.get_builder_position(),
            force=True
        )
        self._highlighter.clear()
    
    def _select_sprites(self):
        yield from self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=map_objects.EditorSprite
        )