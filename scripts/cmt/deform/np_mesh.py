"""Efficient mesh processing using numpy"""

import numpy as np
import json
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts


class Mesh(object):
    @classmethod
    def from_obj(cls, file_path):
        with open(file_path, "r") as fh:
            lines = fh.readlines()

        points = []
        read_vertices = False
        for line in lines:
            if line.startswith("v "):
                read_vertices = True
                v = line.split()[1:]
                points.append([float(v[0]), float(v[1]), float(v[2])])
            elif read_vertices:
                break
        points = np.array(points)
        return Mesh(points)

    @classmethod
    def from_maya_mesh(cls, mesh):

        points = shortcuts.get_points(mesh)
        points = np.array([[p.x, p.y, p.z] for p in points])
        return Mesh(points)

    def __init__(self, points):
        self.points = points

    def mask_points(self, base, mask):
        points = base.points + ((self.points - base.points).T * mask.values).T
        return Mesh(points)

    def separate_axis(
        self,
        base,
        x_axis=1.0,
        y_axis=1.0,
        z_axis=1.0,
        x_direction=0,
        y_direction=0,
        z_direction=0,
    ):
        axis_scale = np.array([x_axis, y_axis, z_axis])
        deltas = (self.points - base.points) * axis_scale

        isolate_vector_direction(deltas, x_direction, 0)
        isolate_vector_direction(deltas, y_direction, 1)
        isolate_vector_direction(deltas, z_direction, 2)

        points = base.points + deltas
        return Mesh(points)

    def to_maya_mesh(self, mesh):

        points = OpenMaya.MPointArray()
        for p in self.points:
            points.append(OpenMaya.MPoint(p[0], p[1], p[2]))
        shortcuts.set_points(mesh, points)


def isolate_vector_direction(deltas, direction, axis):
    if direction < 0:
        deltas[:, :][deltas[:, axis] > 0] = 0
    elif direction > 0:
        deltas[:, :][deltas[:, axis] < 0] = 0
    return deltas


class Mask(object):
    """1D array of float values."""

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, "r") as fh:
            data = json.load(fh)
        values = np.array(data)
        return Mask(values)

    def __init__(self, values):
        self.values = values
