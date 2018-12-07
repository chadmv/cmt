"""A tool used to create curve controls.

Curves can be serialized into json format and added to the curve library for future creation.

Usage:

From the menu:
CMT > Rigging > Create Control

To show the UI:
import cmt.rig.control
cmt.rig.control.ui()

API:
data = dump(['curve1'])
new_curve = create_curve(data)
"""
from functools import partial
import json
import os
import logging
from cmt.qt import QtWidgets
from cmt.qt import QtGui
from cmt.qt import QtCore
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import cmt.shortcuts as shortcuts

logger = logging.getLogger(__name__)
CONTROLS_DIRECTORY = os.path.join(os.path.dirname(__file__), "controls")

# The message attribute specifying which nodes are part of a transform stack.
STACK_ATTRIBUTE = "cmt_transformStack"


def export_controls(controls=None, file_path=None):
    """Serializes the given curves into the control library.

    :param curves: Optional list of curves.
    """
    if file_path is None:
        file_path = shortcuts.get_save_file_name("*.json", "cmt.control")
        if not file_path:
            return
    if controls is None:
        controls = cmds.ls(sl=True)
    data = get_control_data(controls)
    with open(file_path, "w") as fh:
        json.dump(data, fh, indent=4, cls=CurveShapeEncoder)
        logger.info("Exported controls {}".format(file_path))


def get_control_data(controls=None):
    """Get the serializable data of the given controls.

    :param controls: Controls to serialize
    :return: List of control data dictionaries
    """
    if controls is None:
        controls = cmds.ls(sl=True)
    data = [CurveShape(transform=control) for control in controls]
    return data


class CurveCreateMode(object):
    """Used by import_controls to specify how to create new curves."""

    new_curve = 0
    selected_curve = 1
    saved_curve = 2


def import_controls(
    file_path=None, create_mode=CurveCreateMode.saved_curve, tag_as_controller=False
):
    """Imports control shapes from disk.

    :param file_path: Path to the control file.
    :param create_mode: One of the values of CurveCreateMode
        new_curve: Create the curve on a new transform.
        selected_curve: Create the curve on the selected transform.
        saved_curve: Create the curve on transform saved with the curve shape.
    :param tag_as_controller: True to tag the curve transform as a controller
    :return: The new curve transform
    """
    controls = load_controls(file_path)
    selected_transform = cmds.ls(sl=True)
    if selected_transform:
        selected_transform = selected_transform[0]

    transforms = []
    for curve in controls:
        transform = {
            CurveCreateMode.new_curve: _get_new_transform_name(curve.transform),
            CurveCreateMode.selected_curve: selected_transform,
            CurveCreateMode.saved_curve: curve.transform,
        }[create_mode]
        transforms.append(curve.create(transform, tag_as_controller))
    return transforms


def load_controls(file_path=None):
    """Load the CurveShape objects from disk.

    :param file_path:
    :return:
    """
    if file_path is None:
        file_path = shortcuts.get_open_file_name("*.json", "cmt.control")
        if not file_path:
            return

    with open(file_path, "r") as fh:
        data = json.load(fh)
    logger.info("Loaded controls {}".format(file_path))
    curves = [CurveShape(**control) for control in data]
    return curves


def _get_new_transform_name(base):
    """Get a new unique transform name

    :param base: Base name
    :return: A unique name of a non-existing transform
    """
    name = base
    i = 1
    while cmds.objExists(name):
        name = "{}{}".format(base, i)
        i += 1
    return name


