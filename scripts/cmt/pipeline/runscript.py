"""A tool used to run Python scripts on disk."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial
import logging
import os
import runpy

from PySide2.QtCore import *
from PySide2.QtWidgets import *

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
from cmt.ui.widgets.filepathwidget import FilePathWidget
from cmt.ui.stringcache import StringCache

logger = logging.getLogger(__name__)


def run_script(file_path, init_globals=None):
    """Execute the code at the named filesystem location.

    The supplied path may refer to a Python source file, a compiled bytecode file or a
    valid sys.path entry containing a __main__ module.

    :param file_path: File path
    :param init_globals: Optional dictionary to populate the module's globals
    """
    if init_globals is None:
        init_globals = dict()
    file_path = os.path.realpath(file_path)
    logger.info("Running {}".format(file_path))
    runpy.run_path(file_path, init_globals, "__main__")


_win = None


def show():
    """Shows the window."""
    global _win
    if _win:
        _win.close()
    _win = RunScriptWindow()
    _win.show()


class RunScriptWindow(MayaQWidgetBaseMixin, QMainWindow):
    """The RunScriptWindow allows the user to browse for and run Python scripts on disk.
    """

    def __init__(self, parent=None):
        super(RunScriptWindow, self).__init__(parent)
        self.setWindowTitle("Run Script")
        self.resize(800, 600)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.file_model = QFileSystemModel(self)
        self.root_path = FilePathWidget(
            "Root: ",
            FilePathWidget.directory,
            name="cmt.runscript.rootpath",
            parent=self,
        )
        self.root_path.path_changed.connect(self.set_root_path)
        main_layout.addWidget(self.root_path)

        splitter = QSplitter(self)
        main_layout.addWidget(splitter)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.recent_list = RecentList(self)
        splitter.addWidget(self.recent_list)

        self.file_tree_view = QTreeView()
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.Files | QDir.AllDirs)
        self.file_model.setReadOnly(True)
        self.file_model.setNameFilters(["*.py"])
        self.file_model.setNameFilterDisables(False)
        self.file_tree_view.setModel(self.file_model)
        self.file_tree_view.setColumnHidden(1, True)
        self.file_tree_view.setColumnHidden(2, True)
        self.file_tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree_view.customContextMenuRequested.connect(
            self.on_file_tree_context_menu
        )
        self.file_tree_view.doubleClicked.connect(self.on_file_tree_double_clicked)
        splitter.addWidget(self.file_tree_view)

        splitter.setSizes([200, 400])
        self.set_root_path(self.root_path.path)

    def set_root_path(self, path):
        index = self.file_model.setRootPath(path)
        self.file_tree_view.setRootIndex(index)

    def on_file_tree_double_clicked(self, index):
        path = self.file_model.fileInfo(index).absoluteFilePath()
        if not os.path.isfile(path) or not path.endswith(".py"):
            return
        self.run_script(path)

    def on_file_tree_context_menu(self, pos):
        index = self.file_tree_view.indexAt(pos)

        if not index.isValid():
            return

        path = self.file_model.fileInfo(index).absoluteFilePath()
        if not os.path.isfile(path) or not path.endswith(".py"):
            return
        self.create_context_menu(path, self.file_tree_view.mapToGlobal(pos))

    def create_context_menu(self, path, pos):
        menu = QMenu()
        menu.addAction(
            QAction("Run Script", self, triggered=partial(self.run_script, path))
        )
        menu.exec_(pos)

    def run_script(self, path):
        self.recent_list.recents.push(path)
        run_script(path)


class RecentList(QListView):
    """List view providing quick access to recently run scripts."""

    def __init__(self, parent=None):
        super(RecentList, self).__init__(parent)
        self.recents = StringCache("cmt.runscript.recents", max_values=20)
        self.setModel(self.recents)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_recents_context_menu)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.on_recents_double_clicked)

    def on_recents_double_clicked(self, index):
        path = self.recents.data(index, Qt.DisplayRole)
        run_script(path)

    def on_recents_context_menu(self, pos):
        index = self.indexAt(pos)
        path = self.recents.data(index, Qt.DisplayRole)

        menu = QMenu()
        menu.addAction(QAction("Run Script", self, triggered=partial(run_script, path)))
        menu.exec_(self.mapToGlobal(pos))
