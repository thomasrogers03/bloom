# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

SCENE_3D = core.BitMask32(1)
SCENE_2D = core.BitMask32(2)
SCENE = SCENE_3D | SCENE_2D

# PORTALS_ENABLED = True
PORTALS_ENABLED = False

# MAP_CACHE_ENABLED = True
MAP_CACHE_ENABLED = False

CACHE_PATH = 'cache'

DOUBLE_CLICK_TIMEOUT = 0.25

TICK_RATE = 1 / 35.0
TICK_SCALE = 10240

