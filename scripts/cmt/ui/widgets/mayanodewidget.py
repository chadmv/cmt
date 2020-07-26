"""A widget to select a file path.

The widget stores previously selected paths in QSettings

Example
-------
def func(t):
    print(t)

from cmt.widgets.filepathwidget import FilePathWidget
widget = FilePathWidget(label='My File',
                        file_mode=FilePathWidget.existing_file,
                        name='unique_name',
                        file_filter='Python Files (*.py)')
widget.path_changed.connect(func)
widget.show()
"""

from __future__ import absolute_import
from __future__ import print_function

import os

from PySide2.QtCore import Signal
from PySide2.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
    QPushButton,
)

import maya.cmds as cmds

import cmt.shortcuts as shortcuts
from cmt.ui.stringcache import StringCache


class MayaNodeWidget(QWidget):
    """Widget allowing Maya node selection with a persistent cache.

    Users should connect to the node_changed signal.
    """

    node_changed = Signal(str)

    def __init__(self, label=None, name=None, parent=None):
        """Constructor

        :param label: Optional label text.
        :param name: Unique name used to query persistent data.
        :param parent: Parent QWidget.
        """
        super(MayaNodeWidget, self).__init__(parent)
        self.cache = StringCache("cmt.mayanodewidget.{}".format(name), parent=self)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        if label:
            label = QLabel(label, self)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self._layout.addWidget(label)

        self._combo_box = QComboBox(self)
        self._combo_box.setEditable(True)
        self._combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._combo_box.setInsertPolicy(QComboBox.InsertAtTop)
        self._combo_box.setModel(self.cache)
        self._combo_box.editTextChanged.connect(self.edit_changed)
        self._layout.addWidget(self._combo_box)

        button = QPushButton("<", self)
        button.released.connect(self.use_selected)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._layout.addWidget(button)

    @property
    def node(self):
        return self._combo_box.currentText()

    @node.setter
    def node(self, value):
        self._combo_box.setEditText(value)

    def edit_changed(self, text):
        """Slot called whenever the text changes in the combobox.

        :param text: New text.
        """
        if not text:
            return
        if cmds.objExists(text):
            self.node_changed.emit(text)
            self._combo_box.blockSignals(True)
            self._push(text)
            self._combo_box.blockSignals(False)

    def use_selected(self):
        """Populate the combobox with the name of the selected node."""
        selected = cmds.ls(sl=True)
        if selected:
            self._push(selected[0])

    def _push(self, node):
        """Push a new node onto the cache.

        :param path: Node name.
        """
        self.cache.push(node)
        self._combo_box.setCurrentIndex(0)
