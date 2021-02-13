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
        self._sectors = utils.new_sector_collection()

    def tearDown(self):
        test_id = self.id()
        for sector_index, sector in enumerate(self._sectors.sectors):
            utils.save_sector_images(
                f"{test_id}-sector_{sector_index}", sector, self._sectors
            )

    def test_can_link(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        other_side_sector = utils.build_rectangular_sector(self._sectors, -1, 1, 1, 2)

        link_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()

        link_other_side_wall = utils.find_wall_on_point(
            other_side_sector, core.Point2(-1, 1)
        )
        self.assertEqual(link_wall.other_side_wall, link_other_side_wall)

    def test_no_link_when_facing_same_direction(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        utils.build_rectangular_sector(self._sectors, -2, 2, -2, 1)

        link_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()

        self.assertIsNone(link_wall.other_side_wall)

    def test_can_link_bigger_to_smaller(self):
        sector = utils.build_rectangular_sector(self._sectors, -2, 2, -1, 1)
        other_side_sector = utils.build_rectangular_sector(self._sectors, -1, 1, 1, 2)

        link_wall = utils.find_wall_on_point(sector, core.Point2(2, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()

        split_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        other_side_wall = utils.find_wall_on_point(
            other_side_sector, core.Point2(-1, 1)
        )
        self.assertEqual(split_wall.other_side_wall, other_side_wall)

    def test_can_link_smaller_to_bigger_one_split_first_wall(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        other_side_sector = utils.build_rectangular_sector(self._sectors, -1, 2, 1, 2)

        link_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()

        link_other_side_wall = utils.find_wall_on_point(
            other_side_sector, core.Point2(-1, 1)
        )
        self.assertEqual(link_wall.other_side_wall, link_other_side_wall)

    def test_can_link_smaller_to_bigger_one_split_second_wall(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        other_side_sector = utils.build_rectangular_sector(self._sectors, -2, 1, 1, 2)

        link_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()

        link_other_side_wall = utils.find_wall_on_point(
            other_side_sector, core.Point2(-1, 1)
        )
        self.assertEqual(link_wall.other_side_wall, link_other_side_wall)

    def test_can_link_smaller_to_bigger_two_splits(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        other_side_sector = utils.build_rectangular_sector(self._sectors, -2, 2, 1, 2)

        link_wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(link_wall, self._sectors).try_link_wall()

        link_other_side_wall = utils.find_wall_on_point(
            other_side_sector, core.Point2(-1, 1)
        )
        self.assertEqual(link_wall.other_side_wall, link_other_side_wall)

    @unittest.skip
    def test_does_not_link_adjacent_wall(self):
        raise NotImplementedError()
