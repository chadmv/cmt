import os
from functools import partial
from PySide import QtGui
from PySide import QtCore
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import cmt.shortcuts as shortcuts
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields

COMPONENT_FOLDER = 0
COMPONENT_ITEM = 1
SETTINGS = QtCore.QSettings('CMT', 'cqueue')
SETTINGS_QUEUES = 'cqueue_queues'


def delete_layout_contents(layout):
    """Delete the contents of a layout.

    :param layout: The layout to clear.
    """
    try:
        count = layout.count()
    except AttributeError:
        count = 0
    for i in range(count):
        widget = layout.takeAt(0)
        try:
            widget.widget().deleteLater()
        except AttributeError:
            delete_layout_contents(widget)


def get_recent_queues():
    """Gets the recent queues saved in the settings."""
    values = []
    if SETTINGS.contains(SETTINGS_QUEUES):
        value = SETTINGS.value(SETTINGS_QUEUES)
        values = [str(x) for x in value if os.path.exists(str(x))]
    return values


def save_recent_queues(latest_file_path):
    """Saves a path to the list of recent queue files.

    :param latest_file_path: The path to add to the list of recent queues.
    """
    values = get_recent_queues()
    try:
        values.remove(latest_file_path)
    except ValueError:
        pass
    if len(values) > 10:
        # Only keep the latest 10 files.
        values.pop()
    values.insert(0, latest_file_path)
    SETTINGS.setValue(SETTINGS_QUEUES, values)


# Singleton window
_win = None

def show():
    """Shows the CQueue window."""
    global _win
    if _win is None:
        _win = CQueueWindow()
    _win.show(dockable=True)
    _win.parent().setAcceptDrops(True)


