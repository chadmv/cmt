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
from __future__ import division
from __future__ import print_function

import json
import os

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import cmt.shortcuts as shortcuts


class StringCache(QStringListModel):
    """A QStringListModel that saves its values in a persistent cache."""

    def __init__(self, name, max_values=10, parent=None):
        """Constructor

        :param name: Name used to query persistent data
        :param max_values: Maximum number of values to store in the cache
        :param parent: QWidget parent
        """
        super(StringCache, self).__init__(parent)
        self._name = name
        self.max_values = max_values
        data = shortcuts.get_setting(self._name)
        if data:
            data = json.loads(data)
            self.setStringList(data)

    def push(self, value):
        """Push a new value onto the cache stack.

        :param value: New value.
        """
        values = self.stringList()
        if value in values:
            values.remove(value)
        values.insert(0, value)
        if len(values) > self.max_values:
            values = values[: self.max_values]
        self.setStringList(values)
        self._save()

    def _save(self):
        """Saves the string list to the persistent cache."""
        shortcuts.set_setting(self._name, json.dumps(self.stringList()))


class FilePathWidget(QWidget):
    """Widget allowing file path selection with a persistent cache.

    Users should connect to the path_changed signal.
    """

    any_file = 0
    existing_file = 1
    directory = 2
    path_changed = Signal(str)

    def __init__(
        self, label=None, file_mode=any_file, file_filter=None, name=None, parent=None
    ):
        """Constructor

        :param label: Optional label text.
        :param file_mode: Sets the file dialog mode.  One of
            FilePathWidget.[any_file|existing_file|directory].
        :param file_filter:  File filter text example 'Python Files (*.py)'.
        :param name: Unique name used to query persistent data.
        :param parent: Parent QWidget.
        """
        super(FilePathWidget, self).__init__(parent)
        self.file_mode = file_mode
        if file_filter is None:
            file_filter = "Any File (*)"
        self.file_filter = file_filter
        self.cache = StringCache("cmt.filepathwidget.{}".format(name), parent=self)
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        if label:
            label = QLabel(label, self)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self._layout.addWidget(label)

        self._combo_box = QComboBox(self)
        self._combo_box.setEditable(True)
        self._combo_box.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self._combo_box.setInsertPolicy(QComboBox.InsertAtTop)
        self._combo_box.setModel(self.cache)
        self._combo_box.editTextChanged.connect(self.edit_changed)
        self._layout.addWidget(self._combo_box)

        button = QPushButton("Browse", self)
        button.released.connect(self.show_dialog)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._layout.addWidget(button)

    @property
    def path(self):
        return self._combo_box.currentText()

    @path.setter
    def path(self, value):
        self._combo_box.setEditText(value)

    def edit_changed(self, text):
        """Slot called whenever the text changes in the combobox.

        :param text: New text.
        """
        if not text:
            return
        text = text.replace("\\", "/")
        if (os.path.isfile(text) and self.file_mode != FilePathWidget.directory) or (
            os.path.isdir(text) and self.file_mode == FilePathWidget.directory
        ):
            self.path_changed.emit(text)
            self._combo_box.blockSignals(True)
            self._push(text)
            self._combo_box.blockSignals(False)

    def show_dialog(self):
        """Show the file browser dialog."""
        dialog = QFileDialog(self)
        dialog.setNameFilter(self.file_filter)
        file_mode = [
            QFileDialog.AnyFile,
            QFileDialog.ExistingFile,
            QFileDialog.Directory,
        ][self.file_mode]
        dialog.setFileMode(file_mode)
        dialog.setModal(True)
        if self.cache:
            dialog.setHistory(self.cache.stringList())

        for value in self.cache.stringList():
            if os.path.exists(value):
                if os.path.isfile(value):
                    directory = os.path.dirname(value)
                    dialog.selectFile(value)
                else:
                    directory = value
                dialog.setDirectory(directory)
                break
        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()
            if path:
                self._push(path[0])

    def _push(self, path):
        """Push a new path onto the cache.

        :param path: Path value.
        """
        self.cache.push(path)
        self._combo_box.setCurrentIndex(0)
