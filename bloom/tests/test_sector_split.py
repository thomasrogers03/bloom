# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw
from . import utils


class TestSectorSplit(unittest.TestCase):

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

    def test_can_split(self):
        sector = self._build_rectangular_sector(-1, 1, -1, 1)
        self._do_split(
            sector,
            [
                core.Point2(-1, 0),
                core.Point2(1, 0)
            ]
        )
        self.assertEqual(2, len(self._sectors.sectors))

        self.assertEqual(4, len(sector.walls))
        utils.assert_wall_bunch_not_clockwise(sector, core.Point2(1, 1))
        utils.assert_sector_has_point(sector, core.Point2(1, 0))
        utils.assert_sector_has_point(sector, core.Point2(1, 1))
        utils.assert_sector_has_point(sector, core.Point2(-1, 1))
        utils.assert_sector_has_point(sector, core.Point2(-1, 0))

        new_sector = self._sectors.sectors[1]
        self.assertEqual(4, len(new_sector.walls))
        utils.assert_wall_bunch_not_clockwise(new_sector, core.Point2(-1, -1))
        utils.assert_sector_has_point(new_sector, core.Point2(-1, -1))
        utils.assert_sector_has_point(new_sector, core.Point2(1, -1))
        utils.assert_sector_has_point(new_sector, core.Point2(1, 0))
        utils.assert_sector_has_point(new_sector, core.Point2(-1, 0))

        split_wall = utils.find_wall_on_point(sector, core.Point2(-1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(1, 0))
        self.assertEqual(split_wall.other_side_wall.get_sector(), new_sector)

        split_wall = utils.find_wall_on_point(new_sector, core.Point2(1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(-1, 0))
        self.assertEqual(split_wall.other_side_wall.get_sector(), sector)

    def test_can_split_vertically(self):
        sector = self._build_rectangular_sector(-1, 1, -1, 1)
        self._do_split(
            sector,
            [
                core.Point2(0, -1),
                core.Point2(0, 1)
            ]
        )
        self.assertEqual(2, len(self._sectors.sectors))

        self.assertEqual(4, len(sector.walls))
        utils.assert_wall_bunch_not_clockwise(sector, core.Point2(-1, 1))
        utils.assert_sector_has_point(sector, core.Point2(-1, 1))
        utils.assert_sector_has_point(sector, core.Point2(-1, -1))
        utils.assert_sector_has_point(sector, core.Point2(0, -1))
        utils.assert_sector_has_point(sector, core.Point2(0, 1))

        new_sector = self._sectors.sectors[1]
        self.assertEqual(4, len(new_sector.walls))
        utils.assert_wall_bunch_not_clockwise(new_sector, core.Point2(1, -1))
        utils.assert_sector_has_point(new_sector, core.Point2(1, -1))
        utils.assert_sector_has_point(new_sector, core.Point2(1, 1))
        utils.assert_sector_has_point(new_sector, core.Point2(0, 1))
        utils.assert_sector_has_point(new_sector, core.Point2(0, -1))

        split_wall = utils.find_wall_on_point(sector, core.Point2(0, -1))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, 1))
        self.assertEqual(split_wall.other_side_wall.get_sector(), new_sector)

        split_wall = utils.find_wall_on_point(new_sector, core.Point2(0, 1))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, -1))
        self.assertEqual(split_wall.other_side_wall.get_sector(), sector)

    def test_can_split_multiple_points(self):
        sector = self._build_rectangular_sector(-1, 1, -1, 1)
        self._do_split(
            sector,
            [
                core.Point2(-1, 0),
                core.Point2(0, 0),
                core.Point2(1, 0)
            ]
        )
        self.assertEqual(2, len(self._sectors.sectors))

        self.assertEqual(5, len(sector.walls))
        utils.assert_wall_bunch_not_clockwise(sector, core.Point2(-1, 1))
        utils.assert_sector_has_point(sector, core.Point2(-1, 0))
        utils.assert_sector_has_point(sector, core.Point2(0, 0))
        utils.assert_sector_has_point(sector, core.Point2(1, 0))

        new_sector = self._sectors.sectors[1]
        self.assertEqual(5, len(new_sector.walls))
        utils.assert_wall_bunch_not_clockwise(new_sector, core.Point2(-1, -1))
        utils.assert_sector_has_point(new_sector, core.Point2(-1, 0))
        utils.assert_sector_has_point(new_sector, core.Point2(0, 0))
        utils.assert_sector_has_point(new_sector, core.Point2(1, 0))

        split_wall = utils.find_wall_on_point(sector, core.Point2(-1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, 0))

        split_wall = utils.find_wall_on_point(sector, core.Point2(0, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(1, 0))

        split_wall = utils.find_wall_on_point(new_sector, core.Point2(1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, 0))

        split_wall = utils.find_wall_on_point(new_sector, core.Point2(0, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(-1, 0))

    def test_can_split_with_island(self):
        sector = self._build_rectangular_sector(-3, 3, -3, 3)
        operations.sector_insert.SectorInsert(sector).insert(
            [
                core.Point2(-1, -1),
                core.Point2(-1, 1),
                core.Point2(1, 1),
                core.Point2(1, -1),
            ]
        )

        self._do_split(
            sector,
            [
                core.Point2(-1, 0),
                core.Point2(-2, 0),
                core.Point2(-2, 2),
                core.Point2(2, 2),
                core.Point2(2, 0),
                core.Point2(1, 0)
            ]
        )
        self.assertEqual(3, len(self._sectors.sectors))

        utils.assert_wall_bunch_not_clockwise(sector, core.Point2(-3, -3))
        utils.assert_wall_bunch_clockwise(sector, core.Point2(-1, 0))
        utils.assert_sector_has_shape(
            sector, 
            core.Point2(-3, -3),
            core.Point2(3, -3),
            core.Point2(3, 3),
            core.Point2(-3, 3),
            
            core.Point2(-1, -1),
            core.Point2(1, -1),
            core.Point2(1, 0),
            core.Point2(2, 0),
            core.Point2(2, 2),
            core.Point2(-2, 2),
            core.Point2(-2, 0),
            core.Point2(-1, 0),
        )

        new_sector = self._sectors.sectors[2]
        utils.assert_wall_bunch_not_clockwise(new_sector, core.Point2(1, 1))
        utils.assert_sector_has_shape(
            new_sector,
            core.Point2(-1, 0),
            core.Point2(-1, 1),
            core.Point2(1, 1),
            core.Point2(1, 0),
            core.Point2(2, 0),
            core.Point2(2, 2),
            core.Point2(-2, 2),
            core.Point2(-2, 0),
        )


    @unittest.skip
    def test_can_split_with_multiple_islands(self):
        raise AssertionError()

    def _do_split(
        self,
        sector: map_objects.EditorSector,
        split_points: typing.List[core.Point2]
    ):
        split = operations.sector_split.SectorSplit(sector, self._sectors)
        split.split(split_points)

    def _build_rectangular_sector(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float
    ):
        return utils.build_rectangular_sector(
            self._sectors,
            left,
            right,
            bottom,
            top
        )

    @staticmethod
    def _assert_does_not_have_point(sector: map_objects.EditorSector, point: core.Point2):
        points: typing.List[core.Point2] = []
        for wall in sector.walls:
            points.append(wall.point_1)
            if wall.point_1 == point:
                raise AssertionError(f'Point, {point}, found in {points}')