class CQueueWindow(MayaQWidgetDockableMixin, QtGui.QMainWindow):
    """The window used to load published assets into a shot."""

    def __init__(self, parent=None):
        super(CQueueWindow, self).__init__(parent)
        self.setWindowTitle('CQueue')
        self.setObjectName('CQueueWindow')
        self.resize(1280, 600)
        self.queue = core.ComponentQueue()
        self.recent_menu = None
        self.create_menu()

        main_widget = QtGui.QWidget(self)
        main_vbox = QtGui.QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        splitter = QtGui.QSplitter()
        splitter.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        main_vbox.addWidget(splitter)

        # Create the list of available components
        widget = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout(widget)
        vbox.setContentsMargins(0, 0, 0, 0)
        button = QtGui.QPushButton('Add Components to Queue')
        button.released.connect(self.add_selected_components_to_queue)
        vbox.addWidget(button)
        self.component_tree = QtGui.QTreeView()
        self.component_tree.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        vbox.addWidget(self.component_tree)
        splitter.addWidget(widget)

        widget = QtGui.QWidget()
        splitter.addWidget(widget)
        vbox = QtGui.QVBoxLayout(widget)
        scroll_area = QtGui.QScrollArea()
        scroll_area.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.queue_widget = QtGui.QWidget()
        self.queue_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.queue_layout = QtGui.QVBoxLayout(self.queue_widget)
        self.queue_layout.addStretch()
        scroll_area.setWidget(self.queue_widget)
        scroll_area.setWidgetResizable(True)
        vbox.addWidget(scroll_area)
        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        button = QtGui.QPushButton('Execute')
        button.released.connect(self.execute_queue)
        hbox.addWidget(button)

        splitter.setSizes([50, 300])
        splitter.setStretchFactor(0, 0.5)

        self.populate_components()

    def populate_components(self):
        """Populates the component tree with the available components"""
        root_node = ComponentNode(None)
        components = core.get_components()
        comp_lookup = {}
        for comp in components:
            tokens = comp.split('.')
            parent = root_node
            path_tokens = []
            for token in tokens:
                path_tokens.append(token)
                path = '.'.join(path_tokens)
                node_parent = comp_lookup.get(path)
                if not node_parent:
                    parent = ComponentNode(path, parent)
                    comp_lookup[path] = parent
                else:
                    parent = node_parent
        model = ComponentModel(root_node)
        self.component_tree.setModel(model)
        self.expand_tree(root_node, model)

    def expand_tree(self, root_node, model):
        """Expands all the collapsed elements in a tree starting at the root_node."""
        parent = root_node.parent()
        parent_idx = model.createIndex(parent.row(), 0, parent) if parent else QtCore.QModelIndex()
        index = model.index(root_node.row(), 0, parent_idx)
        self.component_tree.setExpanded(index, True)
        for child in root_node.children:
            self.expand_tree(child, model)

    def create_menu(self):
        """Creates the menu."""
        menubar = self.menuBar()

        # File Menu
        menu = menubar.addMenu('File')

        action = QtGui.QAction('New', self)
        action.triggered.connect(self.new_queue)
        message = 'Create a new component queue.'
        action.setToolTip(message)
        action.setStatusTip(message)
        menu.addAction(action)

        action = QtGui.QAction('Load Queue', self)
        action.triggered.connect(self.load_queue)
        message = 'Load a queue from disk.'
        action.setToolTip(message)
        action.setStatusTip(message)
        menu.addAction(action)

        action = QtGui.QAction('Save Queue', self)
        action.triggered.connect(self.save_queue)
        message = 'Save the current queue to disk.'
        action.setToolTip(message)
        action.setStatusTip(message)
        menu.addAction(action)

        self.recent_menu = QtGui.QMenu('Recent Queues', menu)
        menu.addMenu(self.recent_menu)
        self.populate_recent_queue_menu()

    def populate_recent_queue_menu(self):
        """Populates the recent queue menu."""
        self.recent_menu.clear()
        for queue in get_recent_queues():
            action = QtGui.QAction(queue, self)
            action.triggered.connect(partial(self.load_queue, queue))
            self.recent_menu.addAction(action)

    def new_queue(self):
        """Clears the current queue and makes a new queue."""
        self.queue = core.ComponentQueue()
        self.display_queue(self.queue)

    def load_queue(self, file_path=None):
        """Load the specified queue.  If not queue is specified, display a dialog to load a queue from disk.

        :param file_path: Optional path of a queue to load.
        """
        if file_path is None:
            file_path = QtGui.QFileDialog.getOpenFileName(self,
                                                          'Load Component Queue',
                                                          '',
                                                          'json files (*.json)',
                                                          '',
                                                          QtGui.QFileDialog.DontUseNativeDialog)[0]
        if file_path:
            self.queue = core.load_queue(file_path)
            self.display_queue(self.queue)
            save_recent_queues(file_path)
            self.populate_recent_queue_menu()

    def save_queue(self):
        """Display a dialog to save a queue to disk."""
        file_path = QtGui.QFileDialog.getSaveFileName(self,
                                                      'Save Component Queue',
                                                      '',
                                                      'json files (*.json)',
                                                      '',
                                                      QtGui.QFileDialog.DontUseNativeDialog)[0]
        if file_path:
            self.queue.export(file_path)

    def display_queue(self, queue):
        """Renders the queue in the queue panel.

        :param queue: ComponentQueue to display.
        """
        delete_layout_contents(self.queue_layout)
        for comp in queue:
            comp_widget = ComponentWidget(comp, queue, self)
            self.queue_layout.addWidget(comp_widget)
        self.queue_layout.addStretch()

    def add_selected_components_to_queue(self):
        """Adds the selected components in the component tree to the queue."""
        indices = self.component_tree.selectionModel().selectedRows()
        # We want to insert the widgets before the stretch so get last index
        last = self.queue_layout.count() - 1
        for index in indices:
            node = index.internalPointer()
            if node.children:
                # Only leaf nodes are Components.
                continue
            comp = core.load_component_class(node.component_path)
            self.queue.add(comp)
            comp_widget = ComponentWidget(comp, self.queue, self)
            self.queue_layout.insertWidget(last, comp_widget)
            last += 1

    def execute_queue(self):
        self.queue.execute()


class ComponentNode(shortcuts.BaseTreeNode):
    """The node that will be added to the tree model to display the components."""
    def __init__(self, component_path, parent=None):
        super(ComponentNode, self).__init__(parent)
        self.component_path = component_path
        self.name = self.component_path.split('.')[-1] if component_path else None
        if component_path:
            self.component_class = core.get_component_class(component_path)
        else:
            self.component_class = None

    def image(self, size=32):
        if self.component_class:
            return self.component_class.image(size)

    def tooltip(self):
        return self.component_class.__doc__ if self.component_class else self.component_path


class ComponentModel(QtCore.QAbstractItemModel):
    """The model used to show all the components in the component tree."""

    def __init__(self, root=None, parent=None):
        super(ComponentModel, self).__init__(parent)
        self._root_node = root

    def rowCount(self, parent):
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
            return node.name
        elif role == QtCore.Qt.DecorationRole:
            return node.image()
        elif role == QtCore.Qt.ToolTipRole:
            return node.tooltip()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return 'Components'

    def flags(self, index):
        fl = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return fl

    def parent(self, index):
        if not index.isValid() or not index.internalPointer():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()
        if parent_item == self._root_node:
            return QtCore.QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()

        child_item = parent_node.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()


