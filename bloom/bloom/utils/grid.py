# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core


def make_grid(scene: core.NodePath, name: str, thickness: float, line_count: int, colour: core.Vec4):
    grid: core.NodePath = scene.attach_new_node(name)

    cell_segments = core.LineSegs()
    cell_segments.set_thickness(thickness)
    cell_segments.set_color(colour)

    cell_segments.draw_to(0, 0, 0)
    cell_segments.draw_to(0, 1, 0)
    cell_segments.draw_to(1, 1, 0)
    cell_segments.draw_to(1, 0, 0)
    cell_segments.draw_to(0, 0, 0)

    cell_node = cell_segments.create('cell')
    cell: core.NodePath = grid.attach_new_node(cell_node)

    half_line_count = int(line_count / 2)
    for x in range(line_count):
        for y in range(line_count):
            new_cell: core.NodePath = grid.attach_new_node(f'{x}_{y}')
            cell.copy_to(new_cell)
            cell.set_pos(x - half_line_count, y - half_line_count, 0)

    grid.flatten_medium()
    grid.set_transparency(True)

    return grid
