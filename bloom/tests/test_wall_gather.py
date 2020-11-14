# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw
from . import utils


class TestWallGather(unittest.TestCase):

    def setUp(self):
        mock_geometry_factory = mock.Mock()
        mock_suggest_sky = mock.Mock()

        map_to_load = game_map.Map()
        self._sectors = map_objects.SectorCollection(
            map_to_load,
            mock_geometry_factory,
            mock_suggest_sky
        )
        self._start_sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        operations.sector_split.SectorSplit(self._start_sector, self._sectors).split(
            [
                core.Point2(-1, 0),
                core.Point2(1, 0)
            ]
        )
        wall_to_split = utils.find_wall_on_point(self._start_sector, core.Point2(-1, 0))
        operations.wall_split.WallSplit(wall_to_split).split(core.Point2(0, 0))

    def tearDown(self):
        test_id = self.id()
        for sector_index, sector in enumerate(self._sectors.sectors):
            utils.save_sector_images(
                f'{test_id}-sector_{sector_index}', 
                sector,
                self._sectors
            )

    def test_can_grab_walls_2_sectors(self):
        self._assert_got_all_walls()

    def test_can_grab_walls_3_sectors(self):
        operations.sector_split.SectorSplit(self._start_sector, self._sectors).split(
            [
                core.Point2(0, 0),
                core.Point2(0, 1)
            ]
        )

        self._assert_got_all_walls()

    def test_can_grab_walls_4_sectors(self):
        operations.sector_split.SectorSplit(self._start_sector, self._sectors).split(
            [
                core.Point2(0, 0),
                core.Point2(0, 1)
            ]
        )
        operations.sector_split.SectorSplit(self._sectors.sectors[1], self._sectors).split(
            [
                core.Point2(0, 0),
                core.Point2(0, -1)
            ]
        )

        self._assert_got_all_walls()

    def test_can_grab_walls_5_sectors(self):
        operations.sector_split.SectorSplit(self._start_sector, self._sectors).split(
            [
                core.Point2(0, 0),
                core.Point2(0, 1)
            ]
        )
        operations.sector_split.SectorSplit(self._start_sector, self._sectors).split(
            [
                core.Point2(0, 0),
                core.Point2(-1, 1)
            ]
        )
        operations.sector_split.SectorSplit(self._sectors.sectors[1], self._sectors).split(
            [
                core.Point2(0, 0),
                core.Point2(0, -1)
            ]
        )

        self._assert_got_all_walls()

    def _assert_got_all_walls(self):
        start_wall = utils.find_wall_on_point(self._start_sector, core.Point2(0, 0))
        walls_at_point = start_wall.all_walls_at_point_1()

        for wall in walls_at_point:
            self.assertEqual(wall.point_1, start_wall.point_1)

        wall_sectors = [wall.get_sector() for wall in walls_at_point]

        for sector_index, sector in enumerate(self._sectors.sectors):
            if sector not in wall_sectors:
                raise AssertionError(f'Sector {sector_index} not found in wall gather')
