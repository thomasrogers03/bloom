# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math

from panda3d import core

from .. import constants


class MoveDebug:

    def __init__(self, scene: core.NodePath):
        self._scene = scene
        self._debug: core.NodePath = None

    def update_move_debug_2d_offset(self, start_position: core.Point2, offset: core.Vec2, height: float):
        self.update_move_debug_2d(start_position, start_position + offset, height)

    def update_move_debug_2d(self, start_position: core.Point2, new_position: core.Point2, height: float):
        start = core.Point3(start_position.x, start_position.y, height)
        end = core.Point3(new_position.x, new_position.y, height)
        self.update_move_debug(start, end)
    
    def update_move_debug(self, start_position: core.Point3, new_position: core.Point3):
        self.clear_debug()
        self._debug = self._scene.attach_new_node('debug')
        self._debug.set_depth_write(False)
        self._debug.set_depth_test(False)
        self._debug.set_bin('fixed', constants.FRONT_MOST)

        direction = new_position - start_position
        half_direction = direction / 2
        self._debug.set_pos(start_position + half_direction)

        debug_segments = core.LineSegs('debug_line')
        debug_segments.set_thickness(4)
        debug_segments.set_color(0, 1, 1, 0.85)
        debug_segments.draw_to(-half_direction)
        debug_segments.draw_to(half_direction)

        self._debug.attach_new_node(debug_segments.create())

        debug_text_node = core.TextNode('debug_text')
        theta = math.atan2(direction.y, direction.x)
        theta = math.degrees(theta)
        text = f'Angle: {theta}\n'
        text += f'Delta: {direction}'
        debug_text_node.set_text(text)
        debug_text_node.set_align(core.TextNode.A_center)

        debug_text: core.NodePath = self._debug.attach_new_node(debug_text_node)
        debug_text.set_billboard_axis()
        debug_text.set_scale(-96)

    def clear_debug(self):
        if self._debug is not None:
            self._debug.remove_node()
            self._debug = None
