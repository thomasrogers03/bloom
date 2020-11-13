# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects


class SectorInsert:

    def __init__(self, sector_to_split: map_objects.EditorSector):
        self._sector_to_split = sector_to_split

    def split(
        self,
        points: typing.List[core.Point2]
    ):
        pass

