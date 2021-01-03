# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import os.path
from concurrent import futures

import yaml

from . import cameras, constants, game_map
from .editor import map_editor

logger = logging.getLogger(__name__)


class AutoSave:
    _MAX_BACKUPS = 10
    _executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(
        self,
        editor: map_editor.MapEditor,
        meta_data: dict,
        camera_collection: cameras.Cameras,
        map_path: str
    ):
        self._editor = editor
        self._meta_data = meta_data
        self._camera_collection = camera_collection
        self._map_path_prefix = map_path[:constants.MAP_EXTENSION_SKIP]
        self._stopped = False

    def perform_save(self, task):
        if self._stopped:
            return task.done

        self._truncate_backups()
        position = self._camera_collection.get_builder_position()
        map_to_save = self._editor.to_game_map(position)

        self._executor.submit(self._do_save, map_to_save)

        path = self._map_path(0)
        self._log_info(f'Auto saving to {path}')

        return task.again

    def stop(self):
        self._stopped = True

    def _truncate_backups(self):
        backup_indices = reversed(range(self._MAX_BACKUPS - 1))
        for index in backup_indices:
            self._move_backup(index)

    def _move_backup(self, index: int):
        old_path = self._map_path(index)
        if not os.path.exists(old_path):
            return

        new_index = index + 1
        old_meta_data_path = self._meta_data_path(index)

        new_path = self._map_path(new_index)
        new_meta_data_path = self._meta_data_path(new_index)

        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(old_path, new_path)
        if os.path.exists(old_meta_data_path):
            if os.path.exists(new_meta_data_path):
                os.remove(new_meta_data_path)
            os.rename(old_meta_data_path, new_meta_data_path)

    def _map_path(self, index: int):
        return f'{self._map_path_prefix}-BACKUP-{index}.MAP'

    def _meta_data_path(self, index: int):
        return f'{self._map_path_prefix}-BACKUP-{index}.YAML'

    def _do_save(self, map_to_save: game_map.Map):
        path = self._map_path(0)
        meta_data_path = self._meta_data_path(0)

        result, _ = map_to_save.save(path)
        with open(path, 'w+b') as file:
            file.write(result)

        with open(meta_data_path, 'w+') as file:
            file.write(yaml.dump(self._meta_data))

    def _log_info(self, message: str):
        logger.info(message)
        self._camera_collection.set_info_text(message)
