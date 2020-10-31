# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import time
import typing
from glob import glob

import numpy

from . import data_loading, game_map
from .rff import RFF

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
        self._image = None

    @property
    def image(self):
        return self._image

    @property
    def data_size(self):
        return self._width * self._height

    def load(self, unpacker: data_loading.Unpacker, palette):
        if self._image is not None:
            return

        unpacker.seek(self._data_offset)
        indices = numpy.frombuffer(
            unpacker.get_bytes(self.data_size),
            dtype='uint8'
        ).reshape((self._width, self._height)).T
        image = palette[indices]
        self._image = image

class Art:

    def __init__(self, rff: RFF, path: str):
        with open(path, 'rb') as file:
            tile_data = file.read()
        self._unpacker = data_loading.Unpacker(tile_data)

        self._header = self._unpacker.read_struct(Header)
        count = self._header.tile_end - self._header.tile_start + 1

        widths = self._unpacker.read_multiple_members(data_loading.UInt16, count)
        heights = self._unpacker.read_multiple_members(data_loading.UInt16, count)
        list_of_animation_data = self._unpacker.read_multiple(AnimationData, count)

        data_offset = self._unpacker.offset

        self._tiles: typing.List[Tile] = []
        combined_tile_data = zip(widths, heights, list_of_animation_data)
        for width, height, animation_data in combined_tile_data:
            tile = Tile(width, height, animation_data, data_offset)
            self._tiles.append(tile)

            data_offset += tile.data_size

        palette = numpy.frombuffer(
            rff.data_for_entry(
                'BLOOD.PAL'
            ),
            dtype='uint8'
        ).reshape((256, 3))
        b, g, r = palette[:,0], palette[:,1], palette[:,2]
        a = [255] * 255 + [0]
        self._default_palette = numpy.array(list(zip(r, g, b, a))).astype('uint8')

    @property
    def count(self):
        return len(self._tiles)

    def has_tile(self, tile_number):
        return tile_number >= self._header.tile_start and tile_number <= self._header.tile_end

    def get_tile_image(self, tile_number):
        tile = self._tiles[tile_number - self._header.tile_start]
        tile.load(self._unpacker, self._default_palette)
        
        return tile.image

class ArtManager:

    def __init__(self, rff: RFF, paths: typing.List[str]):
        self._art = [Art(rff, path) for path in paths]
        self._tile_count = sum(art.count for art in self._art)

    @property
    def tile_count(self):
        return self._tile_count

    def get_tile_image(self, tile_number):
        for art in self._art:
            if art.has_tile(tile_number):
                return art.get_tile_image(tile_number)
        
        raise ValueError(f'Tile {tile_number} not available')
