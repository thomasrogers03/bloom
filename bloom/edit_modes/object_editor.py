# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import typing

from direct.showbase import DirectObject
from panda3d import core

from .. import cameras, dialogs, edit_menu, edit_mode, editor, map_data
from .. import menu as context_menu
from ..editor import highlighter, map_editor, map_objects, operations
from ..editor.descriptors import constants as descriptor_constants
from ..editor.descriptors import sprite_type_descriptor
from ..editor.highlighting import highlight_details
from ..editor.properties import sprite_properties
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

    def setup_commands(self, event_handler: DirectObject.DirectObject, menu: context_menu.Menu):
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
            command=self._move_selected_to_ceiling
        )
        self._menu.add_command(
            label="Move sprite to floor (end)",
            command=self._move_selected_to_floor
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

        event_handler.accept('home', self._move_selected_to_ceiling)
        event_handler.accept('end', self._move_selected_to_floor)

        event_handler.accept('control-page_up', self._move_sector_up)
        event_handler.accept('control-page_up-repeat', self._move_sector_up)
        event_handler.accept('control-page_down', self._move_sector_down)
        event_handler.accept('control-page_down-repeat', self._move_sector_down)

        event_handler.accept('page_up', self._move_sector_part_up)
        event_handler.accept('page_up-repeat', self._move_sector_part_up)
        event_handler.accept('page_down', self._move_sector_part_down)
        event_handler.accept('page_down-repeat', self._move_sector_part_down)

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
        event_handler.accept('m', self._toggle_wall_middle)

        event_handler.accept('-', self._decrease_shade)
        event_handler.accept('--repeat', self._decrease_shade)
        event_handler.accept('=', self._increase_shade)
        event_handler.accept('=-repeat', self._increase_shade)

        self._setup_context_menu(menu)

    def set_copy_sprite(self, sprite: map_objects.EditorSprite):
        self._copy_sprite = sprite

    def _setup_context_menu(self, menu: context_menu.Menu):
        self._setup_wall_context_menu(menu.add_sub_menu('Edit'))
        self._setup_sprite_context_menu(menu.add_sub_menu('Add Sprite'))
        menu.add_command('Fill out sector behind wall', self._fill_wall_sector)

    def _setup_wall_context_menu(self, menu: context_menu.Menu):
        menu.add_command('Extrude', self._extrude_selection)

    def _setup_sprite_context_menu(self, menu: context_menu.Menu):
        category_menus = {}
        for category in descriptor_constants.sprite_category_descriptors.keys():
            category_menus[category] = menu.add_sub_menu(category)
        for sprite_type, sprite_descriptor in descriptor_constants.sprite_types.items():
            category_menus[sprite_descriptor.category].add_command(
                sprite_descriptor.name,
                self._add_sprite_from_context_menu_callback(
                    sprite_type,
                    sprite_descriptor
                )
            )

    def _fill_wall_sector(self):
        selected = self._highlighter.select(selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return

        result = operations.sector_fill.SectorFill(
            selected.map_object.get_sector(), 
            self._editor.sectors
        ).fill(selected.map_object)

        if result:
            self._camera_collection.set_info_text('Filled out sector')

    def _edit_object_properties(self):
        selected = self._highlighter.select()
        if selected is None:
            return

        if isinstance(selected.map_object, map_objects.sprite.EditorSprite):
            self._dialogs.sprite_properties.show(selected.map_object)
        elif isinstance(selected.map_object, map_objects.EditorSector):
            self._property_editor.set_sector(selected.map_object)
            self._edit_mode_selector.push_mode(self._property_editor)
        elif isinstance(selected.map_object, map_objects.EditorWall):
            self._dialogs.wall_properties.show(selected.map_object)

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
                operations.sprite_facing.SpriteFacing(
                    selected_item.map_object).change_facing()
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
            operations.flip.Flip(
                self._editor.undo_stack, 
                selected_item.map_object, 
                selected_item.part
            ).flip()

    def _bind_objects(self):
        selected = self._highlighter.select_append()
        if len(selected) < 2:
            return

        transmitter = selected[-1]
        receivers = selected[:-1]

        selected_objects = [item.map_object for item in receivers]
        grouping = self._editor.sectors.event_groupings.get_grouping(
            transmitter.map_object,
            selected_objects
        )
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

            stat = selected_item.map_object.get_stat_for_part(selected_item.part)
            self._camera_collection.set_info_text(
                f'Blocking: {stat.blocking}, Blocking 2: {stat.blocking2}')

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
            operations.increment_sector_heinum.IncrementSectorHeinum(
                selected_item.map_object,
                selected_item.part
            ).increment(amount)

        if len(selected) > 0:
            first_selected = selected[0]
            heinum = first_selected.map_object.get_heinum(first_selected.part)
            build_heinum = editor.to_build_heinum(heinum)
            self._camera_collection.set_info_text(f'Heinum: {build_heinum}')

    def _set_sector_first_wall(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorWall
        )
        if selected is None:
            return

        selected.map_object.get_sector().set_first_wall(selected.map_object)

    def _swap_lower_texture(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorWall)
        if selected is None:
            return

        operations.swap_wall_bottom.SwapWallBottom(selected.map_object).toggle()

    def _toggle_wall_peg(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorWall
        )
        if selected is None:
            return

        operations.swap_wall_peg.SwapWallPeg(
            selected.map_object, selected.part
        ).toggle()

    def _toggle_wall_middle(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorWall
        )
        if selected is None:
            return

        operations.toggle_wall_middle.ToggleWallMiddle(
            selected.map_object, selected.part
        ).toggle()

    def _decrease_angle(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[map_objects.EditorSector, map_objects.EditorSprite]
        )

        for selected_item in selected:
            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                operations.sprite_angle_update.SpriteAngleUpdate(
                    selected_item.map_object).increment(-15)
            elif isinstance(selected_item.map_object, map_objects.EditorSector):
                operations.sector_rotate.SectorRotate(
                    selected_item.map_object).rotate(-15)

    def _increase_angle(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[map_objects.EditorSector, map_objects.EditorSprite]
        )

        for selected_item in selected:
            if isinstance(selected_item.map_object, map_objects.EditorSprite):
                operations.sprite_angle_update.SpriteAngleUpdate(
                    selected_item.map_object).increment(15)
            elif isinstance(selected_item.map_object, map_objects.EditorSector):
                operations.sector_rotate.SectorRotate(
                    selected_item.map_object).rotate(15)

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

    def _add_sprite_from_context_menu_callback(
        self,
        sprite_type: int,
        descriptor: sprite_type_descriptor.SpriteTypeDescriptor
    ):
        def _callback():
            selected = self._highlighter.select()
            if selected is None:
                return

            blood_sprite = map_data.sprite.Sprite.new()
            sprite = selected.map_object.add_sprite(blood_sprite)
            sprite_properties.SpriteDialog.apply_sprite_properties(
                sprite,
                descriptor,
                descriptor.default_tile,
                descriptor.palette
            )

            hit_position = self._editor.snapper.snap_to_grid_3d(selected.hit_position)
            sprite.move_to(hit_position)
        return _callback

    def _add_sprite(self, sprite_type=None):
        selected = self._highlighter.select(
            selected_type_or_types=[map_objects.EditorSector, map_objects.EditorWall]
        )
        if selected is None:
            return

        sprite = self._add_sprite_to_sector(selected)
        if selected.is_floor:
            self._move_sprite_to_floor(sprite)
        elif selected.is_ceiling:
            self._move_sprite_to_ceiling(sprite)
        elif selected.is_wall:
            offset = selected.map_object.get_normal_3d() * 8
            sprite.move_to(sprite.position - offset)
            sprite.get_stat_for_part(None).facing = 1
            theta = selected.map_object.line_segment.get_direction_theta()
            sprite.set_theta(theta + 180)
            sprite.invalidate_geometry()

    def _add_sprite_to_sector(self, selected: highlight_details.HighlightDetails):
        sector = selected.get_sector()
        hit_position = self._editor.snapper.snap_to_grid_3d(selected.hit_position)
        if self._copy_sprite is None:
            return sector.add_new_sprite(hit_position)
        else:
            blood_sprite = self._copy_sprite.sprite.copy()
            sprite = sector.add_sprite(blood_sprite)
            sprite.set_source_event_grouping(self._copy_sprite.source_event_grouping)
            sprite.move_to(hit_position)
            return sprite

    def _move_selected_to_floor(self):
        for selected_item in self._select_sprites_or_sectors():
            if selected_item.is_sprite:
                self._move_sprite_to_floor(selected_item.map_object)
            else:
                operations.sector_move_to_adjacent.SectorMoveToAdjacent(
                    selected_item.map_object, selected_item.part
                ).move(False)

    def _move_sprite_to_floor(self, sprite: map_objects.EditorSprite):
        editor_sector = sprite.get_sector()
        new_z = editor_sector.floor_z_at_point(sprite.origin_2d)
        sprite.set_z_at_bottom(new_z)

    def _move_selected_to_ceiling(self):
        for selected_item in self._select_sprites_or_sectors():
            if selected_item.is_sprite:
                self._move_sprite_to_ceiling(selected_item.map_object)
            else:
                operations.sector_move_to_adjacent.SectorMoveToAdjacent(
                    selected_item.map_object, selected_item.part
                ).move(True)

    def _move_sprite_to_ceiling(self, sprite: map_objects.EditorSprite):
        editor_sector = sprite.get_sector()
        new_z = editor_sector.ceiling_z_at_point(sprite.origin_2d)
        sprite.set_z_at_top(new_z)

    def _move_sector_up(self):
        self._move_sector(-1)

    def _move_sector_down(self):
        self._move_sector(1)

    def _move_sector(self, direction: float):
        selected = self._highlighter.select_append()

        sectors: typing.Set[map_objects.EditorSector] = set()
        for selected_object in selected:
            if isinstance(selected_object.map_object, map_objects.EditorSector):
                sectors.add(selected_object.map_object)

        amount = direction * self._editor.snapper.grid_size
        delta = core.Vec3(0, 0, amount)
        for sector in sectors:
            sector.move_floor_to(sector.floor_z + amount)
            sector.move_ceiling_to(sector.ceiling_z + amount)

            for marker in sector.floor_z_motion_markers:
                marker.move_to(marker.origin + delta)

            for marker in sector.ceiling_z_motion_markers:
                marker.move_to(marker.origin + delta)

            for sprite in sector.sprites:
                sprite.move_to(sprite.origin + delta)

    def _move_sector_part_up(self):
        self._move_sector_part(-1)

    def _move_sector_part_down(self):
        self._move_sector_part(1)

    def _move_sector_part(self, direction: float):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=map_objects.EditorSector
        )

        amount = direction * self._editor.snapper.grid_size
        delta = core.Vec3(0, 0, amount)
        for selected_object in selected:
            sector = selected_object.map_object
            if selected_object.part == map_objects.EditorSector.FLOOR_PART:
                sector.move_floor_to(sector.floor_z + amount)

                for marker in sector.floor_z_motion_markers:
                    marker.move_to(marker.origin + delta)
            else:
                sector.move_ceiling_to(sector.ceiling_z + amount)

                for marker in sector.ceiling_z_motion_markers:
                    marker.move_to(marker.origin + delta)

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
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorWall)
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
        operations.sector_join.SectorJoin(
            self._editor.sectors, sector_1, sector_2).join()
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

    def _select_sprites_or_sectors(self):
        yield from self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[
                map_objects.EditorSprite,
                map_objects.EditorSector,
            ]
        )
