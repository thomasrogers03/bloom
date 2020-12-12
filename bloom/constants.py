# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from os import environ

from panda3d import core


def env(name, default):
    return environ.get(name, default)


def _create_vertex_format():
    vertex_array_format = core.GeomVertexArrayFormat()
    vertex_array_format.add_column(
        'vertex',
        3,
        core.Geom.NT_float32,
        core.Geom.C_point
    )
    vertex_array_format.add_column(
        'color',
        4,
        core.Geom.NT_float32,
        core.Geom.C_color
    )
    vertex_array_format.add_column(
        'texcoord',
        2,
        core.Geom.NT_float32,
        core.Geom.C_texcoord
    )

    vertex_format = core.GeomVertexFormat()
    vertex_format.add_array(vertex_array_format)

    return core.GeomVertexFormat.register_format(vertex_format)


DEBUG = env('DEBUG', 'false').lower() == 'true'

SCENE_3D = core.BitMask32(1)
SCENE_2D = core.BitMask32(2)
SCENE = SCENE_3D | SCENE_2D

PORTALS_ENABLED = env('PORTALS_ENABLED', 'true').lower() == 'true'
PORTALS_DEBUGGING_ENABLED = DEBUG or env('PORTAL_DEBUG', 'false').lower() == 'true'
PORTAL_DEBUG_DEPTH = int(env('PORTAL_DEBUG_DEPTH', '0'))

# MAP_CACHE_ENABLED = True
MAP_CACHE_ENABLED = False

CACHE_PATH = 'cache'

DOUBLE_CLICK_TIMEOUT = 0.25

TICK_RATE = 1 / 35.0
TICK_SCALE = 10240

VERTEX_FORMAT = _create_vertex_format()

HIGHLIGHT_DEPTH_OFFSET = 2
DEPTH_OFFSET = 10

REALLY_BIG_NUMBER = 1 << 17
BIG_NUMBER = 1 << 16

BACK_MOST = -1000
FRONT_MOST = 1000

DIRECT_GUI_WHEELUP = core.PGButton.get_release_prefix() + core.MouseButton.wheel_up().get_name() + '-'
DIRECT_GUI_WHEELDOWN = core.PGButton.get_release_prefix() + core.MouseButton.wheel_down().get_name() + '-'

TEXT_SIZE = 0.04
LARGE_TEXT_SIZE = 0.05
BIG_TEXT_SIZE = 0.06
HUGE_TEXT_SIZE = 0.08
PADDING = 0.02

SCENE_SCALE = 1 / 100

MAP_EXTENSION_SKIP = -len('.MAP')

GUI_HAS_FOCUS = 'gui_has_focus'
GUI_LOST_FOCUS = 'gui_lost_focus'
