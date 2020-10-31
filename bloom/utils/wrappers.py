# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging


def error_wrapped(logger_name):
    logger = logging.getLogger(logger_name)

    def _with_logger(callback):
        def _wrapped(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception as error:
                logger.warn(f'Error running {callback}', exc_info=error)
        return _wrapped
    return _with_logger
