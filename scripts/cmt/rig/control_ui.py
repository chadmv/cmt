"""The graphical interface of the control module"""

from functools import partial
import os
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *

import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

import cmt.shortcuts as shortcuts
from cmt.rig.control import (
    get_control_paths_in_library,
    rotate_components,
    CONTROLS_DIRECTORY,
    export_curves,
    mirror_curve,
    import_curves_on_selected,
    import_new_curves,
    documentation,
)


def show():
    ControlWindow.show_window()


class ControlWindow(shortcuts.SingletonWindowMixin, MayaQWidgetBaseMixin, QMainWindow):
    """The UI used to create and manipulate curves from the curve library."""

    def __init__(self, parent=None):
        super(ControlWindow, self).__init__(parent)
        self.setWindowTitle("CMT Control Creator")
        self.resize(300, 500)

        menubar = self.menuBar()
        menu = menubar.addMenu("Help")
        action = menu.addAction("Documentation")
        action.triggered.connect(documentation)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        vbox = QVBoxLayout(self)
        main_widget.setLayout(vbox)

        size = 20
        label_width = 60
        icon_left = QIcon(QPixmap(":/nudgeLeft.png").scaled(size, size))
        icon_right = QIcon(QPixmap(":/nudgeRight.png").scaled(size, size))
        validator = QDoubleValidator(-180.0, 180.0, 2)
        grid = QGridLayout()
        vbox.addLayout(grid)

        # Rotate X
        label = QLabel("Rotate X")
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 0, 0, Qt.AlignRight)
        b = QPushButton(icon_left, "")
        b.released.connect(partial(self.rotate_x, direction=-1))
        grid.addWidget(b, 0, 1)
        self.offset_x = QLineEdit("45.0")
        self.offset_x.setValidator(validator)
        grid.addWidget(self.offset_x, 0, 2)
        b = QPushButton(icon_right, "")
        b.released.connect(partial(self.rotate_x, direction=1))
        grid.addWidget(b, 0, 3)

        # Rotate Y
        label = QLabel("Rotate Y")
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 1, 0, Qt.AlignRight)
        b = QPushButton(icon_left, "")
        b.released.connect(partial(self.rotate_y, direction=-1))
        grid.addWidget(b, 1, 1)
        self.offset_y = QLineEdit("45.0")
        self.offset_y.setValidator(validator)
        grid.addWidget(self.offset_y, 1, 2)
        b = QPushButton(icon_right, "")
        b.released.connect(partial(self.rotate_y, direction=1))
        grid.addWidget(b, 1, 3)

        # Rotate Z
        label = QLabel("Rotate Z")
        label.setMaximumWidth(label_width)
        grid.addWidget(label, 2, 0, Qt.AlignRight)
        b = QPushButton(icon_left, "")
        b.released.connect(partial(self.rotate_z, direction=-1))
        grid.addWidget(b, 2, 1)
        self.offset_z = QLineEdit("45.0")
        self.offset_z.setValidator(validator)
        grid.addWidget(self.offset_z, 2, 2)
        b = QPushButton(icon_right, "")
        b.released.connect(partial(self.rotate_z, direction=1))
        grid.addWidget(b, 2, 3)
        grid.setColumnStretch(2, 2)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        b = QPushButton("Export to Library")
        b.released.connect(self.export_to_library)
        hbox.addWidget(b)
        b = QPushButton("Remove Selected")
        b.released.connect(self.remove_selected)
        hbox.addWidget(b)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        b = QPushButton("Set Color")
        b.released.connect(self.set_color)
        hbox.addWidget(b)
        b = QPushButton("Mirror Curve")
        b.released.connect(self.mirror_curve)
        hbox.addWidget(b)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        b = QPushButton("Create Selected")
        b.released.connect(self.create_selected)
        hbox.addWidget(b)

        self.control_list = QListWidget()
        self.control_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        vbox.addWidget(self.control_list)

        self.populate_controls()

    def populate_controls(self):
        """Populates the control list with the available controls stored in
        CONTROLS_DIRECTORY."""
        self.control_list.clear()
        controls = get_control_paths_in_library()
        self.control_list.addItems(controls)

    def rotate_x(self, direction):
        """Callback function to rotate the components around the x axis by the amount of
        degrees in offset_x.

        :param direction: 1 or -1
        """
        amount = float(self.offset_x.text()) * direction
        rotate_components(amount, 0, 0)

    def rotate_y(self, direction):
        """Callback function to rotate the components around the y axis by the amount of
        degrees in offset_y.

        :param direction: 1 or -1
        """
        amount = float(self.offset_y.text()) * direction
        rotate_components(0, amount, 0)

    def rotate_z(self, direction):
        """Callback function to rotate the components around the z axis by the amount of
        degrees in offset_z.

        :param direction: 1 or -1
        """
        amount = float(self.offset_z.text()) * direction
        rotate_components(0, 0, amount)

    def export_to_library(self):
        """Exports the selected curves into the CONTROLS_DIRECTORY."""
        controls = cmds.ls(sl=True)
        for control in controls:
            name = control.split("|")[-1].split(":")[-1]
            file_path = os.path.join(CONTROLS_DIRECTORY, "{}.json".format(name))
            export_curves([control], file_path)
        self.populate_controls()

    def set_color(self):
        """Open a dialog to set the override RGB color of the selected nodes."""
        nodes = cmds.ls(sl=True) or []
        if nodes:
            color = cmds.getAttr("{}.overrideColorRGB".format(nodes[0]))[0]
            color = QColor(color[0] * 255, color[1] * 255, color[2] * 255)
            color = QColorDialog.getColor(color, self, "Set Curve Color")
            if color.isValid():
                color = [color.redF(), color.greenF(), color.blueF()]
                for node in nodes:
                    shape = shortcuts.get_shape(node)
                    cmds.setAttr("{}.overrideEnabled".format(shape), True)
                    cmds.setAttr("{}.overrideRGBColors".format(shape), True)
                    cmds.setAttr("{}.overrideColorRGB".format(shape), *color)

    def mirror_curve(self):
        """Mirrors the curve of the first selected to the second selected."""
        nodes = cmds.ls(sl=True) or []
        if len(nodes) != 2:
            raise RuntimeError("Select source and destination transforms")
        mirror_curve(nodes[0], nodes[1])

    def create_selected(self):
        """Create the curves selected in the curve list."""
        sel = cmds.ls(sl=True)
        target = sel[0] if sel else None
        func = import_curves_on_selected if target else import_new_curves
        curves = []
        for item in self.control_list.selectedItems():
            text = item.text()
            control_file = os.path.join(CONTROLS_DIRECTORY, "{0}.json".format(text))
            controls = func(control_file)
            curves += controls
            if target:
                cmds.select(target)
        if curves:
            cmds.select(curves)

    def remove_selected(self):
        """Remove the curves selected in the curve list from the curve library."""
        items = self.control_list.selectedItems()
        if items:
            button = QMessageBox.question(
                self,
                "Remove Controls",
                "Are you sure you want to remove the selected controls?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if button == QMessageBox.Yes:
                for item in items:
                    text = item.text()
                    control_file = os.path.join(
                        CONTROLS_DIRECTORY, "{0}.json".format(text)
                    )
                    os.remove(control_file)
                self.populate_controls()
