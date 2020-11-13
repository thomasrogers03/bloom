# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw


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
        self._assert_sector_clockwise(sector)
        self._assert_has_point(sector, core.Point2(-1, -1))
        self._assert_has_point(sector, core.Point2(-1, 0))
        self._assert_has_point(sector, core.Point2(1, 0))
        self._assert_has_point(sector, core.Point2(1, -1))

        new_sector = self._sectors.sectors[1]
        self.assertEqual(4, len(new_sector.walls))
        self._assert_sector_clockwise(new_sector)
        self._assert_has_point(new_sector, core.Point2(-1, 1))
        self._assert_has_point(new_sector, core.Point2(-1, 0))
        self._assert_has_point(new_sector, core.Point2(1, 1))
        self._assert_has_point(new_sector, core.Point2(1, 0))

        split_wall = self._find_wall_on_point(sector, core.Point2(-1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(1, 0))
        self.assertEqual(split_wall.other_side_wall.get_sector(), new_sector)

        split_wall = self._find_wall_on_point(new_sector, core.Point2(1, 0))
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
        self._assert_sector_clockwise(sector)
        self._assert_has_point(sector, core.Point2(0, 1))
        self._assert_has_point(sector, core.Point2(1, 1))
        self._assert_has_point(sector, core.Point2(1, -1))
        self._assert_has_point(sector, core.Point2(0, -1))

        new_sector = self._sectors.sectors[1]
        self.assertEqual(4, len(new_sector.walls))
        self._assert_sector_clockwise(new_sector)
        self._assert_has_point(new_sector, core.Point2(0, -1))
        self._assert_has_point(new_sector, core.Point2(-1, -1))
        self._assert_has_point(new_sector, core.Point2(-1, 1))
        self._assert_has_point(new_sector, core.Point2(0, 1))

        split_wall = self._find_wall_on_point(sector, core.Point2(0, -1))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, 1))
        self.assertEqual(split_wall.other_side_wall.get_sector(), new_sector)

        split_wall = self._find_wall_on_point(new_sector, core.Point2(0, 1))
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
        self._assert_sector_clockwise(sector)
        self._assert_has_point(sector, core.Point2(-1, 0))
        self._assert_has_point(sector, core.Point2(0, 0))
        self._assert_has_point(sector, core.Point2(1, 0))

        new_sector = self._sectors.sectors[1]
        self.assertEqual(5, len(new_sector.walls))
        self._assert_sector_clockwise(new_sector)
        self._assert_has_point(new_sector, core.Point2(-1, 0))
        self._assert_has_point(new_sector, core.Point2(0, 0))
        self._assert_has_point(new_sector, core.Point2(1, 0))

        split_wall = self._find_wall_on_point(sector, core.Point2(-1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, 0))

        split_wall = self._find_wall_on_point(sector, core.Point2(0, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(1, 0))

        split_wall = self._find_wall_on_point(new_sector, core.Point2(1, 0))
        self.assertEqual(split_wall.other_side_wall.point_1, core.Point2(0, 0))

        split_wall = self._find_wall_on_point(new_sector, core.Point2(0, 0))
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

        self.assertEqual(12, len(sector.walls))
        self._assert_sector_clockwise(sector)
        self._assert_wall_bunch_not_clockwise(sector, core.Point2(-1, 0))

        new_sector = self._sectors.sectors[2]
        self._assert_sector_clockwise(new_sector)
        self.assertEqual(8, len(new_sector.walls))

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
        sector = self._sectors.new_sector(map_data.sector.Sector())

        point_1 = sector.add_wall(map_data.wall.Wall())
        point_1.teleport_point_1_to(core.Point2(left, bottom))

        point_2 = sector.add_wall(map_data.wall.Wall())
        point_2.teleport_point_1_to(core.Point2(left, top))

        point_3 = sector.add_wall(map_data.wall.Wall())
        point_3.teleport_point_1_to(core.Point2(right, top))

        point_4 = sector.add_wall(map_data.wall.Wall())
        point_4.teleport_point_1_to(core.Point2(right, bottom))

        point_1.set_wall_point_2(point_2)
        point_2.set_wall_point_2(point_3)
        point_3.set_wall_point_2(point_4)
        point_4.set_wall_point_2(point_1)

        return sector

    @staticmethod
    def _find_wall_on_point(sector: map_objects.EditorSector, point: core.Point2):
        for wall in sector.walls:
            if wall.point_1 == point:
                return wall

        raise ValueError('Point not found')

    @staticmethod
    def _assert_sector_clockwise(sector: map_objects.EditorSector):
        points: typing.List[core.Point2] = []

        first_wall = sector.walls[0]
        wall = first_wall.wall_point_2
        while wall != first_wall:
            points.append(wall.point_1)
            wall = wall.wall_point_2
        points.append(wall.point_1)

        if not sector_draw.is_sector_clockwise(points):
            raise AssertionError('Sector was not clockwise')

    @staticmethod
    def _assert_wall_bunch_not_clockwise(
        sector: map_objects.EditorSector, 
        start_point: core.Point2
    ):
        points: typing.List[core.Point2] = []

        first_wall = TestSectorSplit._find_wall_on_point(sector, start_point)
        wall = first_wall.wall_point_2
        while wall != first_wall:
            points.append(wall.point_1)
            wall = wall.wall_point_2
        points.append(wall.point_1)

        if sector_draw.is_sector_clockwise(points):
            raise AssertionError('Sector was clockwise')

    @staticmethod
    def _assert_has_point(sector: map_objects.EditorSector, point: core.Point2):
        points: typing.List[core.Point2] = []
        for wall in sector.walls:
            points.append(wall.point_1)
            if wall.point_1 == point:
                return

        raise AssertionError(f'Point, {point}, not found in {points}')