class CurveShape(json.JSONEncoder):
    """Represents the data required to build a nurbs curve shape"""

    def __init__(
        self, transform=None, cvs=None, degree=3, form=0, knots=None, color=None
    ):
        self.cvs = cvs
        self.degree = degree
        self.form = form
        self.knots = knots
        self.color = color
        self.transform_matrix = OpenMaya.MTransformationMatrix()
        self.transform = transform
        if transform and cmds.objExists(transform) and not cvs:
            self.set_from_curve(transform)

    def set_from_curve(self, transform):
        """Store the parameters from an existing curve in the CurveShape object.

        :param transform: Transform
        :return:
        """
        shape = shortcuts.get_shape(transform)
        if shape and cmds.nodeType(shape) == "nurbsCurve":
            self.transform = transform
            self.cvs = cmds.getAttr("{}.cv[*]".format(shape))
            self.degree = cmds.getAttr("{}.degree".format(shape))
            self.form = cmds.getAttr("{}.form".format(shape))
            self.knots = get_knots(shape)
            if cmds.getAttr("{}.overrideEnabled".format(shape)):
                if cmds.getAttr("{}.overrideRGBColors".format(shape)):
                    self.color = cmds.getAttr("{}.overrideColorRGB".format(shape))[0]
                else:
                    self.color = cmds.getAttr("{}.overrideColor".format(shape))
            else:
                self.color = None

    def create(self, transform=None, as_controller=True):
        """Create a curve.

        :param transform: Name of the transform to create the curve shape under.
            If the transform does not exist, it will be created.
        :param as_controller: True to mark the curve transform as a controller.
        :return: The transform of the new curve shapes.
        """
        transform = transform or self.transform
        if not cmds.objExists(transform):
            transform = cmds.createNode("transform", name=transform)
        periodic = self.form == 2
        points = self._get_transformed_points()
        points = points + points[: self.degree] if periodic else points
        curve = cmds.curve(degree=self.degree, p=points, per=periodic, k=self.knots)
        shape = shortcuts.get_shape(curve)
        if self.color is not None:
            cmds.setAttr("{}.overrideEnabled".format(shape), True)
            if isinstance(self.color, int):
                cmds.setAttr("{}.overrideColor".format(shape), self.color)
            else:
                cmds.setAttr("{}.overrideRGBColors".format(shape), True)
                cmds.setAttr("{}.overrideColorRGB".format(shape), *self.color)
        cmds.parent(shape, transform, r=True, s=True)
        shape = cmds.rename(shape, "{}Shape".format(transform))
        cmds.delete(curve)
        if as_controller:
            cmds.controller(transform)
        logger.info("Created curve {} for transform {}".format(shape, transform))
        return transform

    def _get_transformed_points(self):
        matrix = self.transform_matrix.asMatrix()
        points = [OpenMaya.MPoint(*x) * matrix for x in self.cvs]
        points = [(p.x, p.y, p.z) for p in points]
        return points

    def translate_by(self, x, y, z, local=True):
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.translateBy(OpenMaya.MVector(x, y, z), space)

    def set_translation(self, x, y, z, local=True):
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.setTranslation(OpenMaya.MVector(x, y, z), space)

    def rotate_by(self, x, y, z, local=True):
        x, y, z = [v * 0.0174533 for v in [x, y, z]]
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.rotateBy(OpenMaya.MEulerRotation(x, y, z), space)

    def set_rotation(self, x, y, z):
        x, y, z = [v * 0.0174533 for v in [x, y, z]]
        self.transform_matrix.setRotation(OpenMaya.MEulerRotation(x, y, z))

    def scale_by(self, x, y, z, local=True):
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.scaleBy([x, y, z], space)

    def set_scale(self, x, y, z, local=True):
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.setScale([x, y, z], space)


class CurveShapeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CurveShape):
            return {
                "cvs": obj.cvs,
                "degree": obj.degree,
                "form": obj.form,
                "knots": obj.knots,
                "color": obj.color,
                "transform": obj.transform,
            }
        return json.JSONEncoder.default(self, obj)


def rotate_components(rx, ry, rz, nodes=None):
    """Rotate the given nodes' components the given number of degrees about each axis.

    :param rx: Degrees around x.
    :param ry: Degrees around y.
    :param rz: Degrees around z.
    :param nodes: Optional list of curves.
    """
    if nodes is None:
        nodes = cmds.ls(sl=True) or []
    for node in nodes:
        pivot = cmds.xform(node, q=True, rp=True, ws=True)
        cmds.rotate(
            rx, ry, rz, "{0}.cv[*]".format(node), r=True, p=pivot, os=True, fo=True
        )


