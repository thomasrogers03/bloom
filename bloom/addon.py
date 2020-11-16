# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import configparser
import typing

class Map(typing.NamedTuple):
    name: str
    title: str
    author: str
    song: str
    endings: typing.List[int]
    messages: typing.List[str]

class Episode(typing.NamedTuple):
    title: str
    maps: typing.Dict[str, Map]

class Addon:

    def __init__(self, path: str):
        config = configparser.ConfigParser()
        config.read(path)

        self._episodes: typing.Dict[int, Episode] = {}
        self._all_maps: typing.Dict[int, Map] = {}
        for section in config:
            episode_number = self._section_episode_number(section)
            if episode_number is None:
                continue

            self._episodes[episode_number] = Episode(config[section]['Title'], {})
            for sub_section in config[section]:
                map_number = self._section_map_number(sub_section)
                if map_number is None:
                    continue

                map_name = config[section][sub_section]
                if map_name not in config:
                    continue

                map_name = map_name.lower()
                map_section = config[map_name]
                map_definition = Map(
                    map_name,
                    map_section['Title'],
                    map_section.get('Author', 'unknown'),
                    map_section.get('Song', '').upper(),
                    [],
                    []
                )
                self._episodes[episode_number].maps[map_number] = map_definition
                self._all_maps[map_name] = map_definition
            
    @staticmethod
    def _section_episode_number(section: str):
        episode = 'episode'
        if section.lower().startswith(episode):
            return int(section[len(episode):])
        return None
            
    @staticmethod
    def _section_map_number(section: str):
        map = 'map'
        if section.lower().startswith(map):
            return int(section[len(map):])
        return None

    def song_for_map(self, map_name: str):
        map_name = map_name.lower()
        if map_name in self._all_maps:
            return self._all_maps[map_name].song
        return None