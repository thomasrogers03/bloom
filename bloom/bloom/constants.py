# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

SCENE_3D = core.BitMask32(1)
SCENE_2D = core.BitMask32(2)
SCENE = SCENE_3D | SCENE_2D

# PORTALS_ENABLED = True
PORTALS_ENABLED = False