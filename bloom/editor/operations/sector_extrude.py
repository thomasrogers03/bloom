# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects, ror_constants


class SectorExtrude:
    _OFFSET = 512
    _WALL_OFFSET = core.Vec2(256, 256)
    _LINK_OFFSET = 64

    def __init__(self, sector: map_objects.EditorSector, all_sectors: map_objects.SectorCollection, part: str):
        self._sector = sector
        self._all_sectors = all_sectors
        self._part = part

    def extrude(self, link_id: int, link_type: str):
        if self._link is not None:
            return

        link_sprite_offset = self._get_link_offset()

        new_sector = self._all_sectors.create_sector(self._sector)
        new_sector.move_ceiling_to(self.new_ceiling_z)
        new_sector.move_floor_to(self.new_floor_z)

        mapped_walls: typing.Dict[map_objects.EditorWall, map_objects.EditorWall] = {}
        for editor_wall in self._walls:
            new_blood_wall = editor_wall.blood_wall.copy()

            new_wall = new_sector.add_wall(new_blood_wall)
            position = new_wall.origin_2d + self._WALL_OFFSET
            new_wall.teleport_point_1_to(position)

            mapped_walls[editor_wall] = new_wall

        for old_wall in self._walls:
            editor_wall = mapped_walls[old_wall]

            new_point_2 = mapped_walls[old_wall.wall_point_2]
            editor_wall.set_wall_point_2(new_point_2)

            new_previous_wall = mapped_walls[old_wall.wall_previous_point]
            editor_wall.wall_previous_point = new_previous_wall

        link_sprite_position = self._walls[0].origin + link_sprite_offset
        link_sprite_position_for_new_sector = link_sprite_position + \
            core.Vec3(self._WALL_OFFSET.x, self._WALL_OFFSET.y, 0)

        if self._part == map_objects.EditorSector.FLOOR_PART:
            upper_sector = self._sector
            lower_sector = new_sector

            upper_sprite_position = link_sprite_position
            lower_sprite_position = link_sprite_position_for_new_sector
        else:
            lower_sector = self._sector
            upper_sector = new_sector

            upper_sprite_position = link_sprite_position_for_new_sector
            lower_sprite_position = link_sprite_position

        upper_link = upper_sector.add_new_sprite(upper_sprite_position)
        lower_link = lower_sector.add_new_sprite(lower_sprite_position)

        picnum = ror_constants.ROR_TILE_MAPPING[link_type]
        upper_sector.sector.sector.floor_picnum = picnum
        lower_sector.sector.sector.ceiling_picnum = picnum

        upper_link.sprite.sprite.picnum = 2332
        upper_link.sprite.sprite.tags[0] = ror_constants.UPPER_TAG_MAPPING[link_type]
        upper_link_z = upper_sector.floor_z_at_point(
            upper_link.origin_2d
        )
        upper_link.move_to(
            core.Point3(
                upper_link.origin_2d.x,
                upper_link.origin_2d.y,
                upper_link_z - upper_link.size.y / 2
            )
        )
        upper_link.sprite.data.data1 = link_id
        
        lower_link.sprite.sprite.picnum = 2331
        lower_link.sprite.sprite.tags[0] = ror_constants.LOWER_TAG_MAPPING[link_type]
        lower_link_z = lower_sector.ceiling_z_at_point(
            lower_link.origin_2d
        )
        lower_link.move_to(
            core.Point3(
                lower_link.origin_2d.x,
                lower_link.origin_2d.y,
                lower_link_z + lower_link.size.y / 2
            )
        )
        lower_link.sprite.data.data1 = link_id

        upper_origin = core.Point3(
            upper_link.origin_2d.x,
            upper_link.origin_2d.y,
            upper_link_z
        )
        upper_sector.link(
            map_objects.EditorSector.FLOOR_PART, 
            lower_sector,
            upper_origin
        )
        lower_origin = core.Point3(
            lower_link.origin_2d.x,
            lower_link.origin_2d.y,
            lower_link_z
        )
        
        lower_sector.link(
            map_objects.EditorSector.CEILING_PART, 
            upper_sector,
            lower_origin
        )

        if link_type in ror_constants.ROR_TYPES_WITH_WATER:
            lower_sector.get_data().underwater = 1

        self._sector.invalidate_geometry()
        new_sector.invalidate_geometry()

    def _get_link_offset(self):
        normal = self._walls[0].get_normal() * self._LINK_OFFSET
        link_sprite_offset_2d = (self._walls[0].get_centre_2d() - normal) - self._walls[0].point_1

        return core.Vec3(
            link_sprite_offset_2d.x,
            link_sprite_offset_2d.y,
            0
        )

    @property
    def _walls(self) -> typing.List[map_objects.EditorWall]:
        return self._sector.walls

    @property
    def _link(self):
        if self._part == map_objects.EditorSector.FLOOR_PART:
            return self._sector.sector_below_floor
        return self._sector.sector_above_ceiling

    @property
    def new_floor_z(self):
        if self._part == map_objects.EditorSector.FLOOR_PART:
            return 2 * self._sector.floor_z - self._sector.ceiling_z
        return self._sector.ceiling_z

    @property
    def new_ceiling_z(self):
        if self._part == map_objects.EditorSector.CEILING_PART:
            return 2 * self._sector.ceiling_z - self._sector.floor_z
        return self._sector.floor_z
