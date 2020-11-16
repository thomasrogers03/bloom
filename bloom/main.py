# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import pathlib
import sys

from direct.gui import DirectGuiGlobals
from panda3d import core

from . import bloom_app, constants, parameters


def main():
    try:
        options = parameters.get_parameters()
        core.load_prc_file_data('', 'sync-video #f')
        core.load_prc_file_data('', 'show-frame-rate-meter #t')
        core.load_prc_file_data('', 'disable-message-loop #t')
        core.load_prc_file_data('', 'tk-frame-rate 300')
        core.load_prc_file_data('', 'direct-gui-edit 1')
        core.load_prc_file_data('', 'audio-library-name p3openal_audio')
        if options.performance_stats:
            core.load_prc_file_data('', 'want-pstats 1')
        if options.direct_tools:
            raise NotImplementedError()
            # core.load_prc_file_data('', 'want-tk #t')
            # core.load_prc_file_data('', 'want-directtools #t')

        working_directory = pathlib.Path.cwd()
        drive_letter = None
        if working_directory.drive:
            drive_letter = working_directory.drive[0].lower()
            working_directory = pathlib.Path(f'/{drive_letter}', *working_directory.parts[1:])
        working_directory = working_directory.as_posix()
        core.get_model_path().append_directory(working_directory)

        if constants.DEBUG:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )

        app = bloom_app.Bloom(options.map_path)
        app.run()
    except Exception as error:
        print(f'Error running application: {error}')
