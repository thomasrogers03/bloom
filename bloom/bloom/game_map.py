# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import os.path
import pickle
import typing
import zlib

from . import constants, data_loading
from .map_data import headers, sector, sprite, wall


class Map:
    _DEFAULT_MAP_SIZE = 2048

    def __init__(self):
        self._encrypted = True

        self._header_0 = headers.MapHeader0.default()
        self._header_1 = headers.MapHeader1.default()
        self._header_2 = headers.MapHeader2.default()
        self._header_3 = headers.MapHeader3.default()
        self._header_4 = headers.MapHeader4.default()

        self._sky_offsets = [0]

        self._sectors: typing.List[sector.Sector] = []
        self._walls: typing.List[wall.Wall] = []
        self._sprites: typing.List[sprite.Sprite] = []
        self._crc: int = None

    @staticmethod
    def load(map_path: str, map_data: bytes):
        result = Map()
        result._load(map_path, map_data)
        return result

    def new(self):
        new_sector = sector.Sector()
        new_sector.sector.floor_z = self._DEFAULT_MAP_SIZE * 16
        new_sector.sector.ceiling_z = -self._DEFAULT_MAP_SIZE * 16
        new_sector.sector.first_wall_index = 0
        new_sector.sector.wall_count = 4
        new_sector.sector.tags[2] = -1
        self._sectors.append(new_sector)

        wall_1 = wall.Wall()
        wall_1.wall.position_x = -self._DEFAULT_MAP_SIZE
        wall_1.wall.position_y = -self._DEFAULT_MAP_SIZE
        wall_1.wall.repeat_x = 32
        wall_1.wall.repeat_y = 8
        wall_1.wall.point2_index = 1
        wall_1.wall.other_side_sector_index = -1
        wall_1.wall.other_side_wall_index = -1
        self._walls.append(wall_1)

        wall_2 = wall.Wall()
        wall_2.wall.position_x = self._DEFAULT_MAP_SIZE
        wall_2.wall.position_y = -self._DEFAULT_MAP_SIZE
        wall_2.wall.repeat_x = 32
        wall_2.wall.repeat_y = 8
        wall_2.wall.point2_index = 2
        wall_2.wall.other_side_sector_index = -1
        wall_2.wall.other_side_wall_index = -1
        self._walls.append(wall_2)

        wall_3 = wall.Wall()
        wall_3.wall.position_x = self._DEFAULT_MAP_SIZE
        wall_3.wall.position_y = self._DEFAULT_MAP_SIZE
        wall_3.wall.repeat_x = 32
        wall_3.wall.repeat_y = 8
        wall_3.wall.point2_index = 3
        wall_3.wall.other_side_sector_index = -1
        wall_3.wall.other_side_wall_index = -1
        self._walls.append(wall_3)

        wall_4 = wall.Wall()
        wall_4.wall.position_x = -self._DEFAULT_MAP_SIZE
        wall_4.wall.position_y = self._DEFAULT_MAP_SIZE
        wall_4.wall.repeat_x = 32
        wall_4.wall.repeat_y = 8
        wall_4.wall.point2_index = 0
        wall_4.wall.other_side_sector_index = -1
        wall_4.wall.other_side_wall_index = -1
        self._walls.append(wall_4)

        start_sprite = sprite.Sprite()
        start_sprite.sprite.tags[0] = 1
        start_sprite.sprite.tags[2] = 2047
        start_sprite.sprite.stat.centring = 1
        start_sprite.sprite.clip_distance = 32
        start_sprite.sprite.velocity_x = 1
        start_sprite.sprite.picnum = 2522
        start_sprite.sprite.sector_index = 0
        start_sprite.sprite.repeat_x = 64
        start_sprite.sprite.repeat_y = 64
        self._sprites.append(start_sprite)

        self._header_1.player_sector = 0

    @staticmethod
    def _get_cache_name(map_path: str):
        map_name = os.path.basename(map_path)
        return os.path.join(constants.CACHE_PATH, f'{map_name}.mapcache')

    def _load_from_cache(self, map_path) -> bool:
        if not constants.MAP_CACHE_ENABLED:
            return False

        cache_path = self._get_cache_name(map_path)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as file:
                self._header_0 = pickle.load(file)
                self._encrypted = pickle.load(file)
                self._header_1 = pickle.load(file)
                self._header_2 = pickle.load(file)
                self._header_3 = pickle.load(file)
                self._header_4 = pickle.load(file)
                self._sky_offsets = pickle.load(file)
                self._sectors = pickle.load(file)
                self._walls = pickle.load(file)
                self._sprites = pickle.load(file)
            return True
        return False

    def _save_to_cache(self, map_path):
        if not constants.MAP_CACHE_ENABLED:
            return

        cache_path = self._get_cache_name(map_path)
        with open(cache_path, 'w+b') as file:
            pickle.dump(self._header_0, file)
            pickle.dump(self._encrypted, file)
            pickle.dump(self._header_1, file)
            pickle.dump(self._header_2, file)
            pickle.dump(self._header_3, file)
            pickle.dump(self._header_4, file)
            pickle.dump(self._sky_offsets, file)
            pickle.dump(self._sectors, file)
            pickle.dump(self._walls, file)
            pickle.dump(self._sprites, file)

    def _load(self, map_path: str, map_data: bytes):
        if self._load_from_cache(map_path):
            return

        unpacker = data_loading.Unpacker(map_data)
        self._header_0 = unpacker.read_struct(headers.MapHeader0)

        if self._header_0.major_version == 6 and self._header_0.minor_version == 3:
            self._encrypted = False
        elif self._header_0.major_version == 7 and self._header_0.minor_version == 0:
            self._encrypted = True
        else:
            raise ValueError('Unsupported map format')

        if self._encrypted:
            self._header_1 = unpacker.read_xor_encrypted_struct(
                headers.MapHeader1,
                0x4D
            )
        else:
            self._header_1 = unpacker.read_struct(headers.MapHeader1)

        if self._encrypted:
            key = (0x4D + headers.MapHeader1.size()) & 0xFF
            self._header_2 = unpacker.read_xor_encrypted_struct(
                headers.MapHeader2,
                key
            )
        else:
            self._header_2 = unpacker.read_struct(headers.MapHeader2)

        if self._encrypted:
            key = (
                0x4D + headers.MapHeader1.size() +
                headers.MapHeader2.size()
            ) & 0xFF
            self._header_3 = unpacker.read_xor_encrypted_struct(
                headers.MapHeader3,
                key
            )
        else:
            self._header_3 = unpacker.read_struct(headers.MapHeader3)

        if self._encrypted:
            key = self._header_3.wall_count & 0xFF
            self._header_4 = unpacker.read_xor_encrypted_struct(
                headers.MapHeader4,
                key
            )
        else:
            self._header_4 = None

        if self._encrypted:
            sky_offsets_size = unpacker.get_xor_encrypted_bytes(2, 0x00)
            unpacker.seek_incrementally(-2)
            self._sky_offsets = unpacker.read_multiple_xor_encrypted_members(
                data_loading.Int16,
                sky_offsets_size[0] // 2,
                sky_offsets_size[0]
            )
        else:
            self._sky_offsets = unpacker.read_multiple_members(data_loading.Int16, 16)

        self._sectors = sector.load_sectors(
            unpacker,
            self._encrypted,
            self._header_3
        )
        self._walls = wall.load_walls(
            unpacker,
            self._encrypted,
            self._header_3
        )
        self._sprites = sprite.load_sprites(
            unpacker,
            self._encrypted,
            self._header_3
        )
        self._crc = unpacker.read_member(data_loading.UInt32)

        self._save_to_cache(map_path)

    def save(
        self, 
        map_path: str,
        start_position_x: int, 
        start_position_y: int, 
        start_position_z: int,
        start_theta: int,
        start_sector_index: int
    ) -> bytes:
        packer = data_loading.Packer()

        self._header_1.player_position[0] = start_position_x
        self._header_1.player_position[1] = start_position_y
        self._header_1.player_position[2] = start_position_z
        self._header_1.player_theta = start_theta
        self._header_1.player_sector = start_sector_index

        self._header_3.sector_count = len(self._sectors)
        self._header_3.wall_count = len(self._walls)
        self._header_3.sprite_count = len(self._sprites)

        self._save_to_cache(map_path)

        packer.write_struct(self._header_0)

        if self._encrypted:
            packer.write_xor_encrypted_struct(self._header_1, 0x4D)
        else:
            packer.write_struct(self._header_1)

        if self._encrypted:
            key = (0x4D + headers.MapHeader1.size()) & 0xFF
            packer.write_xor_encrypted_struct(self._header_2, key)
        else:
            packer.write_struct(self._header_2)

        if self._encrypted:
            key = (
                0x4D + headers.MapHeader1.size() +
                headers.MapHeader2.size()
            ) & 0xFF
            packer.write_xor_encrypted_struct(self._header_3, key)
        else:
            packer.write_struct(self._header_3)

        if self._header_4 is not None:
            key = self._header_3.wall_count & 0xFF
            packer.write_xor_encrypted_struct(self._header_4, key)

        if self._encrypted:
            packer.write_multiple_xor_encrypted_members(
                data_loading.UInt16,
                self._sky_offsets,
                len(self._sky_offsets) * 2
            )
        else:
            packer.write_multiple_members(data_loading.UInt16, self._sky_offsets)

        sector.save_sectors(
            packer,
            self._encrypted,
            self._header_3,
            self._sectors
        )
        wall.save_walls(
            packer,
            self._encrypted,
            self._header_3,
            self._walls
        )
        sprite.save_sprites(
            packer,
            self._encrypted,
            self._header_3,
            self._sprites
        )

        self._crc = zlib.crc32(packer.get_bytes())
        packer.write_member(data_loading.UInt32, self._crc)

        return packer.get_bytes()

    @property
    def sectors(self) -> typing.List[sector.Sector]:
        return self._sectors

    @property
    def walls(self) -> typing.List[wall.Wall]:
        return self._walls

    @property
    def sprites(self) -> typing.List[sprite.Sprite]:
        return self._sprites

    @property
    def start_position(self):
        return self._header_1.player_position

    @property
    def start_theta(self):
        return self._header_1.player_theta

    @property
    def sky_offsets(self) -> typing.List[int]:
        return self._sky_offsets
