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
from PySide import QtGui
from PySide import QtCore
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import cmt.shortcuts as shortcuts

logger = logging.getLogger(__name__)
CONTROLS_DIRECTORY = os.path.join(os.path.dirname(__file__), 'controls')


def ui():
    """Display the control creator ui."""
    win = ControlWindow()
    win.show()


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
        cmds.rotate(rx, ry, rz, '{0}.cv[*]'.format(node), r=True, p=pivot, os=True, fo=True)


def create_curve(control):
    """Create a curve.

    :param control: A data dictionary generated from the dump function.
    :return: The created curve.
    """
    periodic = control['form'] == 2
    degree = control['degree']
    points = control['cvs']
    points = points + points[:degree] if periodic else points
    curve = cmds.curve(degree=degree, p=points, n=control['name'], per=periodic, k=control['knots'])
    cmds.xform(curve, matrix=control['xform'])
    cmds.xform(curve, piv=control['pivot'])
    cmds.delete(curve, constructionHistory=True)
    cmds.setAttr('{0}.overrideEnabled'.format(curve), control['overrideEnabled'])
    cmds.setAttr('{0}.overrideRGBColors'.format(curve), control['overrideRGBColors'])
    cmds.setAttr('{0}.overrideColorRGB'.format(curve), *control['overrideColorRGB'])
    cmds.setAttr('{0}.overrideColor'.format(curve), control['overrideColor'])
    return curve


def dump(curves=None):
    """Get a data dictionary representing all the given curves.

    :param curves: Optional list of curves.
    :return: A json serializable list of dictionaries containing the data required to recreate the curves.
    """
    if curves is None:
        curves = cmds.ls(sl=True) or []
    data = []
    for node in curves:
        shape = shortcuts.get_shape(node)
        if cmds.nodeType(shape) == 'nurbsCurve':
            control = {
                'name': node,
                'cvs': cmds.getAttr('{0}.cv[*]'.format(node)),
                'degree': cmds.getAttr('{0}.degree'.format(node)),
                'form': cmds.getAttr('{0}.form'.format(node)),
                'xform': cmds.xform(node, q=True, matrix=True),
                'knots': get_knots(node),
                'pivot': cmds.xform(node, q=True, rp=True),
                'overrideEnabled': cmds.getAttr('{0}.overrideEnabled'.format(node)),
                'overrideRGBColors': cmds.getAttr('{0}.overrideRGBColors'.format(node)),
                'overrideColorRGB': cmds.getAttr('{0}.overrideColorRGB'.format(node))[0],
                'overrideColor': cmds.getAttr('{0}.overrideColor'.format(node)),
            }
            data.append(control)
    if curves:
        cmds.select(curves)
    return data


def get_knots(curve):
    """Gets the list of knots of a curve so it can be recreated.

    :param curve: Curve to query.
    :return: A list of knot values that can be passed into the curve creation command.
    """
    curve = shortcuts.get_shape(curve)
    info = cmds.createNode('curveInfo')
    cmds.connectAttr('{0}.worldSpace'.format(curve), '{0}.inputCurve'.format(info))
    knots = cmds.getAttr('{0}.knots[*]'.format(info))
    cmds.delete(info)
    return knots


def dump_controls(curves=None):
    """Serializes the given curves into the control library.

    :param curves: Optional list of curves.
    """
    if curves is None:
        curves = cmds.ls(sl=True)
    data = dump(curves)
    for curve in data:
        name = curve['name']
        file_path = os.path.join(CONTROLS_DIRECTORY, '{0}.json'.format(name))
        logger.info('Exporting %s', file_path)
        fh = open(file_path, 'w')
        json.dump(curve, fh, indent=4)
        fh.close()


