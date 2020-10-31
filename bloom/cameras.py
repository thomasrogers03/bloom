# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from typing import NamedTuple

from panda3d import core

from . import constants


class Camera(NamedTuple):
    camera: core.NodePath
    camera_node: core.Camera
    lens: core.Lens
    display_region: core.DisplayRegion


class Cameras:

    def __init__(
        self,
        window: core.GraphicsWindow,
        render: core.NodePath,
        render_2d: core.NodePath,
        scene: core.NodePath,
        default_camera: Camera
    ):
        self._window = window
        self._render = render
        self._render_2d = render_2d
        self._scene = scene
        self._builder_2d: core.NodePath = self._scene.attach_new_node('builder_2d')
        self._builder: core.NodePath = self._builder_2d.attach_new_node('builder_3d')
        self._default_camera = default_camera
        self._cameras: typing.Dict[str, Camera] = {'default': self._default_camera}

        self._default_camera.camera.reparent_to(self._builder)
        self._default_camera.camera.node().set_camera_mask(constants.SCENE_3D)
        self._default_camera.lens.set_fov(90)
        self._default_camera.lens.set_near_far(1, 1 << 17)


        builder_camera: core.NodePath = self._builder.attach_new_node(
            'builder_camera'
        )
        builder_camera.hide(constants.SCENE_3D)
        builder_camera.set_depth_write(False)
        builder_camera.set_depth_test(False)
        builder_camera.set_bin('fixed', 1000)
        builder_camera.set_scale(500)

    def __getitem__(self, key):
        return self._cameras[key]

    @property
    def render(self):
        return self._render

    @property
    def render_2d(self):
        return self._render_2d

    @property
    def scene(self):
        return self._scene

    @property
    def builder_2d(self):
        return self._builder_2d

    @property
    def builder(self):
        return self._builder

    def get_builder_position(self) -> core.Point3:
        return self._builder.get_pos(self._scene)

    def get_builder_2d_position(self) -> core.Point3:
        return self._builder_2d.get_pos(self._scene)

    def make_gui_camera(self, name: str) -> Camera:
        lens = core.OrthographicLens()
        lens.set_film_size(1, 1)
        lens.set_near_far(-1, 1)

        camera_node = core.Camera(f'{name}_camera')
        camera_node.set_scene(self._scene)
        camera_node.set_lens(lens)
        camera_node.set_camera_mask(constants.SCENE_2D)
        camera: core.NodePath = self.render.attach_new_node(camera_node)

        display_region: core.DisplayRegion = self._window.make_display_region(
            0, 1, 0, 1
        )
        display_region.set_camera(camera)
        display_region.set_sort(1000)
        display_region.set_active(False)

        camera = Camera(
            camera,
            camera_node,
            lens,
            display_region
        )
        self._cameras[name] = camera

        return camera

    def make_2d_camera(self, name: str) -> Camera:
        lens = core.OrthographicLens()
        film_size = self._default_camera.lens.get_film_size()
        lens.set_film_size(film_size.x * 1280, film_size.y * 1280)
        lens.set_near_far(16, 1_024_000)

        camera_node = core.Camera(f'{name}_camera')
        camera_node.set_scene(self._scene)
        camera_node.set_lens(lens)
        camera_node.set_camera_mask(constants.SCENE_2D)
        camera: core.NodePath = self.render.attach_new_node(camera_node)
        camera.set_scale(32)
        camera.set_hpr(180, -90, 0)
        camera.set_z(512_000)

        display_region: core.DisplayRegion = self._window.make_display_region(
            0, 1, 0, 1
        )
        display_region.set_camera(camera)
        display_region.set_sort(1000)
        display_region.set_active(False)

        camera = Camera(
            camera,
            camera_node,
            lens,
            display_region
        )
        self._cameras[name] = camera

        return camera

    def make_3d_camera(self, name: str):
        pass
