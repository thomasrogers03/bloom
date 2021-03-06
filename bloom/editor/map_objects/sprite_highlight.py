# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core


def show_highlight(display: core.NodePath, rgb_colour: core.Vec3):
    if display is not None and not display.is_empty():
        display.set_color_scale(rgb_colour.x, rgb_colour.y, rgb_colour.z, 1)


def hide_highlight(display: core.NodePath):
    if display is not None and not display.is_empty():
        display.set_color_scale(1, 1, 1, 1)
