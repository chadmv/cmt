import math
import numpy as np
from scipy.linalg import lu_factor, lu_solve, solve

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import cmt.shortcuts as shortcuts


def retarget(source, target, shapes, eps=1.0):
    source_points = get_points(source)
    target_points = get_points(target)
    distances = [
        [sp1.distanceTo(sp2) for sp1 in source_points] for sp2 in source_points
    ]
    max_distance = max([max(d) for d in distances])

    for shape in shapes:
        points = get_points(shape)
        for i in range(len(points)):
            shape_distances = [points[i].distanceTo(sp) for sp in source_points]
            max_d = max(shape_distances)
            if max_d > max_distance:
                max_distance = max_d

    distances = [[rbf(d / max_distance, eps) for d in d1] for d1 in distances]
    # print(distances)
    # distances = [[d for d in d1] for d1 in distances]

    a = np.array(distances)
    # print("a = {}".format(a))

    b = np.array([[tp.x, tp.y, tp.z] for tp in target_points])
    # print("b = {}".format(b))

    x = solve(a, b)
    # print("x = {}".format(x))

    for shape in shapes:
        points = get_points(shape)
        for i in range(len(points)):
            distances = [
                rbf(points[i].distanceTo(sp) / max_distance, eps)
                for sp in source_points
            ]
            # print(distances)
            d = np.array(distances)
            result = np.matmul(d, x)
            points[i] = OpenMaya.MPoint(*result)

        dupe = cmds.duplicate(shape, name="{}_{}".format(shape, eps))[0]
        set_points(dupe, points)
        cmds.delete(cmds.parentConstraint(target, dupe))


def rbf(v, eps=1.0):
    return v
    # return math.exp(-(v / eps) ** 2)


def get_points(mesh):
    path = shortcuts.get_dag_path2(shortcuts.get_shape(mesh))
    mesh_fn = OpenMaya.MFnMesh(path)
    return mesh_fn.getPoints()


def set_points(mesh, points):
    path = shortcuts.get_dag_path2(shortcuts.get_shape(mesh))
    mesh_fn = OpenMaya.MFnMesh(path)
    mesh_fn.setPoints(points)
