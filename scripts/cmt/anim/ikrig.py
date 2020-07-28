from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import maya.cmds as cmds
import cmt.shortcuts as shortcuts

import logging
import os
import re
import webbrowser

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import cmt.shortcuts as shortcuts

from cmt.ui.widgets.mayanodewidget import MayaNodeWidget
from cmt.ui.widgets.filepathwidget import FilePathWidget
from cmt.ui.widgets.accordionwidget import AccordionWidget
from cmt.io.fbx import import_fbx, export_animation_fbx

logger = logging.getLogger(__name__)

_win = None


class Parts(object):
    parts = [
        "root",
        "hips",
        "chest",
        "neck",
        "head",
        "left_clavicle",
        "left_shoulder",
        "left_elbow",
        "left_hand",
        "left_up_leg",
        "left_lo_leg",
        "left_foot",
        "right_clavicle",
        "right_shoulder",
        "right_elbow",
        "right_hand",
        "right_up_leg",
        "right_lo_leg",
        "right_foot",
        "left_thumb_01",
        "left_thumb_02",
        "left_thumb_03",
        "left_index_01",
        "left_index_02",
        "left_index_03",
        "left_middle_01",
        "left_middle_02",
        "left_middle_03",
        "left_ring_01",
        "left_ring_02",
        "left_ring_03",
        "left_pinky_01",
        "left_pinky_02",
        "left_pinky_03",
        "right_thumb_01",
        "right_thumb_02",
        "right_thumb_03",
        "right_index_01",
        "right_index_02",
        "right_index_03",
        "right_middle_01",
        "right_middle_02",
        "right_middle_03",
        "right_ring_01",
        "right_ring_02",
        "right_ring_03",
        "right_pinky_01",
        "right_pinky_02",
        "right_pinky_03",
    ]

    def __init__(self):
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self.current < len(Parts.parts):
            part = Parts.parts[self.current]
            self.current = self.current + 1
            return part
        else:
            raise StopIteration()


def attach_skeletons(source_joints, target_joints):
    """Create the ikRig node and constrain the target joints to locators driven by the ikRig node.

    :param source_joints: List of source joints in the order listed in Parts
    :param target_joints: List of target joints in the order listed in Parts
    :return: The created ikRig node
    """
    cmds.loadPlugin("cmt", qt=True)
    node = cmds.createNode("ikRig")
    locs = []
    for i, j in enumerate(source_joints):
        if j and not cmds.objExists(j):
            raise RuntimeError("Joint {} does not exist".format(j))
        if target_joints[i] and not cmds.objExists(target_joints[i]):
            raise RuntimeError("Joint {} does not exist".format(target_joints[i]))

        if j:
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(j), "{}.inMatrix[{}]".format(node, i)
            )
            path = shortcuts.get_dag_path2(j)
            rest_matrix = list(path.inclusiveMatrix())
            cmds.setAttr("{}.inRestMatrix[{}]".format(node, i), *rest_matrix, type="matrix")

        if target_joints[i]:
            path = shortcuts.get_dag_path2(target_joints[i])
            matrix = list(path.inclusiveMatrix())
            cmds.setAttr("{}.targetRestMatrix[{}]".format(node, i), *matrix, type="matrix")

            loc = cmds.spaceLocator(name="ikrig_{}".format(target_joints[i]))[0]
            cmds.connectAttr("{}.outputTranslate[{}]".format(node, i), "{}.t".format(loc))
            cmds.connectAttr("{}.outputRotate[{}]".format(node, i), "{}.r".format(loc))

            cmds.setAttr("{}Shape.localScale".format(loc), 5, 5, 5)
            locs.append(loc)
        else:
            locs.append(None)

    for loc, joint in zip(locs, target_joints):
        if loc and joint:
            cmds.parentConstraint(loc, joint)

    return node


def show():
    """Shows the browser window."""
    global _win
    if _win:
        _win.close()
    _win = IKRigWindow()
    _win.show()


def documentation():
    pass
    # webbrowser.open("https://github.com/chadmv/cmt/wiki/Unit-Test-Runner-Dialog")


