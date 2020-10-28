# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import sys

from direct.gui import DirectGuiGlobals
from panda3d import core

from . import bloom_app, parameters


def main():
    options = parameters.get_parameters()
    core.load_prc_file_data('', 'sync-video #f')
    core.load_prc_file_data('', 'show-frame-rate-meter #t')
    core.load_prc_file_data('', 'disable-message-loop #t')
    if options.direct_tools:
        raise NotImplementedError()
        # core.load_prc_file_data('', 'want-tk #t')
        # core.load_prc_file_data('', 'want-directtools #t')

    DirectGuiGlobals.WHEELUP = core.PGButton.getReleasePrefix() + core.MouseButton.wheelUp().getName() + '-'
    DirectGuiGlobals.WHEELDOWN = core.PGButton.getReleasePrefix() + core.MouseButton.wheelDown().getName() + '-'

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    app = bloom_app.Bloom(options.map_path)
    app.run()
