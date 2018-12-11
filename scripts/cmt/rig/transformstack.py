from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import re

import maya.cmds as cmds

# The message attribute specifying which nodes are part of a transform stack.
STACK_ATTRIBUTE = "cmt_transformStack"

logger = logging.getLogger(__name__)


def create_transform_stack(node, suffixes=None):
    """Creates a transform stack above the given node.

    Any previous transform stack will be deleted.

    :param node: Node to parent into a transform stack.
    :param suffixes: List of suffixes to add to the created transforms
    :return: A list of the transform nodes created starting from top to bottom.
    """
    previous_parent = get_stack_parent(node)
    delete_stack(node)

    stack_transforms = []
    for i, suffix in enumerate(suffixes):
        name = "{}{}".format(node, suffix)
        transform = cmds.createNode("transform", name=name)
        stack_transforms.append(transform)
        cmds.addAttr(transform, ln=STACK_ATTRIBUTE, at="message")
        cmds.connectAttr(
            "{}.message".format(node), "{}.{}".format(transform, STACK_ATTRIBUTE)
        )
        cmds.delete(cmds.parentConstraint(node, transform))
        if previous_parent:
            cmds.parent(transform, previous_parent)
        previous_parent = transform
    cmds.parent(node, previous_parent)
    stack_transforms.append(node)
    logger.info("Created transform stack {}".format("|".join(stack_transforms)))
    return stack_transforms


def delete_stack(node):
    """Delete the transforms of the stack.

    :param node: Stack leaf.
    """
    stack = get_stack(node)
    if len(stack) <= 1:
        return
    parent = get_stack_parent(node)
    if parent:
        cmds.parent(node, parent)
    else:
        cmds.parent(node, world=True)
    cmds.delete(stack[:-1])


def get_stack(node):
    """Get the transforms in the transform stack

    :param node: Stack leaf transform
    :return: List of transforms
    """
    stack = [node]
    parent = cmds.listRelatives(node, parent=True, path=True)
    if parent:
        parent = parent[0]
    while _is_transform_stack_node(parent):
        stack.insert(0, parent)
        parent = cmds.listRelatives(parent, parent=True, path=True)
        if parent:
            parent = parent[0]
    return stack


def _is_transform_stack_node(node):
    """Tests if the given node is part of a transform stack.

    :param node: Node to test.
    :return: True or False
    """
    if not node:
        return False
    return cmds.objExists("{}.{}".format(node, STACK_ATTRIBUTE))


def get_stack_count(node):
    """Get the number of transforms in the stack.

    :param node: Node to query.
    :return: The number of transforms in the stack.
    """
    return len(get_stack(node))


def get_stack_parent(node):
    """Get the parent of the transform stack belonging to the given node.

    :param node: Node to query.
    :return: The parent node or None if there is no parent.
    """
    stack = get_stack(node)
    parent = cmds.listRelatives(stack[0], parent=True, path=True)
    return parent[0] if parent else None
