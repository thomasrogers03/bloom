# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0



from panda3d import core

from . import navigation_mode_3d


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        camera: core.NodePath,
        lens: core.Lens,
        *args,
        **kwargs
    ):
        super().__init__(camera, lens, *args, **kwargs)
