# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import queue
import time
import typing
from glob import glob

from panda3d import core

from .. import constants, edit_mode
from ..rff import RFF
from . import art


class AnimationData(typing.NamedTuple):
    picnum: int
    ticks_per_frame: int
    animation_count: int


class Manager:
    _QUEUE_TYPE = """queue.Queue[
        typing.Tuple[
            int,
            int,
            typing.Callable[[core.Texture], None]
        ]
    ]"""

    def __init__(self, blood_path: str, rff: RFF, edit_mode_selector: edit_mode.EditMode):
        self._edit_mode_selector = edit_mode_selector
        self._tiles: typing.Dict[int, typing.Dict[int, core.Texture]] = {}
        self._tile_loads: queue.Queue[typing.Tuple[int, int,
                                                   typing.Callable[[core.Texture], None]]] = queue.Queue()

        art_paths = glob(f'{blood_path}/*.[aA][rR][tT]')
        self._art_manager = art.ArtManager(rff, art_paths)
        self._edit_mode_selector.always_run(self._process_loading_tiles)

    def get_all_tiles(self) -> typing.List[int]:
        return sorted(self._art_manager.get_tile_indices())

    def get_tile_dimensions(self, picnum: int):
        width, height = self._art_manager.get_tile_dimensions(picnum)
        return core.Vec2(width, height)

    def get_tile_offsets(self, picnum: int):
        x_offset, y_offset = self._art_manager.get_tile_offsets(picnum)
        return core.Vec2(x_offset, y_offset)

    def get_tile(self, picnum: int, lookup: int):
        if lookup not in self._tiles:
            self._tiles[lookup] = {}

        lookup_tiles = self._tiles[lookup]
        if picnum not in lookup_tiles:
            image = self._art_manager.load_tile_image(picnum, lookup)
            buffer = image.tobytes()

            tile = core.Texture()
            tile.setup_2d_texture(
                image.shape[1],
                image.shape[0],
                core.Texture.T_unsigned_byte,
                core.Texture.F_rgba8
            )
            tile.set_ram_image(buffer)
            lookup_tiles[picnum] = tile

        return lookup_tiles[picnum]

    def get_animation_data(self, picnum: int):
        animation_data = self._art_manager.get_tile_animation_data(picnum)
        if animation_data.count > 0:
            return AnimationData(
                picnum,
                animation_data.tics_per_frame,
                animation_data.count
            )

    def get_tile_async(self, picnum: int, lookup: int, callback: typing.Callable[[core.Texture], None]):
        self._tile_loads.put((picnum, lookup, callback))

    def _process_loading_tiles(self):
        with self._edit_mode_selector.track_performance_stats('process_loading_tiles'):
            now = time.time()
            while (time.time() - now) < constants.TICK_RATE / 2:
                if self._tile_loads.empty():
                    break

                tile_to_load, lookup, callback = self._tile_loads.get_nowait()
                callback(self.get_tile(tile_to_load, lookup))
