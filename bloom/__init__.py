# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import os.path

try:
    import pkg_resources

    def find_resource(name: str):
        return pkg_resources.resource_filename(__name__, os.path.join('resources', name))

except ImportError:

    def find_resource(name: str):
        return os.path.join('bloom/resources', name)
