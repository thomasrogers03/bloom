# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import sys

from panda3d import core

from . import bloom_app

if __name__ == '__main__':
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

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = None
    app = bloom_app.Bloom(path)
    app.run()
