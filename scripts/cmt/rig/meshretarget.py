"""Retarget meshes fit on a source mesh to a modified version of the source mesh.

Most of this was taken from http://mathlab.github.io/PyGeM/_modules/pygem/radial.html#RBF

Example Usage
=============

    retarget("source_body", "new_body", ["shirt", "pants"], rbf=RBF.linear)

"""
import math
import numpy as np
from scipy.spatial.distance import cdist

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import cmt.shortcuts as shortcuts


def retarget(source, target, shapes, rbf=None, radius=0.5, stride=1):
    """Run the mesh retarget.

    :param source: Source mesh
    :param target: Modified source mesh
    :param shapes: List of meshes to retarget
    :param rbf: One of the RBF functions. See class RBF
    :param radius: Smoothing parameter for the rbf
    :param stride: Vertex stride to sample on the source mesh.  Increase to speed up
    the calculation.
    """
    source_points = points_to_np_array(source, stride)
    target_points = points_to_np_array(target, stride)

    if rbf is None:
        rbf = RBF.linear
    # dist = get_distance_matrix(source_points, source_points, RBF.linear, 0)
    # max_distance = np.amax(dist)
    max_distance = 1.0
    weights = get_weight_matrix(source_points, target_points, rbf, radius, max_distance)

    for shape in shapes:
        points = points_to_np_array(shape)
        n_points = points.shape[0]
        dist = get_distance_matrix(points, source_points, rbf, radius, max_distance)
        identity = np.ones((n_points, 1))
        h = np.bmat([[dist, identity, points]])
        # h = dist
        deformed = np.asarray(np.dot(h, weights))
        points = [OpenMaya.MPoint(*p) for p in deformed]
        dupe = cmds.duplicate(
            shape, name="{}_{}_{}".format(shape, radius, rbf.__name__)
        )[0]
        set_points(dupe, points)
        cmds.delete(cmds.parentConstraint(target, dupe))


def points_to_np_array(mesh, stride=1):
    points = get_points(mesh)
    points = [p for p in points][::stride]
    points = np.array([[p.x, p.y, p.z] for p in points])
    return points


def get_points(mesh):
    path = shortcuts.get_dag_path2(shortcuts.get_shape(mesh))
    mesh_fn = OpenMaya.MFnMesh(path)
    return mesh_fn.getPoints()


def get_weight_matrix(sp, tp, rbf, radius, max_distance):
    """Get the weight matrix x in Ax=B

    :param sp: Source control point array
    :param tp: Target control point aray
    :param rbf: Rbf function from class RBF
    :param radius: Smoothing parameter
    :param max_distance: Max distance used to normalize distances

    :return: Weight matrix
    """
    identity = np.ones((sp.shape[0], 1))
    dist = get_distance_matrix(sp, sp, rbf, radius, max_distance)
    # Solve x for Ax=B
    dim = 3
    a = np.bmat(
        [
            [dist, identity, sp],
            [identity.T, np.zeros((1, 1)), np.zeros((1, dim))],
            [sp.T, np.zeros((dim, 1)), np.zeros((dim, dim))],
        ]
    )
    b = np.bmat([[tp], [np.zeros((1, dim))], [np.zeros((dim, dim))]])
    weights = np.linalg.solve(a, b)
    return weights


def get_distance_matrix(v1, v2, rbf, radius, max_distance=1.0):
    matrix = cdist(v1, v2, lambda x, y: rbf((x - y) / max_distance, radius))
    return matrix


def set_points(mesh, points):
    path = shortcuts.get_dag_path2(shortcuts.get_shape(mesh))
    mesh_fn = OpenMaya.MFnMesh(path)
    mesh_fn.setPoints(points)


class RBF(object):
    """Various RBF kernels"""

    @classmethod
    def linear(cls, vector, radius):
        norm = np.linalg.norm(vector)
        return norm

    @classmethod
    def gaussian(cls, vector, radius):
        norm = np.linalg.norm(vector)
        result = np.exp(-(norm * norm) / (radius * radius))
        return result

    @classmethod
    def thin_plate(cls, vector, radius):
        norm = np.linalg.norm(vector / radius)
        result = norm * norm
        if norm > 0:
            result *= np.log(norm)
        return result

    @classmethod
    def multi_quadratic_biharmonic(cls, vector, radius):
        norm = np.linalg.norm(vector)
        result = np.sqrt((norm * norm) + (radius * radius))
        return result

    @classmethod
    def inv_multi_quadratic_biharmonic(cls, vector, radius):
        norm = np.linalg.norm(vector)
        result = 1.0 / (np.sqrt((norm * norm) + (radius * radius)))
        return result

    @classmethod
    def beckert_wendland_c2_basis(cls, vector, radius):
        norm = np.linalg.norm(vector)
        arg = norm / radius
        first = 0
        if (1 - arg) > 0:
            first = np.power((1 - arg), 4)
        second = (4 * arg) + 1
        result = first * second
        return result
