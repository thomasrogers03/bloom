# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import os.path
import pickle
import typing

import numpy

from .. import data_loading, game_map
from ..rff import RFF


class Header(data_loading.CustomStruct):
    version: data_loading.UInt32
    tile_count: data_loading.UInt32
    tile_start: data_loading.UInt32
    tile_end: data_loading.UInt32


class AnimationData(data_loading.CustomStruct):
    count: data_loading.PartialInteger(data_loading.UInt8, 6)
    animation_type: data_loading.PartialInteger(data_loading.UInt8, 2)

    offset_x: data_loading.Int8
    offset_y: data_loading.Int8

    tics_per_frame: data_loading.PartialInteger(data_loading.UInt8, 4)
    view: data_loading.PartialInteger(data_loading.UInt8, 3)
    unknown: data_loading.PartialInteger(data_loading.UInt8, 1)


class Tile:

    def __init__(self, width: int, height: int, animation_data: AnimationData, data_offset: int):
        self._width = width
        self._height = height
        self._animation_data = animation_data
        self._data_offset = data_offset

    @property
    def animation_data(self):
        return self._animation_data

    @property
    def data_size(self):
        return self._width * self._height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def x_offset(self):
        return self._animation_data.offset_x

    @property
    def y_offset(self):
        return self._animation_data.offset_y

    def load(self, unpacker: data_loading.Unpacker, palette, palette_lookup):
        unpacker.seek(self._data_offset)
        indices = numpy.frombuffer(
            unpacker.get_bytes(self.data_size),
            dtype='uint8'
        ).reshape((self._width, self._height)).T

        return palette[palette_lookup[indices]]


class ArtData(typing.NamedTuple):
    widths: typing.List[int]
    heights: typing.List[int]
    animation_data: typing.List[AnimationData]
    data_offset: int

class Art:

    def __init__(self, rff: RFF, path: str):
        with open(path, 'rb') as file:
            tile_data = file.read()
        self._unpacker = data_loading.Unpacker(tile_data)

        self._header = self._unpacker.read_struct(Header)
        self._count = self._header.tile_end - self._header.tile_start + 1

        art_data = self._load_art_data(path)
        data_offset = art_data.data_offset

        self._tiles: typing.List[Tile] = []
        combined_tile_data = zip(
            art_data.widths,
            art_data.heights,
            art_data.animation_data
        )
        for width, height, animation_data in combined_tile_data:
            tile = Tile(width, height, animation_data, data_offset)
            self._tiles.append(tile)

            data_offset += tile.data_size

        self._palettes = {}
        for palette_entry in rff.find_matching_entries('*.pal'):
            palette = numpy.frombuffer(
                rff.data_for_entry(palette_entry),
                dtype='uint8'
            ).reshape((256, 3))
            b, g, r = palette[:, 0], palette[:, 1], palette[:, 2]
            a = [255] * 255 + [0]
            palette = numpy.array(list(zip(r, g, b, a))).astype('uint8')
            self._palettes[palette_entry] = palette

        self._lookups = []
        for lookup_entry in rff.find_matching_entries('*.plu'):
            lookup = numpy.frombuffer(
                rff.data_for_entry(lookup_entry),
                dtype='uint8'
            ).reshape((64, 256))
            lookup = numpy.array(lookup)
            lookup[:, 255] = 255
            self._lookups.append(lookup)

        self._default_palette = self._palettes['BLOOD.PAL']

    def _load_art_data(self, path: str):
        art_name = os.path.basename(path)
        cache_path = f'cache/{art_name}.data.bin'

        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as file:
                return pickle.load(file)
            
        widths = self._unpacker.read_multiple_members(data_loading.UInt16, self._count)
        heights = self._unpacker.read_multiple_members(data_loading.UInt16, self._count)
        animation_data = self._unpacker.read_multiple(AnimationData, self._count)
        art_data = ArtData(
            widths,
            heights,
            animation_data,
            self._unpacker.offset
        )

        with open(cache_path, 'w+b') as file:
            pickle.dump(art_data, file)
        
        return art_data

    @property
    def count(self):
        return len(self._tiles)

    def get_tile_indices(self):
        return [
            index for index in range(self._header.tile_start, self._header.tile_end)
        ]

    def has_tile(self, tile_number):
        return tile_number >= self._header.tile_start and tile_number <= self._header.tile_end

    def get_tile_animation_data(self, tile_number: int):
        return self.get_tile(tile_number).animation_data

    def get_tile_dimensions(self, tile_number: int):
        tile = self.get_tile(tile_number)
        return (tile.width, tile.height)

    def get_tile_offsets(self, tile_number: int):
        tile = self.get_tile(tile_number)
        return (tile.x_offset, tile.y_offset)

    def load_tile_image(self, tile_number: int, lookup: int):
        return self.get_tile(tile_number).load(self._unpacker, self._default_palette, self._lookups[lookup][0])

    def get_tile(self, tile_number: int):
        return self._tiles[tile_number - self._header.tile_start]


class ArtManager:

    def __init__(self, rff: RFF, paths: typing.List[str]):
        self._art = [Art(rff, path) for path in paths]
        self._tile_count = sum(art.count for art in self._art)

    def get_tile_indices(self):
        return [
            index for art in self._art for index in art.get_tile_indices()
        ]

    def get_tile_animation_data(self, tile_number: int):
        return self._get_art(tile_number).get_tile_animation_data(tile_number)

    def get_tile_dimensions(self, tile_number: int):
        return self._get_art(tile_number).get_tile_dimensions(tile_number)

    def get_tile_offsets(self, tile_number: int):
        return self._get_art(tile_number).get_tile_offsets(tile_number)

    def load_tile_image(self, tile_number: int, lookup: int):
        return self._get_art(tile_number).load_tile_image(tile_number, lookup)

    def _get_art(self, tile_number: int):
        for art in self._art:
            if art.has_tile(tile_number):
                return art

        raise ValueError(f'Tile {tile_number} not available')