class ControlWindow(MayaQWidgetDockableMixin, QtGui.QDialog):
    """The UI used to create and manipulate curves from the curve library."""

    def __init__(self, parent=None):
        super(ControlWindow, self).__init__(parent)
        self.setWindowTitle('CMT Control Creator')
        self.resize(300, 500)
        vbox = QtGui.QVBoxLayout(self)

        size = 20
        label_width = 60
        icon_left = QtGui.QIcon(QtGui.QPixmap(':/nudgeLeft.png').scaled(size, size))
        icon_right = QtGui.QIcon(QtGui.QPixmap(':/nudgeRight.png').scaled(size, size))
        validator = QtGui.QDoubleValidator(-180.0, 180.0, 2)
        grid = QtGui.QGridLayout()
        vbox.addLayout(grid)

        # Rotate X
        label = QtGui.QLabel('Rotate X')
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 0, 0, QtCore.Qt.AlignRight)
        b = QtGui.QPushButton(icon_left, '')
        b.released.connect(partial(self.rotate_x, direction=-1))
        grid.addWidget(b, 0, 1)
        self.offset_x = QtGui.QLineEdit('45.0')
        self.offset_x.setValidator(validator)
        grid.addWidget(self.offset_x, 0, 2)
        b = QtGui.QPushButton(icon_right, '')
        b.released.connect(partial(self.rotate_x, direction=1))
        grid.addWidget(b, 0, 3)

        # Rotate Y
        label = QtGui.QLabel('Rotate Y')
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 1, 0, QtCore.Qt.AlignRight)
        b = QtGui.QPushButton(icon_left, '')
        b.released.connect(partial(self.rotate_y, direction=-1))
        grid.addWidget(b, 1, 1)
        self.offset_y = QtGui.QLineEdit('45.0')
        self.offset_y.setValidator(validator)
        grid.addWidget(self.offset_y, 1, 2)
        b = QtGui.QPushButton(icon_right, '')
        b.released.connect(partial(self.rotate_y, direction=1))
        grid.addWidget(b, 1, 3)

        # Rotate Z
        label = QtGui.QLabel('Rotate Z')
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 2, 0, QtCore.Qt.AlignRight)
        b = QtGui.QPushButton(icon_left, '')
        b.released.connect(partial(self.rotate_z, direction=-1))
        grid.addWidget(b, 2, 1)
        self.offset_z = QtGui.QLineEdit('45.0')
        self.offset_z.setValidator(validator)
        grid.addWidget(self.offset_z, 2, 2)
        b = QtGui.QPushButton(icon_right, '')
        b.released.connect(partial(self.rotate_z, direction=1))
        grid.addWidget(b, 2, 3)
        grid.setColumnStretch(2, 2)

        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        b = QtGui.QPushButton('Export Selected')
        b.released.connect(self.dump_controls)
        hbox.addWidget(b)

        b = QtGui.QPushButton('Set Color')
        b.released.connect(self.set_color)
        hbox.addWidget(b)

        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        b = QtGui.QPushButton('Create Selected')
        b.released.connect(self.create_selected)
        hbox.addWidget(b)

        b = QtGui.QPushButton('Remove Selected')
        b.released.connect(self.remove_selected)
        hbox.addWidget(b)

        self.control_list = QtGui.QListWidget()
        self.control_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        vbox.addWidget(self.control_list)

        self.populate_controls()

    def populate_controls(self):
        """Populates the control list with the available controls stored in CONTROLS_DIRECTORY."""
        self.control_list.clear()
        controls = [os.path.splitext(x)[0] for x in os.listdir(CONTROLS_DIRECTORY) if x.endswith('.json')]
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
            color = cmds.getAttr('{0}.overrideColorRGB'.format(nodes[0]))[0]
            color = QtGui.QColor(color[0]*255, color[1]*255, color[2]*255)
            color = QtGui.QColorDialog.getColor(color, self, 'Set Curve Color')
            if color.isValid():
                color = [color.redF(), color.greenF(), color.blueF()]
                for node in nodes:
                    cmds.setAttr('{0}.overrideEnabled'.format(node), True)
                    cmds.setAttr('{0}.overrideRGBColors'.format(node), True)
                    cmds.setAttr('{0}.overrideColorRGB'.format(node), *color)

    def create_selected(self):
        """Create the curves selected in the curve list."""
        curves = []
        for item in self.control_list.selectedItems():
            text = item.text()
            control_file = os.path.join(CONTROLS_DIRECTORY, '{0}.json'.format(text))
            fh = open(control_file, 'r')
            data = json.load(fh)
            fh.close()
            curves.append(create_curve(data))
        if curves:
            cmds.select(curves)

    def remove_selected(self):
        """Remove the curves selected in the curve list from the curve library."""
        items = self.control_list.selectedItems()
        if items:
            button = QtGui.QMessageBox.question(self, 'Remove Controls',
                                                'Are you sure you want to remove the selected controls?',
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if button == QtGui.QMessageBox.Yes:
                for item in items:
                    text = item.text()
                    control_file = os.path.join(CONTROLS_DIRECTORY, '{0}.json'.format(text))
                    os.remove(control_file)
                self.populate_controls()

