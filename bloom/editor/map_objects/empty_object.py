# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core


class EmptyObject:

    def get_sector(self):
        raise NotImplementedError()

    def get_geometry_part(self, part: str) -> core.NodePath:
        raise NotImplementedError()

    def get_type(self) -> int:
        raise NotImplementedError()

    def get_shade(self, part: str) -> float:
        raise NotImplementedError()

    def set_shade(self, part: str, value: float):
        raise NotImplementedError()

    def get_picnum(self, part: str) -> int:
        raise NotImplementedError()

    def set_picnum(self, part: str, picnum: int):
        raise NotImplementedError()

    def reset_panning_and_repeats(self, part: str):
        raise NotImplementedError

    def show_debug(self):
        pass

    def hide_debug(self):
        pass

    def show_highlight(self, part: str, rgb_colour: core.Vec3):
        self._get_highlighter().show_highlight(self.get_geometry_part(part), rgb_colour)

    def hide_highlight(self, part: str):
        self._get_highlighter().hide_highlight(self.get_geometry_part(part))

    def _get_highlighter(self):
        raise NotImplementedError()
