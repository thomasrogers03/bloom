# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
import unittest
from unittest import mock

from panda3d import core

from .. import game_map, map_data
from ..editor import map_objects, operations
from ..editor.operations import sector_draw


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
        pass
