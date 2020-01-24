"""Contains commonly used functions and classes shared by many modules in cmt."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import re

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.api.OpenMaya as OpenMaya2

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


def get_dag_path2(node):
    """Get the MDagPath of the given node.

    :param node: Node name
    :return: Node MDagPath
    """
    selection_list = OpenMaya2.MSelectionList()
    selection_list.add(node)
    return selection_list.getDagPath(0)


def get_shape(node, intermediate=False):
    """Get the shape node of a tranform

    This is useful if you don't want to have to check if a node is a shape node
    or transform.  You can pass in a shape node or transform and the function
    will return the shape node.

    :param node:  node The name of the node.
    :param intermediate:  intermediate True to get the intermediate shape
    :return: The name of the shape node.
    """
    if cmds.objectType(node, isAType="transform"):
        shapes = cmds.listRelatives(node, shapes=True, path=True)
        if not shapes:
            shapes = []
        for shape in shapes:
            is_intermediate = cmds.getAttr("{}.intermediateObject".format(shape))
            if (
                intermediate
                and is_intermediate
                and cmds.listConnections(shape, source=False)
            ):
                return shape
            elif not intermediate and not is_intermediate:
                return shape
        if shapes:
            return shapes[0]
    elif cmds.nodeType(node) in ["mesh", "nurbsCurve", "nurbsSurface"]:
        is_intermediate = cmds.getAttr("{}.intermediateObject".format(node))
        if is_intermediate and not intermediate:
            node = cmds.listRelatives(node, parent=True, path=True)[0]
            return get_shape(node)
        else:
            return node
    return None


def get_points(mesh):
    """Get the MPointArray of a mesh.

    :param mesh: Mesh name
    :return: MPointArray
    """
    mesh = get_shape(mesh)
    path = get_dag_path2(mesh)
    fn_mesh = OpenMaya2.MFnMesh(path)
    return fn_mesh.getPoints()


def set_points(mesh, points):
    """Set the MPointArray of a mesh.

    :param mesh: Mesh name
    :param points: MPointArray
    """
    mesh = get_shape(mesh)
    path = get_dag_path2(mesh)
    fn_mesh = OpenMaya2.MFnMesh(path)
    fn_mesh.setPoints(points)


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
        namespaces = [namespace.replace(":", "")]
        namespaces += cmds.namespaceInfo(namespace, r=True, lon=True) or []
        for namespace in namespaces:
            namespaced_node = "{0}:{1}".format(namespace, node)
            if shape:
                namespaced_node = get_shape(namespaced_node)
            if namespaced_node and cmds.objExists(namespaced_node):
                return namespaced_node
    return None


def get_namespace_from_name(name):
    """Gets the namespace from the given name.

    >>> print(get_namespace_from_name('BOB:character'))
    BOB:
    >>> print(get_namespace_from_name('YEP:BOB:character'))
    YEP:BOB:

    :param name: String to extract the namespace from.
    :return: The extracted namespace
    """
    namespace = re.match("[_0-9a-zA-Z]+(?=:)(:[_0-9a-zA-Z]+(?=:))*", name)
    if namespace:
        namespace = "%s:" % str(namespace.group(0))
    else:
        namespace = ""
    return namespace


def remove_namespace_from_name(name):
    """Removes the namespace from the given name

    >>> print(remove_namespace_from_name('character'))
    character
    >>> print(remove_namespace_from_name('BOB:character'))
    character
    >>> print(remove_namespace_from_name('YEP:BOB:character'))
    character

    :param name: The name with the namespace
    :return: The name without the namesapce
    """
    namespace = get_namespace_from_name(name)
    if namespace:
        return re.sub("^{0}".format(namespace), "", name)
    return name


class BaseTreeNode(object):
    """Base tree node that contains hierarchical functionality for use in a
    QAbstractItemModel"""

    def __init__(self, parent=None):
        self.children = []
        self._parent = parent

        if parent is not None:
            parent.add_child(self)

    def add_child(self, child):
        """Add a child to the node.

        :param child: Child node to add."""
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

        :param row: The child index.
        :return: The tree node at the given index or None if the index was out of
        bounds.
        """
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
        return ""


class SingletonWindowMixin(object):
    """Mixin to be used with a QWidget based window to only allow one instance of the window"""

    _window_instance = None

    @classmethod
    def show_window(cls):
        if not cls._window_instance:
            cls._window_instance = cls()
        cls._window_instance.show()
        cls._window_instance.raise_()
        cls._window_instance.activateWindow()

    def closeEvent(self, event):
        self._window_instance = None
        event.accept()


