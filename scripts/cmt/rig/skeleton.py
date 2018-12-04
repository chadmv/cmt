"""This module contains methods to manipulate and serialize skeletons.

Example usage:
See test_skeleton.py

import cmt.rig.skeleton as skeleton
skeleton.dump('skeleton_grp', json_file)
cmds.file(new=True, f=True)
skeleton.load(json_file)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from six import string_types

import maya.cmds as cmds
import json
import logging

logger = logging.getLogger(__name__)

ATTRIBUTES = [
    "translate",
    "rotate",
    "scale",
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
        if isinstance(value, list):
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
            print(parent)
            cmds.parent(node, parent)
        for attr in ATTRIBUTES:
            attribute = "{}.{}".format(node, attr)
            if not cmds.objExists(attribute):
                continue
            value = data[attr]
            print(attr, value)
            if isinstance(value, string_types):
                cmds.setAttr(attribute, value, type="string")
            elif isinstance(value, list):
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
