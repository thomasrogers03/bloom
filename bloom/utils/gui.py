# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGuiBase
from panda3d import core

from .. import constants


def bind_scroll(
    control: DirectGuiBase.DirectGuiBase, 
    scroll_up: typing.Callable[[typing.Any], None], 
    scroll_down: typing.Callable[[typing.Any], None]
):
    control.bind(constants.DIRECT_GUI_WHEELUP, scroll_up)
    control.bind(constants.DIRECT_GUI_WHEELDOWN, scroll_down)

def size_inside_square_for_texture(texture: core.Texture, square_size: float):
    width = texture.get_x_size()
    height = texture.get_y_size()
    if width < 1 or height < 1:
        return None

    if width > height:
        frame_height = (height / width) * square_size
        frame_width = square_size
    else:
        frame_height = square_size
        frame_width = (width / height) * square_size

    return core.Vec2(frame_width, frame_height)
