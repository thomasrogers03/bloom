# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from . import utils


class TestSectorFlip(unittest.TestCase):

    def setUp(self):
        mock_audio_manager = mock.Mock()
        mock_geometry_factory = mock.Mock()
        mock_suggest_sky = mock.Mock()

        map_to_load = game_map.Map()
        self._sectors = map_objects.SectorCollection(
            map_to_load,
            mock_audio_manager,
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

    def test_can_flip_vertically(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, 0, 1)
        operations.sector_flip.SectorFlip([sector]).flip(True, False)

        utils.assert_sector_has_shape(
            sector, 
            core.Point2(-1, -1),
            core.Point2(-1, 0),
            core.Point2(1, 0),
            core.Point2(1, -1)
        )

    def test_can_flip_horizontally(self):
        sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 1)
        operations.sector_flip.SectorFlip([sector]).flip(False, True)

        utils.assert_sector_has_shape(
            sector, 
            core.Point2(-1, -1),
            core.Point2(-1, 1),
            core.Point2(0, 1),
            core.Point2(0, -1)
        )

    def test_can_flip_both(self):
        sector = utils.build_rectangular_sector(self._sectors, 0, 1, 0, 1)
        operations.sector_flip.SectorFlip([sector]).flip(True, True)

        utils.assert_sector_has_shape(
            sector, 
            core.Point2(-1, -1),
            core.Point2(-1, 0),
            core.Point2(0, 0),
            core.Point2(0, -1)
        )

    def test_can_flip_joined_sectors(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 0)
        sector_2 = utils.build_rectangular_sector(self._sectors, -1, 1, 0, 1)

        wall = utils.find_wall_on_point(sector, core.Point2(1, 0))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()
        
        operations.sector_flip.SectorFlip([sector_2, sector]).flip(True, False)

        utils.assert_sector_has_shape(
            sector, 
            core.Point2(-1, 1),
            core.Point2(-1, 0),
            core.Point2(1, 0),
            core.Point2(1, 1)
        )

        utils.assert_sector_has_shape(
            sector_2, 
            core.Point2(-1, -1),
            core.Point2(-1, 0),
            core.Point2(1, 0),
            core.Point2(1, -1)
        )

        wall = utils.find_wall_on_point(sector_2, core.Point2(1, 0))
        expected_other_side_wall = utils.find_wall_on_point(sector, core.Point2(-1, 0))
        self.assertEqual(wall.other_side_wall, expected_other_side_wall)

    def test_breaks_joined_sector_link_if_other_side_not_flipped(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 0)
        sector_2 = utils.build_rectangular_sector(self._sectors, -1, 1, 0, 1)

        wall = utils.find_wall_on_point(sector, core.Point2(1, 0))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()
        
        operations.sector_flip.SectorFlip([sector_2]).flip(True, False)

        wall = utils.find_wall_on_point(sector_2, core.Point2(1, 0))
        expected_other_side_wall = utils.find_wall_on_point(sector, core.Point2(-1, 0))
        self.assertIsNone(wall.other_side_wall)
        self.assertIsNone(expected_other_side_wall.other_side_wall)