class IKRigWindow(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self, *args, **kwargs):
        super(IKRigWindow, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("IK Rig")
        self.resize(800, 1000)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        vbox = QVBoxLayout(main_widget)

        splitter = QSplitter(orientation=Qt.Vertical)
        vbox.addWidget(splitter)

        self.correspondence_widget = SkeletonCorrespondenceWidget(self)
        splitter.addWidget(self.correspondence_widget)

        self.export_options = ExportOptionsWidget(self)
        self.fbx_browser = FBXFileBrowser(
            self.correspondence_widget, self.export_options, self
        )
        bottom_splitter = QSplitter(orientation=Qt.Horizontal)
        bottom_splitter.addWidget(self.fbx_browser)
        self.accordion = AccordionWidget()
        self.accordion.addItem("New File Name", self.export_options)
        bottom_splitter.addWidget(self.accordion)
        bottom_splitter.setStretchFactor(2, 1)
        splitter.addWidget(bottom_splitter)

        splitter.setStretchFactor(1, 3)
        # accordion.addItem("Retarget Animations", self.fbx_browser)


class SkeletonCorrespondenceWidget(QWidget):
    def __init__(self, parent=None):
        super(SkeletonCorrespondenceWidget, self).__init__(parent)
        header_font_size = 16.0
        vbox = QVBoxLayout(self)
        scroll = QScrollArea()
        vbox.addWidget(scroll)

        splitter = QSplitter(orientation=Qt.Horizontal)

        source_widget = QWidget()
        splitter.addWidget(source_widget)
        layout = QVBoxLayout(source_widget)
        label = QLabel("Source")
        font = label.font()
        font.setPointSize(header_font_size)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.source = SkeletonDefinitionWidget("source", self)
        layout.addWidget(self.source)
        layout.addStretch()

        target_widget = QWidget()
        splitter.addWidget(target_widget)
        layout = QVBoxLayout(target_widget)
        label = QLabel("Target")
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.target = SkeletonDefinitionWidget("target", self)
        layout.addWidget(self.target)
        layout.addStretch()

        scroll.setWidget(splitter)
        scroll.setWidgetResizable(True)

        retarget_button = QPushButton("Attach Skeletons")
        retarget_button.released.connect(self.attach_skeletons)
        vbox.addWidget(retarget_button)

    def attach_skeletons(self):
        source_joints = self.source.joints()
        target_joints = self.target.joints()
        attach_skeletons(source_joints, target_joints)


class SkeletonDefinitionWidget(QWidget):
    def __init__(self, name, parent=None):
        """Constructor

        :param name: Unique name
        :param parent: Parent QWidget.
        """
        super(SkeletonDefinitionWidget, self).__init__(parent)
        layout = QFormLayout(self)
        layout.setSpacing(500)
        for part in Parts():
            setattr(
                self, part, MayaNodeWidget(name="{}.{}".format(name, part), parent=self)
            )
            widget = getattr(self, part)
            label = part.replace("_", " ").title()
            layout.addRow(label, widget)
        layout.setSpacing(0)

    def joints(self):
        return [getattr(self, part).node for part in Parts()]


class ExportOptionsWidget(QWidget):
    def __init__(self, parent=None):
        super(ExportOptionsWidget, self).__init__(parent)
        layout = QFormLayout(self)
        self.prefix = QLineEdit()
        layout.addRow("Prefix:", self.prefix)
        self.suffix = QLineEdit()
        layout.addRow("Suffix:", self.suffix)
        self.search = QLineEdit()
        layout.addRow("Search:", self.search)
        self.replace = QLineEdit()
        layout.addRow("Replace:", self.replace)
        self.export_directory = FilePathWidget(
            file_mode=FilePathWidget.directory, name="ikrig.export", parent=self
        )
        layout.addRow("Export Directory:", self.export_directory)

    def get_export_path(self, path):
        """Get the generated export path given an input path.

        :param path: Input path
        :return: Export path
        """
        name = os.path.basename(path)
        prefix = self.prefix.text().strip()
        suffix = self.suffix.text().strip()
        search = self.search.text().strip()
        replace = self.replace.text().strip()
        if search:
            name = name.replace(search, replace)
        name = "{}{}{}".format(prefix, name, suffix)
        path = os.path.realpath(os.path.join(self.export_directory.path, name))
        return path


class FBXFileBrowser(QWidget):
    def __init__(self, correspondence_widget, export_options_widget, parent=None):
        """Constructor

        :param parent: Parent QWidget.
        """
        super(FBXFileBrowser, self).__init__(parent)
        self.create_actions()

        self.correspondence_widget = correspondence_widget
        self.export_options = export_options_widget

        layout = QVBoxLayout(self)
        self.file_model = QFileSystemModel(self)
        self.root_path = FilePathWidget(
            "Root Directory: ",
            FilePathWidget.directory,
            name="cmt.ikrig.fbxfilebrowser.rootpath",
            parent=self,
        )
        self.root_path.path_changed.connect(self.set_root_path)
        layout.addWidget(self.root_path)

        self.file_tree_view = QTreeView()
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.Files | QDir.AllDirs)
        self.file_model.setReadOnly(True)
        self.file_model.setNameFilters(["*.fbx"])
        self.file_model.setNameFilterDisables(False)
        self.file_tree_view.setModel(self.file_model)
        self.file_tree_view.setColumnHidden(1, True)
        self.file_tree_view.setColumnHidden(2, True)
        self.file_tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree_view.customContextMenuRequested.connect(
            self.on_file_tree_context_menu
        )
        self.file_tree_view.doubleClicked.connect(self.on_file_tree_double_clicked)
        self.file_tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_tree_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.file_tree_view)
        self.set_root_path(self.root_path.path)

    def create_actions(self):
        self.retarget_selected_action = QAction(
            "Retarget Selected",
            toolTip="Retarget and export the selected files.",
            triggered=self.retarget_selected,
        )

    def create_menu(self):
        return
        menubar = self.menuBar()
        menu = menubar.addMenu("Shapes")
        menu.addAction(self.propagate_neutral_action)
        menu.addAction(self.export_selected_action)

    def set_root_path(self, path):
        index = self.file_model.setRootPath(path)
        self.file_tree_view.setRootIndex(index)

    def on_file_tree_double_clicked(self, index):
        path = self.file_model.fileInfo(index).absoluteFilePath()
        if not os.path.isfile(path) or not path.lower().endswith(".fbx"):
            return
        import_fbx(path)

    def on_file_tree_context_menu(self, pos):
        index = self.file_tree_view.indexAt(pos)

        if not index.isValid():
            return

        path = self.file_model.fileInfo(index).absoluteFilePath()
        if not os.path.isfile(path) or not path.lower().endswith(".fbx"):
            return

        sel = cmds.ls(sl=True)

        menu = QMenu()
        menu.addAction(self.retarget_selected_action)
        # menu.addAction(QAction("Retarget selected", self, triggered=self.import_selected_objs))
        menu.exec_(self.file_tree_view.mapToGlobal(pos))

    def get_selected_paths(self):
        indices = self.file_tree_view.selectedIndexes()
        if not indices:
            return []
        paths = [
            self.file_model.fileInfo(idx).absoluteFilePath()
            for idx in indices
            if idx.column() == 0
        ]
        return paths

    def retarget_selected(self):
        """Import the selected shapes in the tree view.

        If a mesh with a blendshape is selected in the scene, the shapes will be added
        as targets
        """
        indices = self.file_tree_view.selectedIndexes()
        if not indices:
            return None
        paths = self.get_selected_paths()

        # Get the root joint
        root = self.correspondence_widget.target.joints()[0]
        parent = cmds.listRelatives(root, parent=True, path=True)
        while parent and cmds.nodeType(parent[0]) == "joint":
            root = parent[0]
            parent = cmds.listRelatives(root, parent=True, path=True)

        progress = QProgressDialog("Retargeting files...", "Abort", 0, len(paths), self)
        progress.setWindowModality(Qt.WindowModal)
        for i, path in enumerate(paths):
            progress.setValue(i)
            if progress.wasCanceled():
                break
            import_fbx(path)
            output_path = self.export_options.get_export_path(path)
            export_animation_fbx(root, output_path)
        progress.setValue(len(paths))
