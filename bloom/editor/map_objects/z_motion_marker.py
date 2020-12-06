# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ... import editor, map_data
from . import marker


class EditorZMotionMarker(marker.EditorMarker):
    POSITION_OFF = 'off'
    POSITION_ON = 'on'

    def __init__(
        self,
        position: str,
        sector_part: str,
        sector: 'bloom.editor.map_objects.sector.EditorSector'
    ):
        super().__init__(
            map_data.sprite.Sprite.new(),
            f'z_motion_marker_{position}',
            sector
        )
        self._position = position
        self._sector_part = sector_part
        self._sector_centre = core.Point2(0, 0)

    @property
    def origin_2d(self):
        return self._sector_centre

    def setup_geometry(self, *args, **kwargs):
        if self._sector_type < 1:
            return

        self._sector_centre = core.Point2(0, 0)
        wall_count = len(self._sector.walls)
        if wall_count > 0:
            for wall in self._sector.walls:
                self._sector_centre += wall.point_1
            self._sector_centre /= wall_count

        super().setup_geometry(*args, **kwargs)

    def move_to(self, position: core.Point3):
        self.set_z(position.z)

    def set_z(self, z: float):
        if self._display is not None:
            self._display.set_pos(self.origin_2d.x, self.origin_2d.y, z)

        build_z = editor.to_build_height(z)
        if self._position == self.POSITION_OFF:
            self._z_motion[0] = build_z
        else:
            self._z_motion[1] = build_z

    @property
    def _z(self):
        if self._position == self.POSITION_OFF:
            build_z = self._z_motion[0]
        else:
            build_z = self._z_motion[1]
        return editor.to_height(build_z)

    @property
    def _z_motion(self) -> typing.List[int]:
        if self._sector_part == self._sector.FLOOR_PART:
            return self._sector_data.floor_zmotion
        return self._sector_data.ceiling_zmotion

    @property
    def _sector_type(self) -> int:
        return self._sector.sector.sector.tags[0]

    @property
    def _sector_data(self) -> map_data.sector.BloodSectorData:
        return self._sector.get_data()
