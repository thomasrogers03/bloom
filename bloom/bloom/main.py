# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import sys

from direct.gui import DirectGuiGlobals
from panda3d import core

from . import bloom_app, parameters


def main():
    try:
        options = parameters.get_parameters()
        core.load_prc_file_data('', 'sync-video #f')
        core.load_prc_file_data('', 'show-frame-rate-meter #t')
        core.load_prc_file_data('', 'disable-message-loop #t')
        if options.direct_tools:
            raise NotImplementedError()
            # core.load_prc_file_data('', 'want-tk #t')
            # core.load_prc_file_data('', 'want-directtools #t')

        DirectGuiGlobals.WHEELUP = core.PGButton.get_release_prefix() + core.MouseButton.wheel_up().get_name() + '-'
        DirectGuiGlobals.WHEELDOWN = core.PGButton.get_release_prefix() + core.MouseButton.wheel_down().get_name() + '-'

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )

        app = bloom_app.Bloom(options.map_path)
        app.run()
    except Exception as error:
        print(f'Error running application: {error}')