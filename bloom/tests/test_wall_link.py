# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw
from . import utils


class TestWallLink(unittest.TestCase):

    def setUp(self):
        mock_geometry_factory = mock.Mock()
        mock_suggest_sky = mock.Mock()

        map_to_load = game_map.Map()
        self._sectors = map_objects.SectorCollection(
            map_to_load,
            mock_geometry_factory,
            mock_suggest_sky
        )

    def tearDown(self):
        test_id = self.id()
        for sector_index, sector in enumerate(self._sectors.sectors):
            utils.save_sector_images(
                f'{test_id}-sector_{sector_index}', 
                sector,
                self._sectors
            )

    def test_can_link(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        utils.build_rectangular_sector(self._sectors, -1, 1, 1, 2)

        link_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()
