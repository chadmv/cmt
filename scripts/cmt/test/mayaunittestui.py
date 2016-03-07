"""
Contains a user interface for the CMT testing framework.

The dialog will display all tests found in MAYA_MODULE_PATH and allow the user to selectively run the tests.  The
dialog will also automatically get any code updates without any need to reload if the dialog is opened before any other
tools have been run.

To open the dialog run the menu item: CMT > Utility > Unit Test Runner.

See https://github.com/chadmv/cmt/wiki/Unit-Test-Runner-Dialog
"""
import __builtin__
import os
import sys
import unittest
import webbrowser
from PySide import QtCore
from PySide import QtGui
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

import cmt.test.mayaunittest as mayaunittest
import cmt.shortcuts as shortcuts

ICON_DIR = os.path.join(os.environ['CMT_ROOT_PATH'], 'icons')

_win = None


def show():
    """Shows the browser window."""
    global _win
    if _win:
        _win.close()
    _win = MayaTestRunnerDialog()
    _win.show()


def documentation():
    webbrowser.open('https://github.com/chadmv/cmt/wiki/Unit-Test-Runner-Dialog')


class MayaTestRunnerDialog(MayaQWidgetBaseMixin, QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MayaTestRunnerDialog, self).__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('CMT Unit Test Runner')
        self.resize(1000, 600)
        self.rollback_importer = RollbackImporter()

        menubar = self.menuBar()
        menu = menubar.addMenu('Settings')
        action = menu.addAction('Buffer Output')
        action.setToolTip('Only display output during a failed test.')
        action.setCheckable(True)
        action.setChecked(mayaunittest.Settings.buffer_output)
        action.toggled.connect(mayaunittest.set_buffer_output)
        action = menu.addAction('New Scene Between Test')
        action.setToolTip('Creates a new scene file after each test.')
        action.setCheckable(True)
        action.setChecked(mayaunittest.Settings.file_new)
        action.toggled.connect(mayaunittest.set_file_new)
        menu = menubar.addMenu('Help')
        action = menu.addAction('Documentation')
        action.triggered.connect(documentation)

        toolbar = self.addToolBar('Tools')
        action = toolbar.addAction('Run All Tests')
        action.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_run_all_tests.png'))))
        action.triggered.connect(self.run_all_tests)
        action.setToolTip('Run all tests.')

        action = toolbar.addAction('Run Selected Tests')
        action.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_run_selected_tests.png'))))
        action.setToolTip('Run all selected tests.')
        action.triggered.connect(self.run_selected_tests)

        action = toolbar.addAction('Run Failed Tests')
        action.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_run_failed_tests.png'))))
        action.setToolTip('Run all failed tests.')
        action.triggered.connect(self.run_failed_tests)

        widget = QtGui.QWidget()
        self.setCentralWidget(widget)
        vbox = QtGui.QVBoxLayout(widget)

        splitter = QtGui.QSplitter(orientation=QtCore.Qt.Horizontal)
        self.test_view = QtGui.QTreeView()
        self.test_view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        splitter.addWidget(self.test_view)
        self.output_console = QtGui.QTextEdit()
        self.output_console.setReadOnly(True)
        splitter.addWidget(self.output_console)
        vbox.addWidget(splitter)
        splitter.setStretchFactor(1, 4)
        self.stream = TestCaptureStream(self.output_console)

        test_suite = mayaunittest.get_tests()
        root_node = TestNode(test_suite)
        self.model = TestTreeModel(root_node, self)
        self.test_view.setModel(self.model)
        self.expand_tree(root_node)

    def expand_tree(self, root_node):
        """Expands all the collapsed elements in a tree starting at the root_node"""
        parent = root_node.parent()
        parent_idx = self.model.createIndex(parent.row(), 0, parent) if parent else QtCore.QModelIndex()
        index = self.model.index(root_node.row(), 0, parent_idx)
        self.test_view.setExpanded(index, True)
        for child in root_node.children:
            self.expand_tree(child)

    def run_all_tests(self):
        """Callback method to run all the tests found in MAYA_MODULE_PATH."""
        self.reset_rollback_importer()
        test_suite = unittest.TestSuite()
        mayaunittest.get_tests(test_suite=test_suite)
        self.output_console.clear()
        self.model.run_tests(self.stream, test_suite)

    def run_selected_tests(self):
        """Callback method to run the selected tests in the UI."""
        self.reset_rollback_importer()
        test_suite = unittest.TestSuite()

        indices = self.test_view.selectedIndexes()
        if not indices:
            return

        # Remove any child nodes if parent nodes are in the list.  This will prevent duplicate tests from being run.
        paths = [index.internalPointer().path() for index in indices]
        test_paths = []
        for path in paths:
            tokens = path.split('.')
            for i in range(len(tokens) - 1):
                p = '.'.join(tokens[0:i+1])
                if p in paths:
                    break
            else:
                test_paths.append(path)

        # Now get the tests with the pruned paths
        for path in test_paths:
            mayaunittest.get_tests(test=path, test_suite=test_suite)

        self.output_console.clear()
        self.model.run_tests(self.stream, test_suite)

    def run_failed_tests(self):
        """Callback method to run all the tests with fail or error statuses."""
        self.reset_rollback_importer()
        test_suite = unittest.TestSuite()
        for node in self.model.node_lookup.values():
            if isinstance(node.test, unittest.TestCase) and node.get_status() in {TestStatus.fail, TestStatus.error}:
                mayaunittest.get_tests(test=node.path(), test_suite=test_suite)
        self.output_console.clear()
        self.model.run_tests(self.stream, test_suite)

    def reset_rollback_importer(self):
        """Resets the RollbackImporter which allows the test runner to pick up code updates without having to reload
        anything."""
        if self.rollback_importer:
            self.rollback_importer.uninstall()
        # Create a new rollback importer to pick up any code updates
        self.rollback_importer = RollbackImporter()

    def closeEvent(self, event):
        """Close event to clean up everything."""
        global _win
        self.rollback_importer.uninstall()
        self.deleteLater()
        _win = None


