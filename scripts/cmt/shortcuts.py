"""Contains commonly used functions and classes shared by many modules in cmt.
"""
import os
import re
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

import logging
logger = logging.getLogger(__name__)


def get_mobject(node):
    """Get the MObject of the given node.

    :param node: Node name
    :return: Node MObject
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(node)
    mobject = OpenMaya.MObject()
    selection_list.getDependNode(0, mobject)
    return mobject


def get_dag_path(node):
    """Get the MDagPath of the given node.

    :param node: Node name
    :return: Node MDagPath
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(node)
    path = OpenMaya.MDagPath()
    selection_list.getDagPath(0, path)
    return path


def get_shape(node, intermediate=False):
    """Get the shape node of a tranform

    This is useful if you don't want to have to check if a node is a shape node
    or transform.  You can pass in a shape node or transform and the function
    will return the shape node.

    :param node:  node The name of the node.
    :param intermediate:  intermediate True to get the intermediate shape
    :return: The name of the shape node.
    """
    if cmds.nodeType(node) == 'transform':
        shapes = cmds.listRelatives(node, shapes=True, path=True)
        if not shapes:
            shapes = []
        for shape in shapes:
            is_intermediate = cmds.getAttr('%s.intermediateObject' % shape)
            if intermediate and is_intermediate and cmds.listConnections(shape, source=False):
                return shape
            elif not intermediate and not is_intermediate:
                return shape
        if shapes:
            return shapes[0]
    elif cmds.nodeType(node) in ['mesh', 'nurbsCurve', 'nurbsSurface']:
        is_intermediate = cmds.getAttr('%s.intermediateObject' % node)
        if is_intermediate and not intermediate:
            node = cmds.listRelatives(node, parent=True, path=True)[0]
            return get_shape(node)
        else:
            return node
    return None


def get_node_in_namespace_hierarchy(node, namespace=None, shape=False):
    """Searches a namespace and all nested namespaces for the given node.

    :param node: Name of the node.
    :param namespace: Root namespace
    :param shape: True to get the shape node, False to get the transform.
    :return: The node in the proper namespace.
    """
    if shape and node and cmds.objExists(node):
        node = get_shape(node)

    if node and cmds.objExists(node):
        return node

    if node and namespace:
        # See if it exists in the namespace or any child namespaces
        namespaces = [namespace.replace(':', ''),]
        namespaces += cmds.namespaceInfo(namespace, r=True, lon=True) or []
        for namespace in namespaces:
            namespaced_node = '{0}:{1}'.format(namespace, node)
            if shape:
                namespaced_node = get_shape(namespaced_node)
            if namespaced_node and cmds.objExists(namespaced_node):
                return namespaced_node
    return None


def get_namespace_from_name(name):
    """Gets the namespace from the given name.

    >>> print get_namespace_from_name('BOB:character')
    BOB:
    >>> print get_namespace_from_name('YEP:BOB:character')
    YEP:BOB:

    :param name: String to extract the namespace from.
    :return: The extracted namespace
    """
    namespace = re.match('[_0-9a-zA-Z]+(?=:)(:[_0-9a-zA-Z]+(?=:))*', name)
    if namespace:
        namespace = '%s:' % str(namespace.group(0))
    else:
        namespace = ''
    return namespace


def remove_namespace_from_name(name):
    """Removes the namespace from the given name

    >>> print remove_namespace_from_name('character')
    character
    >>> print remove_namespace_from_name('BOB:character')
    character
    >>> print remove_namespace_from_name('YEP:BOB:character')
    character

    :param name: The name with the namespace
    :return: The name without the namesapce
    """
    namespace = get_namespace_from_name(name)
    if namespace:
        return re.sub('^{0}'.format(namespace), '', name)
    return name


class BaseTreeNode(object):
    """Base tree node that contains hierarchical functionality for use in a QAbstractItemModel"""

    def __init__(self, parent=None):
        self.children = []
        self._parent = parent

        if parent is not None:
            parent.add_child(self)

    def add_child(self, child):
        """Add a child to the node.

        @param child: Child node to add."""
        if child not in self.children:
            self.children.append(child)

    def remove(self):
        """Remove this node and all its children from the tree."""
        if self._parent:
            row = self.row()
            self._parent.children.pop(row)
            self._parent = None
        for child in self.children:
            child.remove()

    def child(self, row):
        """Get the child at the specified index.

        @param row: The child index.
        @return The tree node at the given index or None if the index was out of bounds."""
        try:
            return self.children[row]
        except IndexError:
            return None

    def child_count(self):
        """Get the number of children in the node"""
        return len(self.children)

    def parent(self):
        """Get the parent of node"""
        return self._parent

    def row(self):
        """Get the index of the node relative to the parent"""
        if self._parent is not None:
            return self._parent.children.index(self)
        return 0

    def data(self, column):
        """Get the table display data"""
        return ''


def get_icon_path(name):
    """Get the path of the given icon name.

    :param name: Name of an icon in the icons directory.
    :return: The full path to the icon or None if it does not exist.
    """
    icon_directory = os.path.join(os.path.dirname(__file__), '..', '..', 'icons')
    image_extensions = ['png', 'svg', 'jpg', 'jpeg']
    for root, dirs, files in os.walk(icon_directory):
        for ext in image_extensions:
            full_path = os.path.join(root, '{0}.{1}'.format(name, ext))
            if os.path.exists(full_path):
                return os.path.normpath(full_path)
    return None


def duplicate_chain(start, end, prefix='', suffix='', search_for='', replace_with=''):
    """ Duplicates the transform chain starting at start and ending at end.

    :param start: The start transform.
    :param end: The end transform.
    :return: A list of the duplicated joints, a list of the original joints that were duplicated
    """
    joint = end
    joints = []
    original_joints = []
    while joint:
        name = '{0}{1}{2}'.format(prefix, joint, suffix)
        if search_for or replace_with:
            name = name.replace(search_for, replace_with)
        original_joints.append(joint)
        duplicate_joint = cmds.duplicate(joint, name=name, parentOnly=True)[0]
        if joints:
            cmds.parent(joints[-1], duplicate_joint)
        joints.append(duplicate_joint)
        if joint == start:
            break
        joint = cmds.listRelatives(joint, parent=True, path=True)
        if joint:
            joint = joint[0]
        else:
            raise RuntimeError('{0} is not a descendant of {1}'.format(end, start))
    joints.reverse()
    original_joints.reverse()
    return joints, original_joints

