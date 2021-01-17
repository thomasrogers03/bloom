# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math

from panda3d import core

from ... import clicker, constants, dialogs
from ...editor import (event_grouping, geometry, highlighter, map_objects,
                       marker_constants, operations)
from ...editor.descriptors import constants as descriptor_constants
from ...editor.highlighting import highlight_details
from ...utils import shapes
from .. import (drawing_mode_3d, edit_mode_2d, moving_clicker,
                navigation_mode_3d)
from . import type_selector


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._type_selector = type_selector.TypeSelector(
            self._camera_collection.aspect_2d,
            self._set_new_markers
        )
        self._type_selector.hide()

        self._highlighter: highlighter.Highlighter = None
        self._sector: map_objects.EditorSector = None
        self._marker_display: core.NodePath = None
        self._moving_clicker: moving_clicker.MovingClicker = None

        self._tickers.append(self._mouse_collision_tests)
        self._tickers.append(self._update_mover)

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self._select_object
        )

        self._make_clicker(
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click=self._select_object_append,
        )

    def enter_mode(self, state):
        super().enter_mode(state)
        self.accept('k', self._cycle_move_direction)

        self.accept('1', self._set_off_z_position)
        self.accept('2', self._set_on_z_position)

        self.accept(',', self._decrease_angle)
        self.accept(',-repeat', self._decrease_angle)
        self.accept('.', self._increase_angle)
        self.accept('.-repeat', self._increase_angle)

        self._moving_clicker.setup_keyboard(self)

        self._context_menu.add_command('Set Up Door', self._setup_door)
        self._context_menu.add_command('Set Up Trap Wall', self._setup_trap_wall)

        if 'grid_visible' in state:
            if state['grid_visible']:
                self._moving_clicker.show_grid()
        else:
            self._moving_clicker.show_grid()

        self._update_markers()
        self._type_selector.show(self._sector)

    def exit_mode(self):
        state = super().exit_mode()
        state['grid_visible'] = self._moving_clicker.grid_visible

        self._clear_markers()
        self._type_selector.hide()
        self._moving_clicker.hide_grid()

        return state

    def set_sector(self, sector: map_objects.EditorSector):
        self._sector = sector

    def set_editor(self, editor):
        super().set_editor(editor)
        self._highlighter = highlighter.Highlighter(editor)
        self._highlighter.set_filter_callback(self._is_valid_highlight)
        self._highlighter.set_get_selected_colour_callback(self._get_selected_colour)
        self._sector = None

        self._moving_clicker = moving_clicker.MovingClicker(
            self._editor._scene,
            self._camera_collection,
            self._camera_collection.transform_to_camera_delta,
            self._highlighter,
            self._clicker_factory,
            self._editor.snapper,
            self._editor.sectors,
            self._editor.undo_stack,
            highlighter_filter_types=[
                map_objects.EditorSector,
                map_objects.EditorMarker,
            ],
            move_sprites_on_sectors=False
        )
        self._moving_clicker.set_updated_callback(self._update_markers)

    def tick(self):
        super().tick()
        self._type_selector.tick()

    def _setup_door(self):
        self._sector.sector.sector.tags[0] = descriptor_constants.reverse_sector_type_lookup['Z Motion']
        
        self._sector.floor_z_motion_markers[0].set_z(self._sector.floor_z)
        self._sector.floor_z_motion_markers[1].set_z(self._sector.floor_z)

        lowest_adjacent = self._sector.floor_z - constants.BIG_NUMBER
        for portal in self._sector.portal_walls():
            if portal.other_side_sector.ceiling_z > lowest_adjacent:
                lowest_adjacent = portal.other_side_sector.ceiling_z

        door_ceiling = lowest_adjacent + self._editor.snapper.grid_size
        
        self._sector.ceiling_z_motion_markers[0].set_z(self._sector.floor_z)
        self._sector.ceiling_z_motion_markers[1].set_z(door_ceiling)
        self._sector.move_ceiling_to(door_ceiling)
        
        self._update_markers()

    def _setup_trap_wall(self):
        self._sector.sector.sector.tags[0] = descriptor_constants.reverse_sector_type_lookup['Z Motion']
        
        self._sector.ceiling_z_motion_markers[0].set_z(self._sector.ceiling_z)
        self._sector.ceiling_z_motion_markers[1].set_z(self._sector.ceiling_z)

        highest_adjacent = self._sector.floor_z + constants.BIG_NUMBER
        for portal in self._sector.portal_walls():
            if portal.other_side_sector.floor_z < highest_adjacent:
                highest_adjacent = portal.other_side_sector.floor_z

        self._sector.floor_z_motion_markers[0].set_z(self._sector.ceiling_z)
        self._sector.floor_z_motion_markers[1].set_z(highest_adjacent)
        self._sector.move_floor_to(highest_adjacent)

        self._update_markers()

    def _decrease_angle(self):
        selected = self._highlighter.select(
            selected_type_or_types=[map_objects.EditorMarker]
        )

        operations.sprite_angle_update.SpriteAngleUpdate(
            selected.map_object
        ).increment(-15)
        self._update_markers()

    def _increase_angle(self):
        selected = self._highlighter.select(
            selected_type_or_types=[map_objects.EditorMarker]
        )

        operations.sprite_angle_update.SpriteAngleUpdate(
            selected.map_object).increment(15)
        self._update_markers()

    def _update_mover(self):
        if self._moving_clicker is not None:
            self._moving_clicker.tick()

    def _set_new_markers(self):
        self._update_markers()
        self._sector.invalidate_geometry()

    def _update_markers(self):
        self._clear_markers()
        if self._sector.get_type() < 1:
            return

        first_marker, second_marker = self._sector.markers
        self._marker_display = self._camera_collection.scene.attach_new_node('markers')
        self._marker_display.set_depth_test(False)

        if first_marker is not None:
            if second_marker is not None:
                self._make_slide_marker(first_marker, second_marker)
            else:
                self._make_rotate_marker(first_marker)

        first_marker, second_marker = self._sector.floor_z_motion_markers
        self._make_z_motion_marker(first_marker, second_marker,
                                   core.Vec4(0, 0.8, 1, 0.8))

        first_marker, second_marker = self._sector.ceiling_z_motion_markers
        self._make_z_motion_marker(first_marker, second_marker,
                                   core.Vec4(0.8, 0, 1, 0.8))

    def _make_rotate_marker(self, marker: map_objects.EditorMarker):
        bounding_rectangle = self._sector.get_bounding_rectangle()
        delta_x = bounding_rectangle.y - bounding_rectangle.x
        delta_y = bounding_rectangle.w - bounding_rectangle.z

        radius = 3 * min(delta_x, delta_y) / 8

        display = shapes.make_circle(
            self._marker_display,
            marker.origin,
            radius * 1.5,
            12
        )
        self._setup_display(display, colour=core.Vec4(0, 1, 0, 0.5))

        display = shapes.make_arc(
            self._marker_display,
            marker.origin,
            radius,
            marker.theta - 90,
            12
        )
        self._setup_display(display)

    def _make_slide_marker(
        self,
        first_marker: map_objects.EditorMarker,
        second_marker: map_objects.EditorMarker
    ):
        direction = second_marker.origin_2d - first_marker.origin_2d
        length = direction.length()
        theta = math.atan2(direction.y, direction.x)

        segments = core.LineSegs()
        segments.set_thickness(8)
        segments.draw_to(0, 0, 0)
        segments.draw_to(length, 0, 0)
        segments.draw_to(length - 64, 64, 0)
        segments.draw_to(length, 0, 0)
        segments.draw_to(length - 64, -64, 0)

        segments_node = segments.create('slide')
        display: core.NodePath = self._marker_display.attach_new_node(segments_node)

        display.set_pos(first_marker.origin)
        display.set_h(math.degrees(theta))
        self._setup_display(display)

    def _make_z_motion_marker(
        self,
        first_marker: map_objects.EditorMarker,
        second_marker: map_objects.EditorMarker,
        colour: core.Vec4
    ):
        length = second_marker.origin.z - first_marker.origin.z
        if length < 0:
            direction = -1
        else:
            direction = 1

        segments = core.LineSegs()
        segments.set_thickness(8)
        segments.draw_to(0, 0, 0)
        segments.draw_to(0, 0, length)
        segments.draw_to(0, 64, length - 64 * direction)
        segments.draw_to(0, 0, length)
        segments.draw_to(0, -64, length - 64 * direction)

        segments_node = segments.create('z_motion')
        display: core.NodePath = self._marker_display.attach_new_node(segments_node)

        display.set_pos(first_marker.origin)
        self._setup_display(display, colour=colour)

    @staticmethod
    def _setup_display(display: core.NodePath, colour=core.Vec4(1, 0, 0, 0.5)):
        display.set_color_scale(colour)
        display.set_transparency(True)

    def _clear_markers(self):
        if self._marker_display is not None:
            self._marker_display.remove_node()
            self._marker_display = None

    def _set_off_z_position(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorSector
        )
        if selected is None:
            return

        self._sector.invalidate_geometry()
        if selected.part == map_objects.EditorSector.FLOOR_PART:
            self._sector.floor_z_motion_markers[0].set_z(self._sector.floor_z)
        else:
            self._sector.ceiling_z_motion_markers[0].set_z(self._sector.ceiling_z)
        self._update_markers()

    def _set_on_z_position(self):
        selected = self._highlighter.select(
            selected_type_or_types=map_objects.EditorSector
        )
        if selected is None:
            return

        self._sector.invalidate_geometry()
        if selected.part == map_objects.EditorSector.FLOOR_PART:
            self._sector.floor_z_motion_markers[1].set_z(self._sector.floor_z)
        else:
            self._sector.ceiling_z_motion_markers[1].set_z(self._sector.ceiling_z)
        self._update_markers()

    def _cycle_move_direction(self):
        selected = self._highlighter.select_append(
            no_append_if_not_selected=True,
            selected_type_or_types=[map_objects.EditorWall, map_objects.EditorSprite]
        )

        for selected_object in selected:
            self._cycle_move_direction_for_object(selected_object.map_object)

    def _cycle_move_direction_for_object(self, selected_object: map_objects.EmptyObject):
        if selected_object.is_marker:
            return

        selected_object.invalidate_geometry()

        data = selected_object.get_stat_for_part(None)
        if data.poly_green:
            data.poly_blue = 0
            data.poly_green = 0
        elif data.poly_blue:
            data.poly_blue = 0
            data.poly_green = 1
        else:
            data.poly_blue = 1

    def _select_object(self):
        self._highlighter.select()

    def _select_object_append(self):
        self._highlighter.select_append()

    def _is_valid_highlight(self, highlight: highlight_details.HighlightDetails):
        return highlight.map_object.get_sector() == self._sector

    def _get_selected_colour(self, selected: highlight_details.HighlightDetails):
        if isinstance(selected.map_object, map_objects.EditorSprite) or \
                isinstance(selected.map_object, map_objects.EditorWall):
            stat = selected.map_object.get_stat_for_part(None)
            if stat.poly_blue:
                return core.Vec4(0, 0, 1, 1)
            elif stat.poly_green:
                return core.Vec4(0, 1, 0, 1)

        return core.Vec4(1, 1, 1, 1)

    def _mouse_collision_tests(self):
        with self._edit_mode_selector.track_performance_stats('mouse_collision_tests'):
            highlight_finder = self._make_highlight_finder_callback()
            self._highlighter.update(highlight_finder)
            self._highlighter.update_displays(self._editor.ticks)