class TestCaptureStream(object):
    """Allows the output of the tests to be displayed in a QTextEdit."""
    success_color = QtGui.QColor(92, 184, 92)
    fail_color = QtGui.QColor(240, 173, 78)
    error_color = QtGui.QColor(217, 83, 79)
    skip_color = QtGui.QColor(88, 165, 204)
    normal_color = QtGui.QColor(200, 200, 200)

    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        """Write text into the QTextEdit."""
        # Color the output
        if text.startswith('ok'):
            self.text_edit.setTextColor(TestCaptureStream.success_color)
        elif text.startswith('FAIL'):
            self.text_edit.setTextColor(TestCaptureStream.fail_color)
        elif text.startswith('ERROR'):
            self.text_edit.setTextColor(TestCaptureStream.error_color)
        elif text.startswith('skipped'):
            self.text_edit.setTextColor(TestCaptureStream.skip_color)

        self.text_edit.insertPlainText(text)
        self.text_edit.setTextColor(TestCaptureStream.normal_color)

    def flush(self):
        pass



class TestStatus:
    """The possible status values of a test."""
    not_run = 0
    success = 1
    fail = 2
    error = 3
    skipped = 4


class TestNode(shortcuts.BaseTreeNode):
    """A node representing a Test, TestCase, or TestSuite for display in a QTreeView."""
    success_icon = QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_test_success.png'))
    fail_icon = QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_test_fail.png'))
    error_icon = QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_test_error.png'))
    skip_icon = QtGui.QPixmap(os.path.join(ICON_DIR, 'cmt_test_skip.png'))

    def __init__(self, test, parent=None):
        super(TestNode, self).__init__(parent)
        self.test = test
        self.tool_tip = str(test)
        self.status = TestStatus.not_run
        if isinstance(self.test, unittest.TestSuite):
            for test_ in self.test:
                if isinstance(test_, unittest.TestCase) or test_.countTestCases():
                    self.add_child(TestNode(test_, self))

    def name(self):
        """Get the name to print in the view."""
        if isinstance(self.test, unittest.TestCase):
            return self.test._testMethodName
        elif isinstance(self.child(0).test, unittest.TestCase):
            return self.child(0).test.__class__.__name__
        else:
            return self.child(0).child(0).test.__class__.__module__

    def path(self):
        """Gets the import path of the test.  Used for finding the test by name."""
        if self.parent() and self.parent().parent():
            return '{0}.{1}'.format(self.parent().path(), self.name())
        else:
            return self.name()

    def get_status(self):
        """Get the status of the TestNode.

        Nodes with children like the TestSuites, will get their status based on the status of the leaf nodes (the
        TestCases).
        @return: A status value from TestStatus.
        """
        if not self.children:
            return self.status
        result = TestStatus.not_run
        for child in self.children:
            child_status = child.get_status()
            if child_status == TestStatus.error:
                # Error status has highest priority so propagate that up to the parent
                return child_status
            elif child_status == TestStatus.fail:
                result = child_status
            elif child_status == TestStatus.success and result != TestStatus.fail:
                result = child_status
            elif child_status == TestStatus.skipped and result != TestStatus.fail:
                result = child_status
        return result

    def get_icon(self):
        """Get the status icon to display with the Test."""
        status = self.get_status()
        return [None,
                TestNode.success_icon,
                TestNode.fail_icon,
                TestNode.error_icon,
                TestNode.skip_icon][status]


