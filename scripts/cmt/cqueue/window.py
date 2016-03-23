import os
import json
import webbrowser
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


def restore_cursor():
    """Restores the cursor from any custom shape."""
    override_cursor = QtGui.qApp.overrideCursor()
    if override_cursor:
        QtGui.qApp.restoreOverrideCursor()


# Singleton window
_win = None

def show():
    """Shows the CQueue window."""
    global _win
    if _win:
        _win.parent().close()
        _win.parent().deleteLater()
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
        self.component_tree = QtGui.QTreeView()
        self.component_tree.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.component_tree.setDragEnabled(True)
        vbox.addWidget(self.component_tree)
        splitter.addWidget(widget)

        widget = QtGui.QWidget()
        splitter.addWidget(widget)
        vbox = QtGui.QVBoxLayout(widget)
        scroll_area = QtGui.QScrollArea()
        scroll_area.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.queue_widget = QueueWidget(parent=self)
        self.queue_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        scroll_area.setWidget(self.queue_widget)
        scroll_area.setWidgetResizable(True)
        vbox.addWidget(scroll_area)
        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        button = QtGui.QPushButton('Execute')
        button.released.connect(self.queue_widget.execute_queue)
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
        self.queue_widget.set_queue(core.ComponentQueue())

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
            queue = core.load_queue(file_path)
            self.queue_widget.set_queue(queue)
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
            self.queue_widget.queue.export(file_path)

    def add_selected_components_to_queue(self):
        """Adds the selected components in the component tree to the queue."""
        indices = self.component_tree.selectionModel().selectedRows()
        for index in indices:
            node = index.internalPointer()
            if node.children:
                # Only leaf nodes are Components.
                continue
            self.queue_widget.add_component_to_queue(node.component_path)


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
            return node.image(size=32)
        elif role == QtCore.Qt.ToolTipRole:
            return node.tooltip()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return 'Components'

    def flags(self, index):
        fl = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        node = index.internalPointer()
        if not node.children:
            fl |= QtCore.Qt.ItemIsDragEnabled
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

    def mimeTypes(self):
        return 'text/plain'

    def mimeData(self, indices):
        pks = ' '.join([idx.internalPointer().component_path for idx in indices])
        data = QtCore.QMimeData()
        data.setText(pks)
        return data


