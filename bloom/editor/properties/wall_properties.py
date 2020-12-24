# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml
from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from ... import constants, edit_mode
from ...tiles import manager
from ...utils import gui
from .. import descriptors, event_grouping, map_objects
from ..descriptors import wall_type_descriptor
from . import sprite_property_view

_WALL_CATEGORIES_TYPE = typing.Dict[str, typing.List[wall_type_descriptor.WallTypeDescriptor]]

class WallDialog:

    def __init__(
        self,
        parent: core.NodePath,
        edit_mode: edit_mode.EditMode
    ):
        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            pos=core.Vec3(-0.78, -0.9),
            frameSize=(0, 1.58, 0, 1.8),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01)
        )
        self._dialog.hide()

        self._property_parent: core.NodePath = self._dialog.attach_new_node('properties')
        self._property_parent.set_pos(0.04, 0, 0.38)

        self._edit_mode = edit_mode

        self._wall: map_objects.EditorWall = None
        self._selected_descriptor: wall_type_descriptor.WallTypeDescriptor = None
        self._current_descriptor: wall_type_descriptor.WallTypeDescriptor = None
        self._current_picnum: int = None
        self._current_palette: int = None
        self._current_status_number: int = None

        self._properties: sprite_property_view.SpritePropertyView = None

        self._type_lookup = {
            wall_type.name: type_index
            for type_index, wall_type in descriptors.wall_types.items()
        }
        type_names = list(self._type_lookup.keys())
        self._type_selector = DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(0.05, 0.38),
            scale=constants.TEXT_SIZE,
            items=type_names,
            command=self._type_changed
        )

        DirectGui.DirectLabel(
            parent=self._dialog,
            text='Special Source:',
            pos=core.Vec3(1.12, 0.38),
            scale=constants.TEXT_SIZE
        )
        self._special_source_menu = DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(1.28, 0.38),
            items=['None', 'Level Start'],
            scale=constants.TEXT_SIZE
        )

        DirectGui.DirectLabel(
            parent=self._dialog,
            text='Special Target:',
            pos=core.Vec3(1.12, 0.38 - constants.TEXT_SIZE - 0.02),
            scale=constants.TEXT_SIZE
        )
        self._special_target_menu = DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(1.28, 0.38 - constants.TEXT_SIZE - 0.02),
            items=['None', 'Next Level', 'Secret Level'],
            scale=constants.TEXT_SIZE
        )

        DirectGui.DirectButton(
            parent=self._dialog,
            pos=core.Vec3(1.36, 0.07),
            text='Ok',
            scale=constants.TEXT_SIZE,
            command=self._save_changes
        )
        DirectGui.DirectButton(
            parent=self._dialog,
            pos=core.Vec3(1.48, 0.07),
            text='Cancel',
            scale=constants.TEXT_SIZE,
            command=self._hide
        )

    def show(self, wall: map_objects.EditorWall):
        self._wall = wall
        self._current_descriptor = descriptors.wall_types[self._wall.get_type()]

        if self._wall.target_event_grouping == event_grouping.EventGroupingCollection.END_LEVEL_GROUPING:
            self._special_target_menu.set('Next Level')
        elif self._wall.target_event_grouping == event_grouping.EventGroupingCollection.SECRET_END_LEVEL_GROUPING:
            self._special_target_menu.set('Secret Level')
        else:
            self._special_target_menu.set('None')

        if self._wall.source_event_grouping == event_grouping.EventGroupingCollection.START_LEVEL_GROUPING:
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

        self._current_descriptor.apply_wall_properties(self._wall, new_values)
        self._wall.blood_wall.wall.tags[0] = self._current_descriptor.wall_type

        target_special_value = self._special_target_menu.get()
        if target_special_value == 'Next Level':
            self._wall.set_target_event_grouping(event_grouping.EventGroupingCollection.END_LEVEL_GROUPING)
        elif target_special_value == 'Secret Level':
            self._wall.set_target_event_grouping(event_grouping.EventGroupingCollection.SECRET_END_LEVEL_GROUPING)
        elif self._wall.target_event_grouping is not None and \
                self._wall.target_event_grouping.special_receiver_id is not None:
            self._wall.set_target_event_grouping(None)

        source_special_value = self._special_source_menu.get()
        if source_special_value == 'Level Start':
            self._wall.set_source_event_grouping(event_grouping.EventGroupingCollection.START_LEVEL_GROUPING)
        elif self._wall.source_event_grouping is not None and \
                self._wall.source_event_grouping.special_receiver_id is not None:
            self._wall.set_source_event_grouping(None)

        self._hide()

    def _clear_property_view(self):
        if self._properties is not None:
            self._properties.destroy()
            self._properties = None

    def _update_property_view(self):
        self._clear_property_view()
        self._properties = sprite_property_view.SpritePropertyView(
            self._property_parent,
            -1,
            self._current_descriptor.get_wall_properties(self._wall),
            None,
            None,
            1.5,
            1.5,
            1.25
        )
        
    def _type_changed(self, value):
        type_index = self._type_lookup[value]
        self._update_property_view()

        if self._wall.blood_wall.wall.tags[0] == type_index:
            return

        self._wall.blood_wall.wall.tags[0] = type_index

    def _reset_selected_wall_type(self, task):
        self._selected_descriptor = None
        return task.done

    def _get_current_palette(self):
        if self._current_descriptor.palette is not None:
            return self._current_descriptor.palette
        return self._current_palette

    def enter_mode(self, state: dict):
        self._dialog.show()

    def exit_mode(self):
        self._dialog.hide()
        return {}

    def _hide(self):
        self._edit_mode.pop_mode()

    def tick(self):
        pass