class TestTreeModel(QtCore.QAbstractItemModel):
    """The model used to populate the test tree view."""

    def __init__(self, root, parent=None):
        super(TestTreeModel, self).__init__(parent)
        self._root_node = root
        self.node_lookup = {}
        # Create a lookup so we can find the TestNode given a TestCase or TestSuite
        self.create_node_lookup(self._root_node)

    def create_node_lookup(self, node):
        """Create a lookup so we can find the TestNode given a TestCase or TestSuite.  The lookup will be used to set
        test statuses and tool tips after a test run.

        @param node: Node to add to the map.
        """
        self.node_lookup[str(node.test)] = node
        for child in node.children:
            self.create_node_lookup(child)

    def rowCount(self, parent):
        """Return the number of rows with this parent."""
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()
        return parent_node.child_count()

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return node.name()
        elif role == QtCore.Qt.DecorationRole:
            return node.get_icon()
        elif role == QtCore.Qt.ToolTipRole:
            return node.tool_tip

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        node = index.internalPointer()
        if role == QtCore.Qt.EditRole:
            self.dataChanged.emit(index, index)
        if role == QtCore.Qt.DecorationRole:
            node.status = value
            self.dataChanged.emit(index, index)
            if node.parent() is not self._root_node:
                self.setData(self.parent(index), value, role)
        elif role == QtCore.Qt.ToolTipRole:
            node.tool_tip = value
            self.dataChanged.emit(index, index)

    def headerData(self, section, orientation, role):
        return "Tests"

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def parent(self, index):
        node = index.internalPointer()
        parent_node = node.parent()
        if parent_node == self._root_node:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()

        child_item = parent_node.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def get_index_of_node(self, node):
        if node is self._root_node:
            return QtCore.QModelIndex()
        return self.index(node.row(), 0, self.get_index_of_node(node.parent()))

    def run_tests(self, stream, test_suite):
        """Runs the given TestSuite.

        @param stream: A stream object with write functionality to capture the test output.
        @param test_suite: The TestSuite to run.
        """
        runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=mayaunittest.TestResult)
        runner.failfast = False
        runner.buffer = mayaunittest.Settings.buffer_output
        result = runner.run(test_suite)

        self._set_test_result_data(result.failures, TestStatus.fail)
        self._set_test_result_data(result.errors, TestStatus.error)
        self._set_test_result_data(result.skipped, TestStatus.skipped)

        for test in result.successes:
            node = self.node_lookup[str(test)]
            index = self.get_index_of_node(node)
            self.setData(index, 'Test Passed', QtCore.Qt.ToolTipRole)
            self.setData(index, TestStatus.success, QtCore.Qt.DecorationRole)

    def _set_test_result_data(self, test_list, status):
        """Store the test result data in model.

        @param test_list: A list of tuples of test results.
        @param status: A TestStatus value."""
        for test, reason in test_list:
            node = self.node_lookup[str(test)]
            index = self.get_index_of_node(node)
            self.setData(index, reason, QtCore.Qt.ToolTipRole)
            self.setData(index, status, QtCore.Qt.DecorationRole)


class RollbackImporter(object):
    """Used to remove imported modules from the module list.

    This allows tests to be rerun after code updates without doing any reloads.
    From: http://pyunit.sourceforge.net/notes/reloading.html

    Usage:
    def run_tests(self):
        if self.rollback_importer:
            self.rollback_importer.uninstall()
        self.rollback_importer = RollbackImporter()
        self.load_and_execute_tests()
    """
    def __init__(self):
        """Creates an instance and installs as the global importer."""
        self.previous_modules = sys.modules.copy()
        self.real_import = __builtin__.__import__
        __builtin__.__import__ = self._import
        self.new_modules = {}

    def _import(self, name, globals=None, locals=None, fromlist=[]):
        result = apply(self.real_import, (name, globals, locals, fromlist))
        self.new_modules[name] = 1
        return result

    def uninstall(self):
        for modname in self.new_modules.keys():
            if modname not in self.previous_modules.keys():
                # Force reload when modname next imported
                del(sys.modules[modname])
        __builtin__.__import__ = self.real_import