def create_curves(curves):
    for curve in curves:
        create_curve(curve)

    # Now parent the curves
    for curve in curves:
        if curve.get("parent"):
            parent = curve["parent"]
            if cmds.objExists(parent):
                cmds.parent(curve["name"], parent)

    # Then create the stacks
    for curve in curves:
        if curve.get("stack"):
            create_transform_stack(curve["name"], curve["stack"])


def create_curve(control):
    """Create a curve.

    :param control: A data dictionary generated from the dump function.
    :return: The created curve.
    """
    periodic = control["form"] == 2
    degree = control["degree"]
    points = control["cvs"]
    points = points + points[:degree] if periodic else points
    curve = cmds.curve(
        degree=degree, p=points, n=control["name"], per=periodic, k=control["knots"]
    )
    cmds.xform(curve, ws=True, matrix=control["xform"])
    cmds.xform(curve, piv=control["pivot"])
    cmds.delete(curve, constructionHistory=True)
    cmds.setAttr("{0}.overrideEnabled".format(curve), control["overrideEnabled"])
    cmds.setAttr("{0}.overrideRGBColors".format(curve), control["overrideRGBColors"])
    cmds.setAttr("{0}.overrideColorRGB".format(curve), *control["overrideColorRGB"])
    cmds.setAttr("{0}.overrideColor".format(curve), control["overrideColor"])
    return curve


def get_knots(curve):
    """Gets the list of knots of a curve so it can be recreated.

    :param curve: Curve to query.
    :return: A list of knot values that can be passed into the curve creation command.
    """
    curve = shortcuts.get_shape(curve)
    info = cmds.createNode("curveInfo")
    cmds.connectAttr("{0}.worldSpace".format(curve), "{0}.inputCurve".format(info))
    knots = cmds.getAttr("{0}.knots[*]".format(info))
    knots = [int(x) for x in knots]
    cmds.delete(info)
    return knots