def get_icon_path(name):
    """Get the path of the given icon name.

    :param name: Name of an icon in the icons directory.
    :return: The full path to the icon or None if it does not exist.
    """
    icon_directory = os.path.join(os.path.dirname(__file__), "..", "..", "icons")
    image_extensions = ["png", "svg", "jpg", "jpeg"]
    for root, dirs, files in os.walk(icon_directory):
        for ext in image_extensions:
            full_path = os.path.join(root, "{0}.{1}".format(name, ext))
            if os.path.exists(full_path):
                return os.path.normpath(full_path)
    return None




_settings = None


def _get_settings():
    """Get the QSettings instance"""
    global _settings
    try:
        from PySide2.QtCore import QSettings
    except ImportError:
        from PySide.QtCore import QSettings
    if _settings is None:
        _settings = QSettings("Chad Vernon", "CMT")
    return _settings


def get_setting(key, default_value=None):
    """Get a value in the persistent cache.

    :param key: Hash key
    :param default_value: Value to return if key does not exist.
    :return: Store value.
    """
    settings = _get_settings()
    return settings.value(key, default_value)


def set_setting(key, value):
    """Set a value in the persistent cache.

    :param key: Hash key
    :param value: Value to store
    """
    settings = _get_settings()
    settings.setValue(key, value)


def get_save_file_name(file_filter, key=None):
    """Get a file path from a save dialog.

    :param file_filter: File filter eg "Maya Files (*.ma *.mb)"
    :param key: Optional key value to access the starting directory which is saved in
        the persistent cache.
    :return: The selected file path
    """
    return _get_file_path(file_filter, key, 0)


def get_open_file_name(file_filter, key=None):
    """Get a file path from an open file dialog.

    :param file_filter: File filter eg "Maya Files (*.ma *.mb)"
    :param key: Optional key value to access the starting directory which is saved in
        the persistent cache.
    :return: The selected file path
    """
    return _get_file_path(file_filter, key, 1)


def get_directory_name(key=None):
    """Get a file path from an open file dialog.

    :param key: Optional key value to access the starting directory which is saved in
        the persistent cache.
    :return: The selected file path
    """
    return _get_file_path("", key, 3)


def _get_file_path(file_filter, key, file_mode):
    """Get a file path from a file dialog.

    :param file_filter: File filter eg "Maya Files (*.ma *.mb)"
    :param key: Optional key value to access the starting directory which is saved in
        the persistent cache.
    :param file_mode: 0 Any file, whether it exists or not.
        1 A single existing file.
        2 The name of a directory. Both directories and files are displayed in the dialog.
        3 The name of a directory. Only directories are displayed in the dialog.
        4 Then names of one or more existing files.
    :return: The selected file path
    """
    start_directory = cmds.workspace(q=True, rd=True)
    if key is not None:
        start_directory = get_setting(key, start_directory)

    file_path = cmds.fileDialog2(
        fileMode=file_mode, startingDirectory=start_directory, fileFilter=file_filter
    )
    if key is not None and file_path:
        file_path = file_path[0]
        directory = (
            file_path if os.path.isdir(file_path) else os.path.dirname(file_path)
        )
        set_setting(key, directory)
    return file_path


# MScriptUtil
def get_int_ptr():
    util = OpenMaya.MScriptUtil()
    util.createFromInt(0)
    return util.asIntPtr()


def ptr_to_int(int_ptr):
    return OpenMaya.MScriptUtil.getInt(int_ptr)


def distance(node1=None, node2=None):
    """Calculate the distance between two nodes

    :param node1: First node
    :param node2: Second node
    :return: The distance
    """
    if node1 is None or node2 is None:
        # Default to selection
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) != 2:
            raise RuntimeError('Select 2 transforms.')
        node1, node2 = selection

    pos1 = cmds.xform(node1, query=True, worldSpace=True, translation=True)
    pos2 = cmds.xform(node2, query=True, worldSpace=True, translation=True)

    pos1 = OpenMaya.MPoint(pos1[0], pos1[1], pos1[2])
    pos2 = OpenMaya.MPoint(pos2[0], pos2[1], pos2[2])
    return pos1.distanceTo(pos2)


def vector_to(source=None, target=None):
    """Calculate the distance between two nodes

    :param source: First node
    :param target: Second node
    :return: MVector (API2)
    """
    if source is None or target is None:
        # Default to selection
        selection = cmds.ls(sl=True, type='transform')
        if len(selection) != 2:
            raise RuntimeError('Select 2 transforms.')
        source, target = selection

    pos1 = cmds.xform(source, query=True, worldSpace=True, translation=True)
    pos2 = cmds.xform(target, query=True, worldSpace=True, translation=True)

    source = OpenMaya2.MPoint(pos1[0], pos1[1], pos1[2])
    target = OpenMaya2.MPoint(pos2[0], pos2[1], pos2[2])
    return target - source
