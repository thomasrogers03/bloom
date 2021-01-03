# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from . import utils


class TestWallJoin(unittest.TestCase):

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

    def test_completely_overlapping(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 1)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()
        
        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 1))
        self.assertEqual(wall.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall)

    def test_first_within_second(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -2, 2)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 2))
        self.assertEqual(other_side_wall.point_2, core.Point2(0, 1))

        other_side_wall_2 = other_side_wall.wall_point_2
        self.assertEqual(other_side_wall_2.point_2, core.Point2(0, -1))

        other_side_wall_3 = other_side_wall_2.wall_point_2
        self.assertEqual(other_side_wall_3.point_2, core.Point2(0, -2))
        
        self.assertEqual(wall.other_side_wall, other_side_wall_2)
        self.assertEqual(other_side_wall_2.other_side_wall, wall)

    def test_second_within_first(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -2, 2)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 1)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -2))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        self.assertEqual(wall.point_2, core.Point2(0, -1))

        wall_2 = wall.wall_point_2
        self.assertEqual(wall_2.point_2, core.Point2(0, 1))

        wall_3 = wall_2.wall_point_2
        self.assertEqual(wall_3.point_2, core.Point2(0, 2))

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 1))
        self.assertEqual(wall_2.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall_2)

    def test_first_within_second_partial_wall_1(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -2, 1)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 1))
        self.assertEqual(other_side_wall.point_2, core.Point2(0, -1))

        other_side_wall_2 = other_side_wall.wall_point_2
        self.assertEqual(other_side_wall_2.point_2, core.Point2(0, -2))
        
        self.assertEqual(wall.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall)

    def test_first_within_second_partial_wall_2(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 2)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 2))
        self.assertEqual(other_side_wall.point_2, core.Point2(0, 1))

        other_side_wall_2 = other_side_wall.wall_point_2
        self.assertEqual(other_side_wall_2.point_2, core.Point2(0, -1))
        
        self.assertEqual(wall.other_side_wall, other_side_wall_2)
        self.assertEqual(other_side_wall_2.other_side_wall, wall)

    def test_second_within_first_partial_wall_1(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 2)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 1)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        self.assertEqual(wall.point_2, core.Point2(0, 1))

        wall_2 = wall.wall_point_2
        self.assertEqual(wall_2.point_2, core.Point2(0, 2))

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 1))
        self.assertEqual(wall.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall)

    def test_second_within_first_partial_wall_2(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -2, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 1)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -2))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        self.assertEqual(wall.point_2, core.Point2(0, -1))

        wall_2 = wall.wall_point_2
        self.assertEqual(wall_2.point_2, core.Point2(0, 1))

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 1))
        self.assertEqual(wall_2.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall_2)

    def test_split_with_multiple_sectors(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, 0, 1)
        third_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 0)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        wall_2 = wall.wall_point_2

        other_side_wall = utils.find_wall_on_point(second_sector, core.Point2(0, 1))
        self.assertEqual(wall_2.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall_2)

        other_side_wall_2 = utils.find_wall_on_point(third_sector, core.Point2(0, 0))
        self.assertEqual(wall.other_side_wall, other_side_wall_2)
        self.assertEqual(other_side_wall_2.other_side_wall, wall)

    def test_split_with_multiple_sectors_different_sector_order(self):
        first_sector = utils.build_rectangular_sector(self._sectors, -1, 0, -1, 1)
        second_sector = utils.build_rectangular_sector(self._sectors, 0, 1, -1, 0)
        third_sector = utils.build_rectangular_sector(self._sectors, 0, 1, 0, 1)

        wall = utils.find_wall_on_point(first_sector, core.Point2(0, -1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        wall_2 = wall.wall_point_2

        other_side_wall = utils.find_wall_on_point(third_sector, core.Point2(0, 1))
        self.assertEqual(wall_2.other_side_wall, other_side_wall)
        self.assertEqual(other_side_wall.other_side_wall, wall_2)

        other_side_wall_2 = utils.find_wall_on_point(second_sector, core.Point2(0, 0))
        self.assertEqual(wall.other_side_wall, other_side_wall_2)
        self.assertEqual(other_side_wall_2.other_side_wall, wall)
