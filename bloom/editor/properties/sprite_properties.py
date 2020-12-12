# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml
from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from ... import constants, edit_mode, tile_dialog
from ...audio import sound_view
from ...tiles import manager
from ...utils import gui
from .. import descriptors, event_grouping, map_objects
from ..descriptors import sprite_type_descriptor
from . import sprite_property_view, sprite_type_list

_SPRITE_CATEGORIES_TYPE = typing.Dict[str, typing.List[sprite_type_descriptor.SpriteTypeDescriptor]]

class SpriteDialog:
    _TILE_FRAME_SIZE = 0.3
    _TILE_FRAME_SIZE_INNER = _TILE_FRAME_SIZE - 0.02

    def __init__(
        self,
        parent: core.NodePath,
        edit_mode: edit_mode.EditMode,
        task_manager: Task.TaskManager,
        sound_browser: sound_view.SoundView,
        tile_viewer: tile_dialog.TileDialog
    ):
        self._task_manager = task_manager

        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            pos=core.Vec3(-1.1, -0.9),
            frameSize=(0, 2.2, 0, 1.8),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01)
        )
        self._dialog.hide()

        self._tile_section = DirectGui.DirectFrame(
            parent=self._dialog,
            pos=core.Vec3(0.65, 0.07),
            frameColor=(0, 0, 0, 0)
        )

        current_tile_frame_parent = DirectGui.DirectFrame(
            parent=self._tile_section,
            pos=core.Vec3(0, constants.TEXT_SIZE),
            frameSize=(0, self._TILE_FRAME_SIZE, 0, self._TILE_FRAME_SIZE),
            frameColor=(0.65, 0.65, 0.65, 1),
            relief=DirectGuiGlobals.SUNKEN,
            borderWidth=(0.01, 0.01)
        )
        self._current_tile_frame = DirectGui.DirectButton(
            pos=core.Vec3(0.01, 0.01),
            parent=current_tile_frame_parent,
            frameSize=(0, self._TILE_FRAME_SIZE, self._TILE_FRAME_SIZE, 0),
            relief=DirectGuiGlobals.FLAT,
            command=self._show_tiles
        )
        self._current_tile_frame.set_transparency(True)
        self._change_tile_button = DirectGui.DirectButton(
            parent=self._tile_section,
            scale=constants.TEXT_SIZE,
            text='Change Tile',
            text_align=core.TextNode.A_left,
            command=self._show_tiles
        )

        self._property_parent: core.NodePath = self._dialog.attach_new_node('properties')
        self._property_parent.set_pos(0.66, 0, 0.38)

        self._sound_browser = sound_browser
        self._tile_viewer = tile_viewer
        self._edit_mode = edit_mode

        self._sprite: map_objects.EditorSprite = None
        self._selected_descriptor: sprite_type_descriptor.SpriteTypeDescriptor = None
        self._current_descriptor: sprite_type_descriptor.SpriteTypeDescriptor = None
        self._current_picnum: int = None
        self._current_palette: int = None
        self._current_status_number: int = None

        category_names = descriptors.sprite_category_descriptors.keys()
        category_names = sorted(category_names)
        category_names = list(category_names)
        self._sprite_categories: _SPRITE_CATEGORIES_TYPE = {
            category_name: []
            for category_name in category_names
        }
        for descriptor in descriptors.sprite_types.values():
            self._sprite_categories[descriptor.category].append(descriptor)

        self._sprite_category_options = DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(0.04, 1.72),
            items=category_names,
            command=self._select_sprite_category,
            scale=constants.TEXT_SIZE,
            text_align=core.TextNode.A_left
        )
        self._sprite_type_list = sprite_type_list.SpriteTypeList(
            self._dialog,
            self._tile_viewer.tile_manager,
            self._select_sprite_type
        )
        self._properties: sprite_property_view.SpritePropertyView = None

        DirectGui.DirectLabel(
            parent=self._dialog,
            text='Special Source:',
            pos=core.Vec3(1.74, 0.38),
            scale=constants.TEXT_SIZE
        )
        self._special_source_menu = DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(1.90, 0.38),
            items=['None', 'Level Start'],
            scale=constants.TEXT_SIZE
        )

        DirectGui.DirectLabel(
            parent=self._dialog,
            text='Special Target:',
            pos=core.Vec3(1.74, 0.38 - constants.TEXT_SIZE - 0.02),
            scale=constants.TEXT_SIZE
        )
        self._special_target_menu = DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(1.90, 0.38 - constants.TEXT_SIZE - 0.02),
            items=['None', 'Next Level', 'Secret Level'],
            scale=constants.TEXT_SIZE
        )

        DirectGui.DirectButton(
            parent=self._dialog,
            pos=core.Vec3(1.98, 0.07),
            text='Ok',
            scale=constants.TEXT_SIZE,
            command=self._save_changes
        )
        DirectGui.DirectButton(
            parent=self._dialog,
            pos=core.Vec3(2.1, 0.07),
            text='Cancel',
            scale=constants.TEXT_SIZE,
            command=self._hide
        )

    def show(self, sprite: map_objects.EditorSprite):
        self._sprite = sprite
        self._current_descriptor = descriptors.sprite_types[self._sprite.get_type()]

        self._sprite_category_options.set(self._current_descriptor.category)
        self._current_palette = self._sprite.sprite.sprite.palette
        self._update_sprite_tile(
            sprite.get_picnum(map_objects.EditorSprite.PART_NAME),
        )
        self._update_available_tiles()

        if self._sprite.target_event_grouping == event_grouping.EventGroupingCollection.END_LEVEL_GROUPING:
            self._special_target_menu.set('Next Level')
        elif self._sprite.target_event_grouping == event_grouping.EventGroupingCollection.SECRET_END_LEVEL_GROUPING:
            self._special_target_menu.set('Secret Level')
        else:
            self._special_target_menu.set('None')

        if self._sprite.source_event_grouping == event_grouping.EventGroupingCollection.START_LEVEL_GROUPING:
            self._special_source_menu.set('Next Level')
        else:
            self._special_source_menu.set('None')

        self._update_property_view()
        self._edit_mode.push_mode(self)

    def _save_changes(self):
        new_values = self._properties.get_values()

        new_picnum = self._properties.get_current_tile()
        if new_picnum is not None:
            self._current_picnum = new_picnum

        self._current_descriptor.apply_sprite_properties(self._sprite, new_values)
        self.apply_sprite_properties(
            self._sprite, 
            self._current_descriptor, 
            self._current_picnum,
            self._get_current_palette()
        )

        target_special_value = self._special_target_menu.get()
        if target_special_value == 'Next Level':
            self._sprite.set_target_event_grouping(event_grouping.EventGroupingCollection.END_LEVEL_GROUPING)
        elif target_special_value == 'Secret Level':
            self._sprite.set_target_event_grouping(event_grouping.EventGroupingCollection.SECRET_END_LEVEL_GROUPING)
        elif self._sprite.target_event_grouping is not None and \
                self._sprite.target_event_grouping.special_receiver_id is not None:
            self._sprite.set_target_event_grouping(None)

        source_special_value = self._special_source_menu.get()
        if source_special_value == 'Level Start':
            self._sprite.set_source_event_grouping(event_grouping.EventGroupingCollection.START_LEVEL_GROUPING)
        elif self._sprite.source_event_grouping is not None and \
                self._sprite.source_event_grouping.special_receiver_id is not None:
            self._sprite.set_source_event_grouping(None)

        self._sprite.invalidate_geometry()
        self._sprite.update_ambient_sound()
        self._hide()

    @staticmethod
    def apply_sprite_properties(
        sprite: map_objects.EditorSprite, 
        descriptor: sprite_type_descriptor.SpriteTypeDescriptor,
        picnum: int,
        palette: int
    ):
        sprite.sprite.sprite.tags[0] = descriptor.sprite_type
        sprite.sprite.sprite.picnum = picnum
        sprite.sprite.sprite.palette = palette
        sprite.sprite.sprite.status_number = descriptor.get_status_number(
            descriptors.sprite_category_descriptors
        )
        sprite.sprite.sprite.stat.invisible = int(descriptor.invisible)

        sprite.sprite.sprite.stat.blocking = 0
        sprite.sprite.sprite.stat.blocking2 = 0
        if descriptor.blocking == 1:
            sprite.sprite.sprite.stat.blocking = 1
        elif descriptor.blocking == 2:
            sprite.sprite.sprite.stat.blocking2 = 1

        repeats = descriptor.sprite_repeats
        if repeats is not None:
            sprite.set_repeats(repeats['x'], repeats['y'])

    def _clear_property_view(self):
        if self._properties is not None:
            self._properties.destroy()
            self._properties = None

    def _update_property_view(self):
        self._clear_property_view()
        self._properties = sprite_property_view.SpritePropertyView(
            self._property_parent,
            self._current_descriptor.default_tile,
            self._current_descriptor.get_sprite_properties(self._sprite),
            self._sound_browser,
            self._update_sprite_tile,
            1.5,
            1.5,
            1.25
        )

    def _select_sprite_category(self, value: str):
        self._sprite_type_list.clear()
        for descriptor in self._sprite_categories[value]:
            self._sprite_type_list.add_sprite_type(descriptor)
        self._sprite_type_list.set_current_type(self._current_descriptor)

    def _select_sprite_type(self, descriptor: sprite_type_descriptor.SpriteTypeDescriptor):
        if self._selected_descriptor == descriptor:
            self._save_changes()
            return

        self._selected_descriptor = descriptor
        self._task_manager.do_method_later(
            constants.DOUBLE_CLICK_TIMEOUT,
            self._reset_selected_sprite_type,
            'reset_double_click_sprite_type'
        )

        if self._current_descriptor != self._selected_descriptor:
            self._current_descriptor = descriptor
            self._current_palette = self._get_current_palette()
            self._update_sprite_tile(descriptor.default_tile)
            self._update_available_tiles()
            self._update_property_view()

    def _reset_selected_sprite_type(self, task):
        self._selected_descriptor = None
        return task.done

    def _get_current_palette(self):
        if self._current_descriptor.palette is not None:
            return self._current_descriptor.palette
        return self._current_palette

    def _update_available_tiles(self):
        valid_tiles = self._current_descriptor.valid_tiles
        if valid_tiles is None or len(valid_tiles) > 1:
            self._tile_viewer.load_tiles(self._current_descriptor.valid_tiles)
            self._change_tile_button.show()
        else:
            self._change_tile_button.hide()

    def enter_mode(self, state: dict):
        self._dialog.show()

    def exit_mode(self):
        self._dialog.hide()
        return {}

    def _hide(self):
        self._edit_mode.pop_mode()

    def tick(self):
        pass

    def _show_tiles(self):
        self._tile_viewer.show(self._current_picnum, self._update_sprite_tile)

    def _update_sprite_tile(self, picnum: int):
        self._current_picnum = picnum

        texture = self._tile_viewer.tile_manager.get_tile(
            self._current_picnum,
            self._current_palette
        )

        frame_size = gui.size_inside_square_for_texture(
            texture,
            self._TILE_FRAME_SIZE_INNER
        )

        if frame_size is None:
            self._current_tile_frame['frameTexture'] = None
            return

        half_width_left = (self._TILE_FRAME_SIZE_INNER - frame_size.x) / 2
        half_height_left = (self._TILE_FRAME_SIZE_INNER - frame_size.y) / 2

        self._current_tile_frame['frameSize'] = (
            half_width_left,
            self._TILE_FRAME_SIZE_INNER - half_width_left,
            self._TILE_FRAME_SIZE_INNER - half_height_left,
            half_height_left,
        )
        self._current_tile_frame['frameTexture'] = texture
