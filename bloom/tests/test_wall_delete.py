# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw
from . import utils


class TestWallDelete(unittest.TestCase):

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

    def test_can_delete(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)

        wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_split.WallSplit(wall).split(core.Point2(0, 1))

        split_wall = utils.find_wall_on_point(sector, core.Point2(0, 1))
        operations.wall_delete.WallDelete(split_wall).delete()

        self.assertEqual(4, len(sector.walls))
        self.assertEqual(split_wall.point_2, core.Point2(-1, 1))

    def test_can_delete_two_sided(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        utils.build_rectangular_sector(self._sectors, -1, 1, 1, 2)

        wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        operations.wall_split.WallSplit(wall).split(core.Point2(0, 1))
        
        wall = utils.find_wall_on_point(sector, core.Point2(0, 1))
        operations.wall_delete.WallDelete(wall).delete()

        wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        self.assertEqual(wall.point_2, core.Point2(-1, 1))
        self.assertEqual(wall.other_side_wall.point_1, core.Point2(-1, 1))

    @unittest.skip
    def test_can_delete_with_other_side(self):
        sector = utils.build_rectangular_sector(self._sectors, -1, 1, -1, 1)
        other_side_sector = utils.build_rectangular_sector(self._sectors, -1, 1, 1, 2)

        wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        operations.wall_link.SectorWallLink(wall, self._sectors).try_link_wall()

        other_side_wall = utils.find_wall_on_point(other_side_sector, core.Point2(-1, 1))
        operations.wall_delete.WallDelete(other_side_wall).delete()

        wall = utils.find_wall_on_point(sector, core.Point2(1, 1))
        self.assertEqual(wall.wall_point_2.point_1, core.Point2(-1, 2))
