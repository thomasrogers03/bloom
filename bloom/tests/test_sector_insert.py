# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw
from . import utils


class TestSectorInsert(unittest.TestCase):

    def setUp(self):
        mock_geometry_factory = mock.Mock()
        mock_suggest_sky = mock.Mock()

        map_to_load = game_map.Map()
        self._sectors = map_objects.SectorCollection(
            map_to_load,
            mock_geometry_factory,
            mock_suggest_sky
        )

    def test_can_draw(self):
        sector = utils.build_rectangular_sector(self._sectors, -3, 3, -3, 3)
        operations.sector_insert.SectorInsert(sector).insert(
            [
                core.Point2(-1, -1),
                core.Point2(1, -1),
                core.Point2(1, 1),
                core.Point2(-1, 1),
            ]
        )

        self.assertEqual(2, len(self._sectors.sectors))
        utils.assert_wall_bunch_not_clockwise(sector, core.Point2(-3, -3))
        utils.assert_wall_bunch_clockwise(sector, core.Point2(-1, -1))

        new_sector = self._sectors.sectors[1]
        utils.assert_wall_bunch_not_clockwise(new_sector, core.Point2(-1, -1))
