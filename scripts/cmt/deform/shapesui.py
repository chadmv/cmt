"""A UI used to manipulate blendshapes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial
import logging
import os

from PySide2.QtCore import *
from PySide2.QtWidgets import *

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import maya.cmds as cmds

from cmt.ui.widgets.filepathwidget import FilePathWidget
from cmt.ui.stringcache import StringCache
import cmt.deform.blendshape as bs
import cmt.deform.np_mesh as np_mesh

reload(bs)
import cmt.shortcuts as shortcuts
from cmt.io.obj import import_obj, export_obj

logger = logging.getLogger(__name__)
_win = None


def show():
    """Shows the window."""
    global _win
    if _win:
        _win.close()
    _win = ShapesWindow()
    _win.show()


class ShapesWindow(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self, parent=None):
        super(ShapesWindow, self).__init__(parent)
        self.setWindowTitle("Shapes")
        self.resize(800, 600)
        self.create_actions()
        self.create_menu()
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.file_model = QFileSystemModel(self)
        self.root_path = FilePathWidget(
            "Root: ", FilePathWidget.directory, name="cmt.shapes.rootpath", parent=self
        )
        self.root_path.path_changed.connect(self.set_root_path)
        main_layout.addWidget(self.root_path)

        self.file_tree_view = QTreeView()
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.Files | QDir.AllDirs)
        self.file_model.setReadOnly(True)
        self.file_model.setNameFilters(["*.obj"])
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
        main_layout.addWidget(self.file_tree_view)
        self.set_root_path(self.root_path.path)

    def create_actions(self):
        self.propagate_neutral_action = QAction(
            "Propagate Neutral Update",
            toolTip="Propagate updates to a neutral mesh to the selected targets.",
            triggered=self.propagate_neutral_update,
        )

        self.export_selected_action = QAction(
            "Export Selected Meshes",
            toolTip="Export the selected meshes to the selected directory",
            triggered=self.export_selected,
        )

    def create_menu(self):
        menubar = self.menuBar()
        menu = menubar.addMenu("Shapes")
        menu.addAction(self.propagate_neutral_action)
        menu.addAction(self.export_selected_action)

    def set_root_path(self, path):
        index = self.file_model.setRootPath(path)
        self.file_tree_view.setRootIndex(index)

    def on_file_tree_double_clicked(self, index):
        path = self.file_model.fileInfo(index).absoluteFilePath()
        if not os.path.isfile(path) or not path.lower().endswith(".obj"):
            return
        self.import_selected_objs()

    def on_file_tree_context_menu(self, pos):
        index = self.file_tree_view.indexAt(pos)

        if not index.isValid():
            return

        path = self.file_model.fileInfo(index).absoluteFilePath()
        if not os.path.isfile(path) or not path.lower().endswith(".obj"):
            return

        sel = cmds.ls(sl=True)
        blendshape = bs.get_blendshape_node(sel[0]) if sel else None

        menu = QMenu()
        label = "Import as target" if blendshape else "Import"
        menu.addAction(QAction(label, self, triggered=self.import_selected_objs))
        if sel and shortcuts.get_shape(sel[0]):
            menu.addAction(
                QAction(
                    "Export selected", self, triggered=partial(export_obj, sel[0], path)
                )
            )
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

    def import_selected_objs(self, add_as_targets=True):
        """Import the selected shapes in the tree view.

        If a mesh with a blendshape is selected in the scene, the shapes will be added
        as targets
        """
        indices = self.file_tree_view.selectedIndexes()
        if not indices:
            return None
        paths = self.get_selected_paths()

        sel = cmds.ls(sl=True)
        blendshape = bs.get_blendshape_node(sel[0]) if sel else None
        meshes = [import_obj(path) for path in paths]
        if blendshape and add_as_targets:
            for mesh in meshes:
                bs.add_target(blendshape, mesh)
                cmds.delete(mesh)
        elif meshes:
            cmds.select(meshes)
        return meshes

    def export_selected(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        indices = self.file_tree_view.selectedIndexes()
        if indices:
            path = self.file_model.fileInfo(indices[0]).absoluteFilePath()
            directory = os.path.dirname(path) if os.path.isfile(path) else path
        else:
            directory = self.file_model.rootPath()

        for mesh in sel:
            path = os.path.join(directory, "{}.obj".format(mesh))
            export_obj(mesh, path)

    def propagate_neutral_update(self):
        sel = cmds.ls(sl=True)
        if len(sel) != 2:
            QMessageBox.critical(
                self, "Error", "Select the old neutral, then the new neutral."
            )
            return
        old_neutral, new_neutral = sel
        meshes = self.import_selected_objs(add_as_targets=False)
        if not meshes:
            return
        bs.propagate_neutral_update(old_neutral, new_neutral, meshes)
