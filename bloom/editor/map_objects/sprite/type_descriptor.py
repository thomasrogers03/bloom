# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing


class Descriptor:
    _DECORATION_CATEGORY = 'decoration'

    def __init__(self, sprite_type: int, descriptor: typing.Dict[str, typing.Any]):
        self._sprite_type = sprite_type
        self._descriptor = descriptor

    @property
    def sprite_repeats(self):
        return self._descriptor.get('repeats', None)

    @property
    def sprite_type(self):
        return self._sprite_type

    @property
    def blocking(self) -> typing.Optional[int]:
        if self._is_decoration:
            return None

        return self._descriptor.get('blocking', 0)

    @property
    def category(self):
        return self._descriptor['category']

    @property
    def name(self):
        return self._descriptor['name']

    @property
    def invisible(self):
        return self._descriptor.get('invisible', False)

    @property
    def palette(self) -> int:
        if self._is_decoration:
            return None

        if 'palette' in self._descriptor:
            return self._descriptor['palette']

        return 0

    @property
    def default_tile(self) -> int:
        if 'tile_config' in self._descriptor:
            tile_config = self._descriptor['tile_config']
            if 'tile' in tile_config:
                return tile_config['tile']
            elif 'tiles' in tile_config:
                return tile_config['tiles'][0]
            elif 'start_tile' in tile_config:
                return tile_config['start_tile']

        return 0

    @property
    def valid_tiles(self) -> typing.List[int]:
        if 'tile_config' in self._descriptor:
            tile_config = self._descriptor['tile_config']
            if 'tile' in tile_config:
                return [tile_config['tile']]
            elif 'tiles' in tile_config:
                return tile_config['tiles']
            elif 'start_tile' in tile_config:
                return [tile_config['start_tile']]

        return None

    @property
    def seq(self) -> typing.Optional[int]:
        return self._descriptor.get('seq', None)

    @property
    def property_descriptors(self) -> typing.List[dict]:
        return self._descriptor.get('properties', [])

    def get_is_droppable(self, category_descriptors: dict) -> bool:
        return category_descriptors[self.category].get('droppable', False)

    def get_status_number(self, category_descriptors: dict):
        return self._descriptor.get(
            'status_number',
            category_descriptors[self.category]['status_number']
        )

    @property
    def _is_decoration(self):
        return self.category == self._DECORATION_CATEGORY
