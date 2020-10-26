# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

def to_degrees(build_angle: int) -> float:
    return (180 * build_angle) / 1024 - 90


def to_build_angle(degrees: float) -> int:
    return int(((degrees + 90) * 1024) / 180)


def to_height(build_height: int) -> float:
    return build_height / float(1 << 4)


def to_build_height(height: float) -> int:
    return int(height * (1 << 4))


def to_heinum(build_height: int) -> float:
    return build_height / float(1 << 12)


def to_build_heinum(height: float) -> int:
    return int(height * (1 << 12))


def to_sprite_repeat(build_sprite_repeat: int) -> float:
    return build_sprite_repeat / 4


def to_build_sprite_repeat(sprite_repeat: float) -> int:
    return int(sprite_repeat * 4)


def to_repeat_x(build_repeat_x: int) -> float:
    return build_repeat_x * 8


def to_build_repeat_x(repeat_x: float) -> int:
    return int(repeat_x / 8)


def to_repeat_y(build_repeat_y: int) -> float:
    return build_repeat_y / 128


def to_build_repeat_y(repeat_y: float) -> int:
    return int(repeat_y * 128)


def to_panning_x(panning_x: int) -> float:
    return float(panning_x)


def to_build_panning_x(panning_x: float) -> int:
    return int(panning_x)


def to_panning_y(build_panning_y: int) -> float:
    return build_panning_y / 2


def to_build_panning_y(build_panning_y: float) -> int:
    return int(build_panning_y * 2)


def snap_to_grid(value: float, grid_size: float):
    return round(value / grid_size) * grid_size
