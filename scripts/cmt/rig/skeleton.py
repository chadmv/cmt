"""This module contains methods to manipulate and serialize skeletons.

Example usage:
See test_skeleton.py

import cmt.rig.skeleton as skeleton
skeleton.dump('root_joint', json_file)
cmds.file(new=True, f=True)
skeleton.load(json_file)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from six import string_types

import math
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import json
import logging

import cmt.shortcuts as shortcuts
from cmt.shortcuts import distance, vector_to

logger = logging.getLogger(__name__)

ATTRIBUTES = [
    "translate",
    "rotate",
    "scale",
    "jointOrient",
    "offsetParentMatrix",
    "radius",
    "rotateOrder",
    "rotateAxis",
    "side",
    "type",
    "otherType",
    "jointTypeX",
    "jointTypeY",
    "jointTypeZ",
]

EXTENSION = ".skel"


def dump(root=None, file_path=None):
    """Dump the hierarchy data starting at root to disk.

    :param root: Root nodes of the hierarchy.
    :param file_path: Export json path.
    :return: The exported file path.
    """
    if root is None:
        root = cmds.ls(sl=True) or []
        if not root:
            return
    if isinstance(root, string_types):
        root = [root]

    if file_path is None:
        file_path = cmds.fileDialog2(
            fileFilter="Skeleton Files (*{})".format(EXTENSION),
            dialogStyle=2,
            caption="Export Skeleton",
            fileMode=0,
            returnFilter=False,
        )
        if not file_path:
            return
        file_path = file_path[0]
    data = dumps(root)
    with open(file_path, "w") as fh:
        json.dump(data, fh, indent=4)
    logger.info("Exported skeleton to %s", file_path)
    return file_path


def dumps(root):
    """Get the serializable form of the joint/transform hierarchy.

    :param root: The root node of the hierarchy to export.
    :return: A list of transform/joint data in depth first order.
    """
    if isinstance(root, string_types):
        root = [root]
    data = []
    for node in root:
        joint_data = get_joint_data(node)
        if not joint_data:
            continue
        data.append(joint_data)

        # Recurse down to all the children
        children = cmds.listRelatives(node, children=True, path=True) or []
        for child in children:
            data += dumps(child)
    return data


def get_joint_data(node):
    """Get the serializable data of a node.

    :param node: Joint or transform name.
    :return: Data dictionary.
    """
    node_type = cmds.nodeType(node)
    shapes = cmds.listRelatives(node, children=True, shapes=True)
    if node_type not in ["joint", "transform"] or (shapes and node_type == "transform"):
        # Skip nodes that are not joints or transforms or if there are shapes below.
        return None

    parent = cmds.listRelatives(node, parent=True)
    parent = parent[0] if parent else None
    joint_data = {"nodeType": node_type, "name": node, "parent": parent}
    for attr in ATTRIBUTES:
        attribute = "{}.{}".format(node, attr)
        if not cmds.objExists(attribute):
            continue
        value = cmds.getAttr(attribute)
        if isinstance(value, list) and isinstance(value[0], tuple):
            value = list(value[0])
        joint_data[attr] = value
    return joint_data


def load(file_path=None):
    """Load a skeleton from disk.

    :param file_path: Json file on disk.
    :return: The hierarchy data loaded from disk.
    """
    if file_path is None:
        file_path = cmds.fileDialog2(
            fileFilter="Skeleton Files (*{})".format(EXTENSION),
            dialogStyle=2,
            caption="Import Skeleton",
            fileMode=1,
            returnFilter=False,
        )
        if not file_path:
            return
        file_path = file_path[0]
    with open(file_path, "r") as fh:
        data = json.load(fh)
    create(data)
    return data


def create(data_list):
    """Create the transform hierarchy.

    :param data_list: The list of transform/joint data generated from dumps.
    """
    for data in data_list:
        node = data["name"]
        if not cmds.objExists(node):
            node = cmds.createNode(data["nodeType"], name=node)
        parent = data["parent"]
        if parent and cmds.objExists(parent):
            try:
                cmds.parent(node, parent)
            except RuntimeError:
                pass
        for attr in ATTRIBUTES:
            attribute = "{}.{}".format(node, attr)
            if not cmds.objExists(attribute):
                continue
            value = data.get(attr)
            if value is None:
                continue
            if isinstance(value, string_types):
                cmds.setAttr(attribute, value, type="string")
            elif isinstance(value, list):
                if len(value) == 16:
                    cmds.setAttr(attribute, *value, type="matrix")
                else:
                    cmds.setAttr(attribute, *value)
            else:
                cmds.setAttr(attribute, value)


def mirror(joint, search_for, replace_with):
    joints = [joint] + (cmds.listRelatives(joint, ad=True, path=True) or [])
    for joint in joints:
        mirrored_joint = joint.replace(search_for, replace_with)
        if cmds.objExists(mirrored_joint):
            translate = list(cmds.getAttr("{0}.t".format(joint))[0])
            parent = cmds.listRelatives(joint, parent=True, path=True)
            if parent and search_for not in parent[0]:
                translate[2] *= -1.0
            else:
                translate = [x * -1.0 for x in translate]
            cmds.setAttr("{0}.t".format(mirrored_joint), *translate)

            rotate = cmds.getAttr("{0}.r".format(joint))[0]
            cmds.setAttr("{0}.r".format(mirrored_joint), *rotate)

            scale = cmds.getAttr("{0}.s".format(joint))[0]
            cmds.setAttr("{0}.s".format(mirrored_joint), *scale)


def insert_joints(joints=None, joint_count=1):
    """Inserts joints evenly spaced along a bone.

    :param joints: List of joints to insert child joints to.
    :param joint_count: Number of joints to insert.
    :return: List of joints created.
    """

    if joints is None:
        joints = cmds.ls(sl=True, type="joint")
        if not joints:
            raise RuntimeError("No joint selected")

    if joint_count < 1:
        raise RuntimeError("Must insert at least 1 joint.")

    result = []
    for joint in joints:
        children = cmds.listRelatives(joint, children=True, type="joint")
        if not children:
            raise RuntimeError(
                "Joint {} needs a child in order to insert joints".format(joint)
            )

        name = joint
        end_joint = children[0]
        d = distance(joint, children[0])
        increment = d / (joint_count + 1)
        direction = vector_to(joint, end_joint)
        direction.normalize()
        direction *= increment

        for i in range(joint_count):
            position = cmds.xform(joint, query=True, worldSpace=True, translation=True)
            position = OpenMaya.MPoint(position[0], position[1], position[2])
            position += direction
            joint = cmds.insertJoint(joint)
            joint = cmds.rename(joint, ("{}_seg#".format(name)))
            cmds.joint(
                joint,
                edit=True,
                component=True,
                position=(position.x, position.y, position.z),
            )
            result.append(joint)
    return result


def tpose_arm(shoulder, elbow, wrist, hand_aim=None, hand_up=None, length_scale=1.0):
    """Put the given shoulder, elbow, and wrist joints in a tpose.

    This function assumes the character is facing forward z.

    :param shoulder: Shoulder joint
    :param elbow: Elbow joint
    :param wrist: Wrist joint
    :param hand_aim: Local hand aim vector (Default [+-]1.0, 0.0, 0.0)
    :param hand_up: Local hand up vector (Default 0.0, 0.0, [+-]1.0)
    """
    a = OpenMaya.MVector(*cmds.xform(shoulder, q=True, ws=True, t=True))
    b = OpenMaya.MVector(*cmds.xform(elbow, q=True, ws=True, t=True))
    c = OpenMaya.MVector(*cmds.xform(wrist, q=True, ws=True, t=True))
    direction = 1.0 if b.x > a.x else -1.0

    t = OpenMaya.MVector(a)
    t.x += ((b - a).length() + (c - b).length()) * direction * length_scale
    pv = (a + t) * 0.5
    pv.z -= 100.0
    path_shoulder = shortcuts.get_dag_path2(shoulder)
    path_elbow = shortcuts.get_dag_path2(elbow)

    a_gr = OpenMaya.MTransformationMatrix(path_shoulder.inclusiveMatrix()).rotation(
        asQuaternion=True
    )
    b_gr = OpenMaya.MTransformationMatrix(path_elbow.inclusiveMatrix()).rotation(
        asQuaternion=True
    )
    ac = (c - a).normal()
    d = (b - (a + (ac * ((b - a) * ac)))).normal()

    a_gr, b_gr = two_bone_ik(a, b, c, d, t, pv, a_gr, b_gr)

    fn_shoulder = OpenMaya.MFnTransform(path_shoulder)
    fn_shoulder.setRotation(a_gr, OpenMaya.MSpace.kWorld)
    fn_elbow = OpenMaya.MFnTransform(path_elbow)
    fn_elbow.setRotation(b_gr, OpenMaya.MSpace.kWorld)

    if hand_aim is None:
        hand_aim = (1.0 * direction, 0.0, 0.0)
    if hand_up is None:
        hand_up = (0.0, 0.0, 1.0 * direction)
    aim_loc = cmds.spaceLocator()[0]
    t.x += direction
    cmds.xform(aim_loc, ws=True, t=(t.x, t.y, t.z))
    cmds.delete(
        cmds.aimConstraint(
            aim_loc,
            wrist,
            aimVector=hand_aim,
            upVector=hand_up,
            worldUpType="vector",
            worldUpVector=[0.0, 0.0, -1.0],
        )
    )
    cmds.delete(aim_loc)


def two_bone_ik(a, b, c, d, t, pv, a_gr, b_gr):
    eps = 0.001
    lab = (b - a).length()
    lcb = (b - c).length()
    lat = clamp((t - a).length(), eps, lab + lcb - eps)

    # Get current interior angles of start and mid
    ac_ab_0 = math.acos(clamp((c - a).normal() * (b - a).normal(), -1.0, 1.0))
    ba_bc_0 = math.acos(clamp((a - b).normal() * (c - b).normal(), -1.0, 1.0))
    ac_at_0 = math.acos(clamp((c - a).normal() * (t - a).normal(), -1.0, 1.0))

    # Get desired interior angles
    ac_ab_1 = math.acos(
        clamp((lcb * lcb - lab * lab - lat * lat) / (-2.0 * lab * lat), -1.0, 1.0)
    )
    ba_bc_1 = math.acos(
        clamp((lat * lat - lab * lab - lcb * lcb) / (-2.0 * lab * lcb), -1.0, 1.0)
    )
    axis0 = ((c - a) ^ d).normal()
    axis1 = ((c - a) ^ (t - a)).normal()

    r0 = OpenMaya.MQuaternion(ac_ab_1 - ac_ab_0, axis0)
    r1 = OpenMaya.MQuaternion(ba_bc_1 - ba_bc_0, axis0)
    r2 = OpenMaya.MQuaternion(ac_at_0, axis1)

    # Pole vector rotation
    # Determine the rotation used to rotate the normal of the triangle formed by
    # a.b.c post r0*r2 rotation to the normal of the triangle formed by triangle a.pv.t
    n1 = ((c - a) ^ (b - a)).normal().rotateBy(r0).rotateBy(r2)
    n2 = ((t - a) ^ (pv - a)).normal()
    r3 = n1.rotateTo(n2)

    a_gr *= r0 * r2 * r3
    b_gr *= r1
    # Since we are calculating in world space, apply the start rotations to the mid
    b_gr *= r0 * r2 * r3
    return a_gr, b_gr


def clamp(in_value, min_value, max_value):
    return max(min(in_value, max_value), min_value)