class QueueWidget(QtGui.QWidget):
    """The ComponentQueue tree view.  Overriden so we can do drag and drop"""
    def __init__(self, queue=None, parent=None):
        super(QueueWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.queue_layout = QtGui.QVBoxLayout(self)
        self.queue_layout.addStretch()
        self.queue = queue if queue else core.ComponentQueue()
        self.drop_indicator = DropIndicator()
        self.hide_indicator()

    def set_queue(self, queue):
        delete_layout_contents(self.queue_layout)
        for comp in queue:
            comp_widget = ComponentWidget(comp, queue, parent=self)
            self.queue_layout.addWidget(comp_widget)
        self.queue_layout.addStretch()
        self.queue = queue

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if not child:
            return
        if not isinstance(child, ComponentWidget):
            return
        pos = child.mapFromParent(event.pos())
        if not child.grab_rect().contains(pos):
            return

        # Create the drag object with the component data we are moving
        mime_data = QtCore.QMimeData()
        mime_data.setText(json.dumps(child.comp.data()))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)
        hotspot = event.pos() - child.pos()
        drag.setHotSpot(hotspot)

        # Resize the indicator so it has the same height as the ComponentWidget we are dragging
        self.drop_indicator.setFixedHeight(child.height())
        QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
        index = self.get_component_index_at_position(event.pos())
        component_widget_index = self.queue_layout.indexOf(child)
        self.queue_layout.takeAt(component_widget_index)
        child.hide()
        self.place_indicator(index)
        if drag.exec_(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
            # The drag reorder was accepted so do the actual move
            drop_indicator_index = self.queue_layout.indexOf(self.drop_indicator)
            self.hide_indicator()
            self.queue_layout.insertWidget(drop_indicator_index, child)
            child.show()
            self.queue.clear()
            components = self.get_ordered_component_widgets()
            for widget in components:
                self.queue.add(widget.comp)
        else:
            self.queue_layout.insertWidget(component_widget_index, child)
            child.show()
        restore_cursor()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            index = self.get_component_index_at_position(event.pos())
            self.place_indicator(index)
            if event.source() in self.children():
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.pos().x() < self.width() and event.pos().y() < self.height():
            index = self.get_component_index_at_position(event.pos())
            self.place_indicator(index)
            if event.source() in self.children():
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()
            else:
                event.setDropAction(QtCore.Qt.CopyAction)
                event.acceptProposedAction()
        else:
            self.hide_indicator()
            event.ignore()

    def place_indicator(self, index):
        if index != self.drop_indicator.index or self.drop_indicator.index == -1:
            indicator_index = self.queue_layout.indexOf(self.drop_indicator)
            if indicator_index > -1:
                self.queue_layout.takeAt(indicator_index)
            self.drop_indicator.index = index
            self.queue_layout.insertWidget(index, self.drop_indicator)
            self.drop_indicator.show()

    def dropEvent(self, event):
        if event.mimeData().hasText() and event.pos().x() < self.width() and event.pos().y() < self.height():
            index = self.drop_indicator.index
            text = event.mimeData().text()
            if '{' in text:
                # We received json serialized component data
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()
            else:
                self.hide_indicator()
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()
                components = [component for component in event.mimeData().text().split()]
                for component_path in components:
                    self.add_component_to_queue(component_path, index)
        else:
            event.ignore()

    def hide_indicator(self):
        indicator_index = self.queue_layout.indexOf(self.drop_indicator)
        if indicator_index != -1:
            self.queue_layout.takeAt(indicator_index)
        self.drop_indicator.hide()
        self.drop_indicator.index = -1

    def get_component_index_at_position(self, position):
        # Snap to the middle so we get over a ComponentWidget
        position.setX(self.width() / 2)
        # If the position is between ComponentWidgets, snap to the next lowest widget.
        components = self.get_ordered_component_widgets()
        index = 0
        for child in components:
            if position.y() < child.pos().y() + child.height() * 0.5:
                break
            index += 1
        return index

    def get_ordered_component_widgets(self):
        """Get the ComponentWidgets ordered top to bottom.

        :return: A list of ComponentWidgets.
        """
        child_count = self.queue_layout.count()
        components = [self.queue_layout.itemAt(i).widget() for i in range(child_count)]
        components = [comp for comp in components if isinstance(comp, ComponentWidget)]
        components.sort(key=lambda node: node.pos().y())
        return components

    def add_component_to_queue(self, component_path, index=None):
        """Adds the selected components in the component tree to the queue."""
        if index is None:
            # If no index is specified, append to the end
            index = self.queue_layout.count() - 1
        comp = component_path if isinstance(component_path, core.Component)\
            else core.load_component_class(component_path)
        self.queue.insert(index, comp)
        comp_widget = ComponentWidget(comp, self.queue, parent=self)
        self.queue_layout.insertWidget(index, comp_widget)

    def execute_queue(self):
        # Reset the execution status of all the ComponentWidgets
        for child in self.children():
            if isinstance(child, ComponentWidget):
                child.set_color(ComponentWidget.normal_color)

        self.queue.execute(on_error=self.on_component_execution_error)

    def on_component_execution_error(self, message, component):
        widget = self.get_component_widget(component)
        if widget:
            widget.set_color(ComponentWidget.error_color)
        msg = QtGui.QMessageBox(self)
        msg.setWindowTitle('Execution Error')
        msg.setText('Component {0} failed to execute.'.format(component.name()))
        msg.setDetailedText(message)
        msg.setIcon(QtGui.QMessageBox.Critical)
        # Need to spacer to set the message box width since setFixedWidth does not work.
        spacer = QtGui.QSpacerItem(500, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        layout = msg.layout()
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        msg.show()

    def get_component_widget(self, component):
        """Get the ComponentWidget of a Component.

        :param component: A Component instance.
        :return: The ComponentWidget of the Componenent.
        """
        for child in self.children():
            if isinstance(child, ComponentWidget) and child.comp is component:
                return child
        return None


class ComponentWidget(QtGui.QFrame):
    """The widget used to display a Component in the ComponentQueue."""
    normal_color = QtGui.QColor(72, 170, 181)
    error_color = QtGui.QColor(217, 83, 79)
    break_point_disabled_icon = QtGui.QIcon(QtGui.QPixmap(':/stopClip.png'))
    break_point_enabled_icon = QtGui.QIcon(QtGui.QPixmap(':/timestop.png'))

    def __init__(self, comp, queue, parent=None):
        super(ComponentWidget, self).__init__(parent)
        self.setMouseTracking(True)
        self.queue_layout = parent.queue_layout
        self.queue = queue
        self.comp = comp
        vbox = QtGui.QVBoxLayout(self)
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        self.over_grab_hotspot = False
        self.color = ComponentWidget.normal_color

        # Header
        hbox = QtGui.QHBoxLayout()
        self.header_layout = hbox
        hbox.setContentsMargins(16, 4, 4, 4)
        vbox.addLayout(hbox)

        # Expand toggle
        expand_action = QtGui.QAction('Toggle', self)
        expand_action.setCheckable(True)
        icon = QtGui.QIcon(QtGui.QPixmap(':/arrowDown.png'))
        expand_action.setIcon(icon)
        expand_action.setToolTip('Toggle details')
        expand_action.setStatusTip('Toggle details')
        button = QtGui.QToolButton()
        button.setDefaultAction(expand_action)
        hbox.addWidget(button)

        # Enable checkbox
        enabled = QtGui.QCheckBox()
        enabled.setToolTip('Enable/Disable Component')
        hbox.addWidget(enabled)

        # Breakpoint
        self.break_point_action = QtGui.QAction('Breakpoint', self)
        self.break_point_action.setCheckable(True)
        self.break_point_action.setIcon(self.break_point_disabled_icon)
        self.break_point_action.setToolTip('Set break point at component.')
        self.break_point_action.setStatusTip('Set break point at component.')
        self.break_point_action.toggled.connect(self.set_break_point)
        button = QtGui.QToolButton()
        button.setDefaultAction(self.break_point_action)
        hbox.addWidget(button)

        # Execute button
        action = QtGui.QAction('Execute', self)
        icon = QtGui.QIcon(QtGui.QPixmap(':/timeplay.png'))
        action.setIcon(icon)
        action.setToolTip('Execute the component')
        action.setStatusTip('Execute the component')
        action.triggered.connect(partial(self.execute_component, on_error=parent.on_component_execution_error))
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        # Image label
        label = QtGui.QLabel()
        label.setPixmap(comp.image(size=24))
        label.setToolTip(comp.__class__.__doc__)
        hbox.addWidget(label)

        # Name label
        label = QtGui.QLabel(comp.name().split('.')[-1])
        label.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        label.setToolTip(comp.__class__.__doc__)
        font = QtGui.QFont()
        font.setPointSize(14)
        label.setFont(font)
        hbox.addWidget(label)
        hbox.addStretch()

        if comp.help_url():
            action = QtGui.QAction('Help', self)
            icon = QtGui.QIcon(QtGui.QPixmap(':/help.png'))
            action.setIcon(icon)
            action.setToolTip('Open help documentation.')
            action.setStatusTip('Open help documentation.')
            action.triggered.connect(partial(webbrowser.open, comp.help_url()))
            button = QtGui.QToolButton()
            button.setDefaultAction(action)
            hbox.addWidget(button)

        action = QtGui.QAction('Delete', self)
        icon = QtGui.QIcon(QtGui.QPixmap(':/smallTrash.png'))
        action.setIcon(icon)
        message = 'Delete Component'
        action.setToolTip(message)
        action.setStatusTip(message)
        action.triggered.connect(partial(self.remove, prompt=True))
        button = QtGui.QToolButton()
        button.setDefaultAction(action)
        hbox.addWidget(button)

        content_widget = QtGui.QWidget()
        content_layout = QtGui.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 8, 0, 0)
        vbox.addWidget(content_widget)
        comp.draw(content_layout)
        enabled.toggled.connect(content_widget.setEnabled)
        enabled.setChecked(comp.enabled)
        enabled.toggled.connect(comp.set_enabled)
        expand_action.toggled.connect(content_widget.setVisible)
        content_widget.setVisible(False)
        content_layout.addStretch()

    def execute_component(self, on_error):
        self.set_color(ComponentWidget.normal_color)
        self.comp.capture_execute(on_error=on_error)

    def set_break_point(self, value):
        self.comp.break_point = value
        icon = self.break_point_enabled_icon if value else self.break_point_disabled_icon
        self.break_point_action.setIcon(icon)

    def grab_rect(self):
        """Get the rectangle describing the grab hotspot."""
        return QtCore.QRect(0, 0, 16, self.height()-1)

    def set_color(self, color):
        """Set the color of status bar on the widget.

        :param color: The new color.
        """
        self.color = color
        self.update()

    def paintEvent(self, event):
        """Override the paintEvent to draw the grab hotspot.

        :param event:
        """
        super(ComponentWidget, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.color)
        painter.drawRect(self.grab_rect())

    def mouseMoveEvent(self, event):
        contains = self.grab_rect().contains(event.pos())
        if contains and not self.over_grab_hotspot:
            QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
            self.over_grab_hotspot = True
        elif not contains and self.over_grab_hotspot:
            restore_cursor()
            self.over_grab_hotspot = False

    def leaveEvent(self, event):
        if self.over_grab_hotspot:
            restore_cursor()
            self.over_grab_hotspot = False

    def move(self, new_index):
        """Move the component to the specified index in the queue.

        :param new_index: Index to move to.
        """
        index = self.index()
        # Reorder the Component in the Queue
        self.queue.remove(index)

        if new_index and new_index > self.queue.length():
            # When we are moving a component to the bottom, the index may get greater than the max allowed
            new_index = self.queue.length()

        self.queue.insert(new_index, self.comp)
        # Reorder the ComponentWidget in the layout
        self.queue_layout.takeAt(index)
        self.queue_layout.insertWidget(new_index, self)

    def index(self):
        """Get the index of the Component. """
        return self.queue.index(self.comp)

    def remove(self, prompt=False):
        """Remove this Component from the queue.

        :param prompt: True to display a message box confirming the removal of the Component.
        """
        if prompt:
            msg_box = QtGui.QMessageBox()
            msg_box.setIcon(QtGui.QMessageBox.Question)
            msg_box.setText('Are you sure you want to remove this component?')
            msg_box.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
            if msg_box.exec_() != QtGui.QMessageBox.Yes:
                return
        index = self.queue.index(self.comp)
        self.queue.remove(index)
        self.queue_layout.takeAt(index)
        self.deleteLater()


class DropIndicator(QtGui.QWidget):
    """The widget used to display a Component in the ComponentQueue."""

    def __init__(self, parent=None):
        super(DropIndicator, self).__init__(parent)
        self.setFixedHeight(45)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(72, 170, 181)
        painter.setPen(color)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
