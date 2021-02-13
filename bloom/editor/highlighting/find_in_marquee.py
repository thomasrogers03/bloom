# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects
from . import highlight_details


class FindInMarquee:
    def __init__(
        self,
        sectors: typing.List[map_objects.EditorSector],
        start: core.Point2,
        end: core.Point2,
    ):
        self._sectors = sectors
        self._start = start
        self._end = end

    def get_objects(self):
        result: typing.List[highlight_details] = []

        hit = core.Point3(self._start.x, self._start.y, 0)

        for sector in self._sectors:
            highlight_count = 0
            for wall in sector.walls:
                if self._point_in_marquee(wall.point_1):
                    if self._point_in_marquee(wall.point_2):
                        part = wall.default_part
                    else:
                        part = f"{wall.vertex_part_name}_highlight"
                    highlight = highlight_details.HighlightDetails(wall, part, hit)
                    highlight_count += 1
                    result.append(highlight)

            if highlight_count == len(sector.walls):
                highlight = highlight_details.HighlightDetails(
                    sector, sector.default_part, hit
                )
                result.append(highlight)

            for sprite in sector.sprites:
                if self._point_in_marquee(sprite.origin_2d):
                    highlight = highlight_details.HighlightDetails(
                        sprite, sprite.default_part, hit
                    )
                    result.append(highlight)

        return result

    def _point_in_marquee(self, point: core.Point2):
        return (
            point.x >= self._start.x
            and point.x <= self._end.x
            and point.y >= self._start.y
            and point.y <= self._end.y
        )
