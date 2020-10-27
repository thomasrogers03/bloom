# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import sys

from panda3d import core

from . import bloom_app, parameters


def main():
    options = parameters.get_parameters()
    core.load_prc_file_data('', 'sync-video #f')
    core.load_prc_file_data('', 'show-frame-rate-meter #t')
    core.load_prc_file_data('', 'win-size 1800 800')

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    app = bloom_app.Bloom(options.map_path)
    app.run()
