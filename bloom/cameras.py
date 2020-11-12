# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
from typing import NamedTuple

from direct.showbase import Loader
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
        resource_loader: Loader.Loader,
        window: core.GraphicsWindow,
        render: core.NodePath,
        render_2d: core.NodePath,
        scene: core.NodePath,
        default_camera: Camera
    ):
        self._resource_loader = resource_loader
        self._window = window
        self._render = render
        self._render_2d = render_2d
        self._scene = scene
        self._builder_2d: core.NodePath = self._scene.attach_new_node('builder_2d')
        self._builder: core.NodePath = self._builder_2d.attach_new_node('builder_3d')
        self._default_camera = default_camera
        self._cameras: typing.Dict[str, Camera] = {'default': self._default_camera}

        builder_arrow_segments = core.LineSegs('builder_2d_arrow')
        builder_arrow_segments.set_thickness(6)
        builder_arrow_segments.set_color(0.85, 0.85, 0.85, 1)
        builder_arrow_segments.draw_to(0, -512, 0)
        builder_arrow_segments.draw_to(0, 512, 0)
        builder_arrow_segments.draw_to(-512, 0, 0)
        builder_arrow_segments.draw_to(0, 512, 0)
        builder_arrow_segments.draw_to(512, 0, 0)
        builder_arrow: core.NodePath = self._builder.attach_new_node(builder_arrow_segments.create())
        builder_arrow.set_depth_write(False)
        builder_arrow.set_depth_test(False)
        builder_arrow.set_bin('fixed', constants.FRONT_MOST)
        builder_arrow.hide(constants.SCENE_3D)

        self._default_camera.camera.reparent_to(self._builder)
        self._default_camera.camera.node().set_camera_mask(constants.SCENE_3D)
        self._default_camera.lens.set_fov(90)
        self._default_camera.lens.set_near_far(10, constants.REALLY_BIG_NUMBER)


        builder_camera: core.NodePath = self._builder.attach_new_node(
            'builder_camera'
        )
        builder_camera.hide(constants.SCENE_3D)
        builder_camera.set_depth_write(False)
        builder_camera.set_depth_test(False)
        builder_camera.set_bin('fixed', constants.FRONT_MOST)
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

    def load_model_into_scene(self, path: str):
        model = self._resource_loader.load_model(path)
        model.reparent_to(self.scene)
        
        return model

    def get_builder_position(self) -> core.Point3:
        return self._builder.get_pos(self._scene)

    def get_builder_2d_position(self) -> core.Point3:
        return self._builder_2d.get_pos(self._scene)

    def make_gui_camera(self, name: str) -> Camera:
        if name in self._cameras:
            return self._cameras[name]

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
        display_region.set_sort(constants.FRONT_MOST)
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
        if name in self._cameras:
            return self._cameras[name]

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
        display_region.set_sort(constants.FRONT_MOST)
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
        if name in self._cameras:
            return self._cameras[name]

        raise NotImplementedError()

    def get_clipping_transform(self):
        position = self._builder_2d.get_pos()
        rotation = self._builder.get_h()

        builder_transform: core.TransformState = self._builder_2d.get_transform()
        builder_transform = builder_transform.get_inverse()
        rotation = core.Mat4.rotate_mat(
            -rotation,
            core.Vec3(0, 0, 1)
        )
        builder_matrix: core.Mat4 = builder_transform.get_mat() * rotation

        lens = self._default_camera.lens
        view = lens.get_view_mat()
        projection = lens.get_projection_mat()

        return builder_matrix * view * projection

    def pan_camera(self, delta: core.Vec2):
        heading = self._builder.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = -sin_theta * delta.y + cos_theta * delta.x
        y_direction = cos_theta * delta.y + sin_theta * delta.x

        self._builder_2d.set_x(
            self._builder_2d,
            x_direction * constants.TICK_SCALE
        )
        self._builder_2d.set_y(
            self._builder_2d,
            y_direction * constants.TICK_SCALE
        )

    def strafe_camera(self, delta: core.Vec2):
        delta *= 100

        heading = self._builder.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = cos_theta * delta.x
        y_direction = sin_theta * delta.x

        self._builder.set_z(
            self._builder.get_z() + delta.y * 512
        )

        self._builder_2d.set_x(
            self._builder_2d,
            x_direction * 512
        )
        self._builder_2d.set_y(
            self._builder_2d,
            y_direction * 512
        )

    def rotate_camera(self, delta: core.Vec2):
        hpr = self._builder.get_hpr()
        hpr = core.Vec3(hpr.x - delta.x * 90, hpr.y + delta.y * 90, 0)

        if hpr.y < -90:
            hpr.y = -90
        if hpr.y > 90:
            hpr.y = 90

        self._builder.set_hpr(hpr)

    def transform_to_camera_delta(self, mouse_delta: core.Vec2) -> core.Vec3:
        heading = self._builder.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))

        x_direction = sin_theta * mouse_delta.y + cos_theta * -mouse_delta.x
        y_direction = cos_theta * mouse_delta.y - sin_theta * -mouse_delta.x
        
        return core.Vec3(x_direction, y_direction, -mouse_delta.y)

    def transform_to_camera_delta_2d(self, mouse_delta: core.Vec2) -> core.Vec3:
        return core.Vec3(mouse_delta.x, mouse_delta.y, 0)