class ControlWindow(
    shortcuts.SingletonWindowMixin, MayaQWidgetBaseMixin, QtWidgets.QDialog
):
    """The UI used to create and manipulate curves from the curve library."""

    def __init__(self, parent=None):
        super(ControlWindow, self).__init__(parent)
        self.setWindowTitle("CMT Control Creator")
        self.resize(300, 500)
        vbox = QtWidgets.QVBoxLayout(self)

        size = 20
        label_width = 60
        icon_left = QtGui.QIcon(QtGui.QPixmap(":/nudgeLeft.png").scaled(size, size))
        icon_right = QtGui.QIcon(QtGui.QPixmap(":/nudgeRight.png").scaled(size, size))
        validator = QtGui.QDoubleValidator(-180.0, 180.0, 2)
        grid = QtWidgets.QGridLayout()
        vbox.addLayout(grid)

        # Rotate X
        label = QtWidgets.QLabel("Rotate X")
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 0, 0, QtCore.Qt.AlignRight)
        b = QtWidgets.QPushButton(icon_left, "")
        b.released.connect(partial(self.rotate_x, direction=-1))
        grid.addWidget(b, 0, 1)
        self.offset_x = QtWidgets.QLineEdit("45.0")
        self.offset_x.setValidator(validator)
        grid.addWidget(self.offset_x, 0, 2)
        b = QtWidgets.QPushButton(icon_right, "")
        b.released.connect(partial(self.rotate_x, direction=1))
        grid.addWidget(b, 0, 3)

        # Rotate Y
        label = QtWidgets.QLabel("Rotate Y")
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 1, 0, QtCore.Qt.AlignRight)
        b = QtWidgets.QPushButton(icon_left, "")
        b.released.connect(partial(self.rotate_y, direction=-1))
        grid.addWidget(b, 1, 1)
        self.offset_y = QtWidgets.QLineEdit("45.0")
        self.offset_y.setValidator(validator)
        grid.addWidget(self.offset_y, 1, 2)
        b = QtWidgets.QPushButton(icon_right, "")
        b.released.connect(partial(self.rotate_y, direction=1))
        grid.addWidget(b, 1, 3)

        # Rotate Z
        label = QtWidgets.QLabel("Rotate Z")
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 2, 0, QtCore.Qt.AlignRight)
        b = QtWidgets.QPushButton(icon_left, "")
        b.released.connect(partial(self.rotate_z, direction=-1))
        grid.addWidget(b, 2, 1)
        self.offset_z = QtWidgets.QLineEdit("45.0")
        self.offset_z.setValidator(validator)
        grid.addWidget(self.offset_z, 2, 2)
        b = QtWidgets.QPushButton(icon_right, "")
        b.released.connect(partial(self.rotate_z, direction=1))
        grid.addWidget(b, 2, 3)
        grid.setColumnStretch(2, 2)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        b = QtWidgets.QPushButton("Export Selected")
        b.released.connect(self.dump_controls)
        hbox.addWidget(b)

        b = QtWidgets.QPushButton("Set Color")
        b.released.connect(self.set_color)
        hbox.addWidget(b)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        b = QtWidgets.QPushButton("Create Selected")
        b.released.connect(self.create_selected)
        hbox.addWidget(b)

        b = QtWidgets.QPushButton("Remove Selected")
        b.released.connect(self.remove_selected)
        hbox.addWidget(b)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        self.stack_count = QtWidgets.QSpinBox()
        self.stack_count.setValue(2)
        hbox.addWidget(self.stack_count)

        b = QtWidgets.QPushButton("Create Transform Stack")
        b.released.connect(self.create_transform_stack)
        b.setToolTip("Creates a transform stack above each selected node.")
        hbox.addWidget(b)

        self.control_list = QtWidgets.QListWidget()
        self.control_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        vbox.addWidget(self.control_list)

        self.populate_controls()

    def populate_controls(self):
        """Populates the control list with the available controls stored in CONTROLS_DIRECTORY."""
        self.control_list.clear()
        controls = [
            os.path.splitext(x)[0]
            for x in os.listdir(CONTROLS_DIRECTORY)
            if x.endswith(".json")
        ]
        controls.sort()
        self.control_list.addItems(controls)

    def rotate_x(self, direction):
        """Callback function to rotate the components around the x axis by the amount of degrees in offset_x.

        :param direction: 1 or -1
        """
        amount = float(self.offset_x.text()) * direction
        rotate_components(amount, 0, 0)

    def rotate_y(self, direction):
        """Callback function to rotate the components around the y axis by the amount of degrees in offset_y.

        :param direction: 1 or -1
        """
        amount = float(self.offset_y.text()) * direction
        rotate_components(0, amount, 0)

    def rotate_z(self, direction):
        """Callback function to rotate the components around the z axis by the amount of degrees in offset_z.

        :param direction: 1 or -1
        """
        amount = float(self.offset_z.text()) * direction
        rotate_components(0, 0, amount)

    def dump_controls(self):
        """Dumps the selected curves to into the CONTROLS_DIRECTORY so they can be added to the library."""
        dump_controls()
        self.populate_controls()

    def set_color(self):
        """Open a dialog to set the override RGB color of the selected nodes."""
        nodes = cmds.ls(sl=True) or []
        if nodes:
            color = cmds.getAttr("{0}.overrideColorRGB".format(nodes[0]))[0]
            color = QtGui.QColor(color[0] * 255, color[1] * 255, color[2] * 255)
            color = QtWidgets.QColorDialog.getColor(color, self, "Set Curve Color")
            if color.isValid():
                color = [color.redF(), color.greenF(), color.blueF()]
                for node in nodes:
                    cmds.setAttr("{0}.overrideEnabled".format(node), True)
                    cmds.setAttr("{0}.overrideRGBColors".format(node), True)
                    cmds.setAttr("{0}.overrideColorRGB".format(node), *color)

    def create_selected(self):
        """Create the curves selected in the curve list."""
        curves = []
        sel = cmds.ls(sl=True)
        target = sel[0] if sel else None
        for item in self.control_list.selectedItems():
            text = item.text()
            control_file = os.path.join(CONTROLS_DIRECTORY, "{0}.json".format(text))
            fh = open(control_file, "r")
            data = json.load(fh)
            fh.close()
            curve = create_curve(data)
            if target:
                cmds.delete(cmds.parentConstraint(target, curve))
            curves.append(curve)
        if curves:
            cmds.select(curves)

    def remove_selected(self):
        """Remove the curves selected in the curve list from the curve library."""
        items = self.control_list.selectedItems()
        if items:
            button = QtWidgets.QMessageBox.question(
                self,
                "Remove Controls",
                "Are you sure you want to remove the selected controls?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if button == QtWidgets.QMessageBox.Yes:
                for item in items:
                    text = item.text()
                    control_file = os.path.join(
                        CONTROLS_DIRECTORY, "{0}.json".format(text)
                    )
                    os.remove(control_file)
                self.populate_controls()

    def create_transform_stack(self):
        count = self.stack_count.value()
        for node in cmds.ls(sl=True) or []:
            create_transform_stack(node, count)


def create_transform_stack(node, count=2):
    """Creates a transform stack above the given node.

    Any previous transform stack will be deleted.

    :param node: Node to parent into a transform stack.
    :param count: Number of transforms to add in the stack.
    :return: A list of the transform nodes created starting from top to bottom.
    """
    previous_parent = cmds.listRelatives(node, parent=True, path=True)
    if previous_parent:
        previous_parent = previous_parent[0]
        while previous_parent and STACK_ATTRIBUTE in (
            cmds.listAttr(previous_parent, ud=True) or []
        ):
            parent = cmds.listRelatives(previous_parent, parent=True, path=True)
            if parent:
                cmds.parent(node, parent)
                parent = parent[0]
            else:
                cmds.parent(node, world=True)
            cmds.delete(previous_parent)
            previous_parent = parent

    nulls = []
    for i in reversed(range(count)):
        name = "_".join(node.split("_")[:-1])
        name = "{0}_{1}nul".format(name, i + 1)
        null = cmds.createNode("transform", name=name)
        nulls.append(null)
        cmds.addAttr(null, ln=STACK_ATTRIBUTE, at="message")
        cmds.connectAttr(
            "{0}.message".format(node), "{0}.{1}".format(null, STACK_ATTRIBUTE)
        )
        cmds.delete(cmds.parentConstraint(node, null))
        if previous_parent:
            cmds.parent(null, previous_parent)
        previous_parent = null
    cmds.parent(node, previous_parent)
    return nulls


def get_stack_count(node):
    """Get the number of transforms in the stack.

    :param node: Node to query.
    :return: The number of transforms in the stack.
    """
    connections = cmds.listConnections("{0}.message".format(node), plugs=True) or []
    count = 0
    for connection in connections:
        connected_node, attribute = connection.split(".")
        if attribute == STACK_ATTRIBUTE:
            count += 1
    return count


def get_stack_parent(node):
    """Get the parent of the transform stack belonging to the given node.

    :param node: Node to query.
    :return: The parent node or None if there is no parent.
    """
    previous_parent = cmds.listRelatives(node, parent=True, path=True)
    if not previous_parent:
        return None
    previous_parent = previous_parent[0]
    while previous_parent and STACK_ATTRIBUTE in (
        cmds.listAttr(previous_parent, ud=True) or []
    ):
        parent = cmds.listRelatives(previous_parent, parent=True, path=True)
        if parent:
            parent = parent[0]
        previous_parent = parent
    return previous_parent
