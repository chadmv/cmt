"""Contains the attribute Field types.  The Fields are pre-made classes that the Components should use
in order to facilitate in the rendering of the available arguments in the taskassembler ui.
"""

from PySide import QtGui
from functools import partial
import maya.cmds as cmds


class Field(object):
    """Base class for all field types.

    Derived classes should implement the widget, value, and copy methods.
    """

    def __init__(self, name=None, value=None, help_text=''):
        """Constructor.  No QWidgets should be created in the constructor or else Maya will crash
        in batch/testing mode."""
        self.name = name
        self._value = value
        self.help_text = help_text

    def widget(self):
        """Get the QWidget of the Field."""
        raise NotImplementedError('No widget implemented for Field.')

    def value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def copy(self):
        """Returns a copy of the Field.

        The copy method is required for support with the

        """
        raise NotImplementedError('No copy implemented for Field.')


class BooleanField(Field):
    """A checkbox field that holds True or False."""

    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(*args, **kwargs)
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        self._widget = QtGui.QCheckBox(self.name)
        self._widget.setChecked(self._value)
        self._widget.setToolTip(self.help_text)
        return self._widget

    def value(self):
        return self._widget.isChecked() if self._widget else self._value

    def set_value(self, value):
        super(BooleanField, self).set_value(value)
        if self._widget:
            self._widget.setChecked(value)

    def copy(self):
        """Returns a copy of the Field"""
        return BooleanField(name=self.name, value=self.value(), help_text=self.help_text)


