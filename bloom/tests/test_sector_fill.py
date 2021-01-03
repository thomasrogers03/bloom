# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw
from . import utils


class TestSectorFill(unittest.TestCase):

    def setUp(self):
        self._sectors = utils.new_sector_collection()

    def tearDown(self):
        test_id = self.id()
        for sector_index, sector in enumerate(self._sectors.sectors):
            utils.save_sector_images(
                f'{test_id}-sector_{sector_index}',
                sector,
                self._sectors
            )

    def test_can_fill(self):
        sector = utils.build_rectangular_sector(self._sectors, -3, 3, -3, 3)
        operations.sector_insert.SectorInsert(sector, self._sectors).insert(
            [
                core.Point2(-1, -1),
                core.Point2(1, -1),
                core.Point2(1, 1),
                core.Point2(-1, 1),
            ]
        )
        operations.sector_delete.SectorDelete(
            self._sectors.sectors[1], 
            self._sectors
        ).delete()

        start_wall = utils.find_wall_on_point(sector, core.Point2(-1, -1))
        result = operations.sector_fill.SectorFill(sector, self._sectors).fill(start_wall)

        sector_2 = self._sectors.sectors[1]

        wall = utils.find_wall_on_point(sector, core.Point2(1, -1))
        expected_other_side_wall = utils.find_wall_on_point(sector_2, core.Point2(-1, -1))
        self.assertEqual(wall.other_side_wall, expected_other_side_wall)

        wall = utils.find_wall_on_point(sector, core.Point2(-1, -1))
        expected_other_side_wall = utils.find_wall_on_point(sector_2, core.Point2(-1, 1))
        self.assertEqual(wall.other_side_wall, expected_other_side_wall)

        wall = utils.find_wall_on_point(sector, core.Point2(-1, 1))
        expected_other_side_wall = utils.find_wall_on_point(sector_2, core.Point2(1, 1))
        self.assertEqual(wall.other_side_wall, expected_other_side_wall)

        wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        expected_other_side_wall = utils.find_wall_on_point(sector_2, core.Point2(1, -1))
        self.assertEqual(wall.other_side_wall, expected_other_side_wall)

        self.assertTrue(result)

    def test_no_fill_if_a_portal_exists(self):
        sector = utils.build_rectangular_sector(self._sectors, -3, 3, -3, 3)
        operations.sector_insert.SectorInsert(sector, self._sectors).insert(
            [
                core.Point2(-1, -1),
                core.Point2(1, -1),
                core.Point2(1, 1),
                core.Point2(-1, 1),
            ]
        )

        start_wall = utils.find_wall_on_point(sector, core.Point2(-1, -1))
        result = operations.sector_fill.SectorFill(sector, self._sectors).fill(start_wall)
        self.assertFalse(result)

        self.assertEqual(2, len(self._sectors.sectors))

    def test_no_fill_if_not_clockwise_wall_bunch(self):
        sector = utils.build_rectangular_sector(self._sectors, -3, 3, -3, 3)

        start_wall = utils.find_wall_on_point(sector, core.Point2(-3, -3))
        result = operations.sector_fill.SectorFill(sector, self._sectors).fill(start_wall)
        self.assertFalse(result)

        self.assertEqual(1, len(self._sectors.sectors))
