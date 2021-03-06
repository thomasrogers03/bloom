# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml
from bloom.editor import event_grouping
from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from ... import constants, map_data
from ...editor import descriptors, map_objects
from ...editor.descriptors import sector_type_descriptor
from ...editor.properties import sprite_property_view
from ...utils import gui


class TypeSelector:
    def __init__(
        self, aspect_2d: core.NodePath, on_type_changed: typing.Callable[[], None]
    ):
        self._aspect_2d = aspect_2d
        self._on_type_changed = on_type_changed

        self._frame = DirectGui.DirectFrame(
            parent=self._aspect_2d,
            frameSize=(0, 0.56, 0, 0.2),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01),
            frameColor=(0.85, 0.85, 0.85, 0.75),
            state=DirectGuiGlobals.NORMAL,
        )
        gui.bind_gui_for_focus(self._frame)
        self._frame.hide()

        self._property_parent: core.NodePath = self._aspect_2d.attach_new_node(
            "properties"
        )
        self._properties_frame = DirectGui.DirectFrame(
            parent=self._property_parent,
            frameSize=(-0.02, 1.02, 0.02, 1.32),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01),
            frameColor=(0.85, 0.85, 0.85, 0.75),
            state=DirectGuiGlobals.NORMAL,
        )
        self._properties_parent: core.NodePath = self._properties_frame.attach_new_node(
            "properties"
        )
        self._properties_parent.set_z(0.10)
        gui.bind_gui_for_focus(self._properties_frame)
        self._properties_frame.hide()
        self._properties: sprite_property_view.SpritePropertyView = None

        self._sector: map_objects.EditorSector = None
        self._current_sector_type: sector_type_descriptor.SectorTypeDescriptor = None

        self._type_lookup = {
            sector_type.name: type_index
            for type_index, sector_type in descriptors.sector_types.items()
        }
        type_names = list(self._type_lookup.keys())
        self._type_selector = DirectGui.DirectOptionMenu(
            parent=self._frame,
            pos=core.Vec3(0.05, 0.08),
            scale=constants.BIG_TEXT_SIZE,
            items=type_names,
            command=self._type_changed,
        )

        DirectGui.DirectLabel(
            parent=self._properties_frame,
            text="Special Source:",
            pos=core.Vec3(
                7 * constants.PADDING, 2 * constants.TEXT_SIZE + 2 * constants.PADDING
            ),
            scale=constants.TEXT_SIZE,
            frameColor=(0, 0, 0, 0),
        )
        self._special_source_menu = DirectGui.DirectOptionMenu(
            parent=self._properties_frame,
            pos=core.Vec3(
                7 * constants.PADDING + 0.16,
                2 * constants.TEXT_SIZE + 2 * constants.PADDING,
            ),
            items=["None", "Level Start"],
            scale=constants.TEXT_SIZE,
        )

        DirectGui.DirectLabel(
            parent=self._properties_frame,
            text="Special Target:",
            pos=core.Vec3(
                7 * constants.PADDING, constants.TEXT_SIZE + constants.PADDING
            ),
            scale=constants.TEXT_SIZE,
            frameColor=(0, 0, 0, 0),
        )
        self._special_target_menu = DirectGui.DirectOptionMenu(
            parent=self._properties_frame,
            pos=core.Vec3(7 * constants.PADDING + 0.16, constants.TEXT_SIZE)
            + constants.PADDING,
            items=["None", "Secret", "Next Level", "Secret Level"],
            scale=constants.TEXT_SIZE,
        )

        self._update_frame_position()

    def tick(self):
        self._update_frame_position()
        self._update_sector_properties()

    def show(self, sector: map_objects.EditorSector):
        self._sector = sector
        self._current_sector_type = sector.sector.sector.tags[0]
        type_name = descriptors.sector_types[self._sector.sector.sector.tags[0]].name
        self._type_selector.set(type_name)

        if (
            self._sector.target_event_grouping
            == event_grouping.EventGroupingCollection.SECRET_GROUPING
        ):
            self._special_target_menu.set("Secret")
        elif (
            self._sector.target_event_grouping
            == event_grouping.EventGroupingCollection.END_LEVEL_GROUPING
        ):
            self._special_target_menu.set("Next Level")
        elif (
            self._sector.target_event_grouping
            == event_grouping.EventGroupingCollection.SECRET_END_LEVEL_GROUPING
        ):
            self._special_target_menu.set("Secret Level")
        else:
            self._special_target_menu.set("None")

        if (
            self._sector.source_event_grouping
            == event_grouping.EventGroupingCollection.START_LEVEL_GROUPING
        ):
            self._special_source_menu.set("Level Start")
        else:
            self._special_source_menu.set("None")

        self._frame.show()
        self._properties_frame.show()

    def hide(self):
        self._clear_property_view()
        self._frame.hide()
        self._properties_frame.hide()

    def _type_changed(self, value):
        type_index = self._type_lookup[value]
        self._current_sector_type = descriptors.sector_types[type_index]
        self._update_property_view()

        if self._sector.sector.sector.tags[0] == type_index:
            return

        self._on_type_changed()

        self._sector.sector.sector.tags[0] = type_index
        markers = self._current_sector_type.marker_types

        for marker_index, marker in enumerate(markers):
            current_marker = self._sector.markers[marker_index]
            if (
                current_marker is not None
                and current_marker.sprite.sprite.tags[0] == marker
            ):
                continue

            sprite_type = descriptors.sprite_types[marker]
            category = descriptors.sprite_category_descriptors[sprite_type.category]

            data = self._sector.get_data()

            data.floor_zmotion[0] = self._sector.sector.sector.floor_z
            data.floor_zmotion[1] = data.floor_zmotion[0]

            data.ceiling_zmotion[0] = self._sector.sector.sector.ceiling_z
            data.ceiling_zmotion[1] = data.ceiling_zmotion[0]

            blood_sprite = map_data.sprite.Sprite.new()
            blood_sprite.sprite.stat.invisible = 1
            blood_sprite.sprite.tags[0] = marker
            blood_sprite.sprite.status_number = category["status_number"]
            blood_sprite.sprite.position_x = int(self._sector.walls[0].point_1.x)
            blood_sprite.sprite.position_y = int(self._sector.walls[0].point_1.y)

            self._sector.set_marker(marker_index, blood_sprite)

        marker_count = len(markers)
        remaining = len(self._sector.markers) - marker_count
        for index in range(remaining):
            offset = index + marker_count
            self._sector.markers[offset] = None

    def _update_frame_position(self):
        left = -self._inverse_aspect_ratio + 0.05
        self._frame.set_pos(left, 0, -0.95)

        right = self._inverse_aspect_ratio - 1.05
        self._property_parent.set_pos(right, 0, -0.98)

    def _update_sector_properties(self):
        if self._properties is None:
            return

        self._current_sector_type.apply_sector_type_properties(
            self._sector, self._properties.get_values()
        )

        target_special_value = self._special_target_menu.get()
        if target_special_value == "Secret":
            self._sector.set_target_event_grouping(
                event_grouping.EventGroupingCollection.SECRET_GROUPING
            )
        elif target_special_value == "Next Level":
            self._sector.set_target_event_grouping(
                event_grouping.EventGroupingCollection.END_LEVEL_GROUPING
            )
        elif target_special_value == "Secret Level":
            self._sector.set_target_event_grouping(
                event_grouping.EventGroupingCollection.SECRET_END_LEVEL_GROUPING
            )
        elif (
            self._sector.target_event_grouping is not None
            and self._sector.target_event_grouping.special_receiver_id is not None
        ):
            self._sector.set_target_event_grouping(None)

        source_special_value = self._special_source_menu.get()
        if source_special_value == "Level Start":
            self._sector.set_source_event_grouping(
                event_grouping.EventGroupingCollection.START_LEVEL_GROUPING
            )
        elif (
            self._sector.source_event_grouping is not None
            and self._sector.source_event_grouping.special_receiver_id is not None
        ):
            self._sector.set_source_event_grouping(None)

        self._sector.invalidate_geometry()

    def _update_property_view(self):
        self._clear_property_view()
        self._properties = sprite_property_view.SpritePropertyView(
            self._properties_parent,
            -1,
            self._current_sector_type.get_sector_type_properties(self._sector),
            None,
            None,
            2.35,
            1,
            1.15,
            alpha=0.5,
        )

    def _clear_property_view(self):
        if self._properties is not None:
            self._properties.destroy()
            self._properties = None

    @property
    def _inverse_aspect_ratio(self):
        return 1 / self._aspect_2d.get_sx()