class CharField(Field):
    """A Field that holds a string value."""

    def __init__(self, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtGui.QLabel(self.name)
        label.setToolTip(self.help_text)
        hbox.addWidget(label)
        self._widget = QtGui.QLineEdit(self._value)
        self._widget.setToolTip(self.help_text)
        hbox.addWidget(self._widget)
        return widget

    def value(self):
        return self._widget.text() if self._widget else self._value

    def set_value(self, value):
        super(CharField, self).set_value(value)
        if self._widget:
            self._widget.setText(value)

    def copy(self):
        """Returns a copy of the Field"""
        return CharField(name=self.name, value=self.value(), help_text=self.help_text)


class FloatField(Field):
    """A Field that holds a float value."""

    def __init__(self, min_value=0.0, max_value=100.0, precision=2, single_step=0.1,
                 *args, **kwargs):
        super(FloatField, self).__init__(*args, **kwargs)
        self._widget = None
        self.min_value = min_value
        self.max_value = max_value
        self.precision = precision
        self.single_step = single_step

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtGui.QLabel(self.name)
        label.setToolTip(self.help_text)
        hbox.addWidget(label)
        self._widget = QtGui.QDoubleSpinBox()
        self._widget.setValue(self._value)
        self._widget.setRange(self.min_value, self.max_value)
        self._widget.setDecimals(self.precision)
        self._widget.setSingleStep(self.single_step)
        self._widget.setToolTip(self.help_text)
        hbox.addWidget(self._widget)
        return widget

    def value(self):
        return self._widget.value() if self._widget else self._value

    def set_value(self, value):
        super(FloatField, self).set_value(value)
        if self._widget:
            self._widget.setValue(value)

    def copy(self):
        """Returns a copy of the Field"""
        return FloatField(name=self.name, value=self.value(), help_text=self.help_text,
                          min_value=self.min_value, max_value=self.max_value,
                          precision=self.precision, single_step=self.single_step)


class ChoiceField(Field):
    """A Field with a dropdown."""

    def __init__(self, choices, *args, **kwargs):
        super(ChoiceField, self).__init__(*args, **kwargs)
        self._widget = None
        self.choices = choices
        if not self._value:
            self._value = choices[0]

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtGui.QLabel(self.name)
        label.setToolTip(self.help_text)
        hbox.addWidget(label)
        self._widget = QtGui.QComboBox()
        self._widget.setToolTip(self.help_text)
        self._widget.addItems(self.choices)
        self._widget.setCurrentIndex(self._widget.findText(self._value))
        hbox.addWidget(self._widget)
        return widget

    def value(self):
        return self._widget.currentText() if self._widget else self._value

    def set_value(self, value):
        super(ChoiceField, self).set_value(value)
        if self._widget:
            self._widget.setCurrentIndex(self._widget.setCurrentIndex(value))

    def copy(self):
        """Returns a copy of the Field"""
        return ChoiceField(choices=self.choices, name=self.name, value=self.value(),
                           help_text=self.help_text)


class FilePathField(Field):
    """A Field that holds a file path and presents a Browse file dialog."""

    def __init__(self, filter='Any File (*)', *args, **kwargs):
        super(FilePathField, self).__init__(*args, **kwargs)
        self.filter = filter
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtGui.QLabel(self.name)
        label.setToolTip(self.help_text)
        hbox.addWidget(label)
        self._widget = QtGui.QLineEdit(self._value)
        self._widget.setToolTip(self.help_text)
        hbox.addWidget(self._widget)
        button = QtGui.QPushButton('Browse')
        button.released.connect(self.browse)
        hbox.addWidget(button)
        return widget

    def browse(self):
        root = cmds.workspace(q=True, rd=True)
        file_path = cmds.fileDialog2(fileFilter=self.filter, dialogStyle=2, caption=self.name,
                                     fileMode=1, returnFilter=False, startingDirectory=root)
        if file_path:
            self._widget.setText(file_path[0])

    def value(self):
        return self._widget.text() if self._widget else self._value

    def set_value(self, value):
        super(FilePathField, self).set_value(value)
        if self._widget:
            self._widget.setText(value)

    def copy(self):
        """Returns a copy of the Field"""
        return FilePathField(name=self.name, value=self.value(), help_text=self.help_text,
                             filter=self.filter)


class MayaNodeField(Field):
    """A Field that holds the name of a Maya node and presents a set from selected button."""

    def __init__(self, *args, **kwargs):
        super(MayaNodeField, self).__init__(*args, **kwargs)
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtGui.QLabel(self.name)
        label.setToolTip(self.help_text)
        hbox.addWidget(label)
        self._widget = QtGui.QLineEdit(self._value)
        self._widget.setToolTip(self.help_text)
        hbox.addWidget(self._widget)
        button = QtGui.QPushButton('Set')
        button.setToolTip('Populate the field with the selected node.')
        button.released.connect(self.set_from_selected)
        hbox.addWidget(button)
        return widget

    def set_from_selected(self):
        """Populate the QLineEdit from the first selected node."""
        sel = cmds.ls(sl=True)
        if sel:
            self._widget.setText(sel[0])

    def value(self):
        return self._widget.text() if self._widget else self._value

    def set_value(self, value):
        super(MayaNodeField, self).set_value(value)
        if self._widget:
            self._widget.setText(value)

    def copy(self):
        """Returns a copy of the Field"""
        return MayaNodeField(name=self.name, value=self.value(), help_text=self.help_text)


class ContainerField(object):
    """A field that can contain many other fields.  This is usually used with ArrayField to add
    multiple groups of Fields.  It can also be use to orient groups of Fields horizontally or
    vertically.
    """
    horizontal = 0
    vertical = 1

    def __init__(self, orientation=horizontal, border=True):
        """Constructor
        :param orientation: ContainerField.horizontal or ContainerField.vertical.
        :param border: True to display a border around the container.
        """
        self.orientation = orientation
        self.border = border
        self.fields = []

    def __getitem__(self, index):
        """Get the Field at the specified index.

        :param index: Index of the field in the Container.
        :raises: IndexError if the index is out of range.
        """
        return self.fields[index]

    def add_field(self, field):
        """Add a new Field to the container.

        :param field: Field to add.
        """
        self.fields.append(field)

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QFrame()
        if self.border:
            widget.setFrameStyle(QtGui.QFrame.StyledPanel)
        else:
            widget.setFrameStyle(QtGui.QFrame.NoFrame)
        if self.orientation == ContainerField.horizontal:
            layout = QtGui.QHBoxLayout(widget)
        else:
            layout = QtGui.QVBoxLayout(widget)
        if not self.border:
            layout.setContentsMargins(0, 0, 0, 0)
        for field in self.fields:
            layout.addWidget(field.widget())
        if self.orientation == ContainerField.vertical:
            # Only add a stretch to vertical layouts because horizontal layout will get too squished
            layout.addStretch()
        return widget

    def copy(self):
        """Returns a copy of the Field"""
        container = ContainerField(orientation=self.orientation, border=self.border)
        for field in self.fields:
            container.add_field(field.copy())
        return container


class ArrayField(object):
    """A field that can dynamically add or remove fields."""

    def __init__(self, add_label_text='Add New Element'):
        self.fields = []
        self.add_label_text = add_label_text
        self.__current = 0  # For iterator

    def __iter__(self):
        return self

    def next(self):
        if self.__current >= len(self.fields):
            self.__current = 0
            raise StopIteration
        else:
            self.__current += 1
            return self.fields[self.__current - 1]

    def add_field(self, field):
        """Add a new Field to dynamic list.

        :param field: Field to add.
        """
        self.fields.append(field)

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QtGui.QPushButton(self.add_label_text)
        button.released.connect(partial(self._add_element, layout))
        layout.addWidget(button)
        for field in self.fields:
            self._add_element(layout, field)
        return widget

    def copy(self):
        """Returns a copy of the Field"""
        array_field = ArrayField(add_label_text=self.add_label_text)
        for field in self.fields:
            array_field.add_field(field.copy())
        return array_field

    def _add_element(self, layout, field=None):
        """Adds a new field to the Array.

        :param layout: The layout to add the new field to.
        :param field: Optional field to add. If omitted, a copy of the last element will be added.
        """
        if field is None:
            if not self.fields:
                raise RuntimeError('No default field set in the ArrayField.')
            field = self.fields[-1].copy()
            self.fields.append(field)
        element_widget = QtGui.QWidget()
        layout.addWidget(element_widget)
        hbox = QtGui.QHBoxLayout(element_widget)
        hbox.setContentsMargins(0, 0, 0, 0)

        field_widget = field.widget()
        hbox.addWidget(field_widget)

        action = QtGui.QAction('Remove', layout)
        action.triggered.connect(partial(self.remove_element, layout, element_widget))

        icon = QtGui.QIcon(QtGui.QPixmap(':/trash.png'))
        action.setIcon(icon)
        action.setToolTip('Remove')
        action.setStatusTip('Remove')
        delete_button = QtGui.QToolButton()
        delete_button.setDefaultAction(action)
        hbox.addWidget(delete_button)

    def remove_element(self, layout, widget):
        if len(self.fields) == 1:
            # Always keep at least one because _add_element copies the last field in the list.
            return
        index = layout.indexOf(widget)
        self.fields.pop(index-1)
        widget = layout.takeAt(index)
        widget.widget().deleteLater()