class ComponentWidget(QtGui.QFrame):
    """The widget used to display a Component in the ComponentQueue."""
    def __init__(self, comp, queue, parent=None):
        super(ComponentWidget, self).__init__(parent)
        self.queue_layout = parent.queue_layout
        self.queue = queue
        self.comp = comp
        vbox = QtGui.QVBoxLayout(self)
        self.setFrameStyle(QtGui.QFrame.StyledPanel)

        # Header
        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        enabled = QtGui.QCheckBox()
        enabled.setToolTip('Enable/Disable Component')
        hbox.addWidget(enabled)
        # Image label
        label = QtGui.QLabel()
        label.setPixmap(comp.image())
        hbox.addWidget(label)
        # Name label
        label = QtGui.QLabel(comp.name().split('.')[-1])
        label.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        font = QtGui.QFont()
        font.setPointSize(14)
        label.setFont(font)
        hbox.addWidget(label)
        hbox.addStretch()

        action = QtGui.QAction('Execute', self)
        icon = QtGui.QIcon(QtGui.QPixmap(':/timeplay.png'))
        action.setIcon(icon)
        action.setToolTip('Execute the component')
        action.setStatusTip('Execute the component')
        action.triggered.connect(comp.execute)
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        action = QtGui.QAction('Up', self)
        icon = QtGui.QIcon(QtGui.QPixmap(':/nudgeUp.png'))
        action.setIcon(icon)
        action.setToolTip('Move up')
        action.setStatusTip('Move up')
        action.triggered.connect(self.move_up)
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        action = QtGui.QAction('Down', self)
        icon = QtGui.QIcon(QtGui.QPixmap(':/nudgeDown.png'))
        action.setIcon(icon)
        action.setToolTip('Move down')
        action.setStatusTip('Move down')
        action.triggered.connect(self.move_down)
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        action = QtGui.QAction('Delete', self)
        icon = QtGui.QIcon(QtGui.QPixmap(':/smallTrash.png'))
        action.setIcon(icon)
        message = 'Delete Component'
        action.setToolTip(message)
        action.setStatusTip(message)
        action.triggered.connect(self.remove)
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        action = QtGui.QAction('Toggle', self)
        action.setCheckable(True)
        icon = QtGui.QIcon(QtGui.QPixmap(':/arrowDown.png'))
        action.setIcon(icon)
        action.setToolTip('Toggle details')
        action.setStatusTip('Toggle details')
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        widget = QtGui.QFrame()
        widget.setFrameStyle(QtGui.QFrame.HLine)
        vbox.addWidget(widget)

        content_widget = QtGui.QWidget()
        content_layout = QtGui.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(content_widget)
        comp.draw(content_layout)
        enabled.toggled.connect(content_widget.setEnabled)
        enabled.setChecked(comp.enabled)
        enabled.toggled.connect(comp.set_enabled)
        action.toggled.connect(content_widget.setVisible)
        content_widget.setVisible(False)
        content_layout.addStretch()

    def move_up(self):
        """Move this Component up in the queue."""
        index = self.queue.index(self.comp)
        if index == 0:
            # Already at the top
            return
        # Reorder the Component in the Queue
        self.queue.remove(index)
        self.queue.insert(index-1, self.comp)
        # Reorder the ComponentWidget in the layout
        self.queue_layout.takeAt(index)
        self.queue_layout.insertWidget(index-1, self)

    def move_down(self):
        """Move this Component down in the queue."""
        index = self.queue.index(self.comp)
        if index == self.queue.length() - 1:
            # Already at the bottom
            return
        # Reorder the Component in the Queue
        self.queue.remove(index)
        self.queue.insert(index+1, self.comp)
        # Reorder the ComponentWidget in the layout
        self.queue_layout.takeAt(index)
        self.queue_layout.insertWidget(index+1, self)

    def remove(self):
        """Remove this Component from the queue."""
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Question)
        msg_box.setText('Are you sure you want to remove this component?')
        msg_box.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
        if msg_box.exec_() == QtGui.QMessageBox.Yes:
            index = self.queue.index(self.comp)
            self.queue.remove(index)
            self.queue_layout.takeAt(index)
            self.deleteLater()