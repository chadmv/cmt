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

    def __init__(self, name, value=None, help_text=''):
        """Constructor.  No QWidgets should be created in the constructor or else Maya will crash
        in batch/testing mode."""
        self.name = name
        self._value = value
        self.help_text = help_text

    def widget(self):
        """Get the QWidget of the Field."""
        raise NotImplementedError('No widget implemented for Field.')

    def name_label(self):
        """Get a QLabel of the Field name."""
        label = QtGui.QLabel(self.name)
        label.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        label.setToolTip(self.help_text)
        return label

    def value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def copy(self):
        """Returns a copy of the Field.

        The copy method is required for support with the

        """
        raise NotImplementedError('No copy implemented for Field.')

    def data(self):
        return {self.name.lower().replace(' ', '_'): self.value()}


class BooleanField(Field):
    """A checkbox field that holds True or False."""

    def __init__(self, name, value=True, *args, **kwargs):
        super(BooleanField, self).__init__(name, value, *args, **kwargs)
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        self._widget = QtGui.QCheckBox()
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

    def __init__(self, name, value='', *args, **kwargs):
        super(CharField, self).__init__(name, value, *args, **kwargs)
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        self._widget = QtGui.QLineEdit(self._value)
        self._widget.setToolTip(self.help_text)
        return self._widget

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

    def __init__(self, name, value=0.0, min_value=0.0, max_value=100.0, precision=2, single_step=0.1,
                 *args, **kwargs):
        super(FloatField, self).__init__(name, value, *args, **kwargs)
        self._widget = None
        self.min_value = min_value
        self.max_value = max_value
        self.precision = precision
        self.single_step = single_step

    def widget(self):
        """Get the QWidget of the Field."""
        self._widget = QtGui.QDoubleSpinBox()
        self._widget.setRange(self.min_value, self.max_value)
        self._widget.setValue(self._value)
        self._widget.setDecimals(self.precision)
        self._widget.setSingleStep(self.single_step)
        self._widget.setToolTip(self.help_text)
        return self._widget

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


class VectorField(Field):
    """A Field that holds 3 floats."""

    def __init__(self, name, value=(0.0, 0.0, 0.0), precision=4, *args, **kwargs):
        super(VectorField, self).__init__(name, value, *args, **kwargs)
        self._widget_x = None
        self._widget_y = None
        self._widget_z = None
        self.precision = precision

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        validator = QtGui.QDoubleValidator(-999999.0, 999999.0, self.precision)
        self._widget_x = QtGui.QLineEdit(str(self._value[0]))
        self._widget_x.setToolTip(self.help_text)
        self._widget_x.setValidator(validator)
        hbox.addWidget(self._widget_x)

        self._widget_y = QtGui.QLineEdit(str(self._value[1]))
        self._widget_y.setToolTip(self.help_text)
        self._widget_y.setValidator(validator)
        hbox.addWidget(self._widget_y)

        self._widget_z = QtGui.QLineEdit(str(self._value[2]))
        self._widget_z.setToolTip(self.help_text)
        self._widget_z.setValidator(validator)
        hbox.addWidget(self._widget_z)
        return widget

    def value(self):
        return [float(x.text()) for x in [self._widget_x, self._widget_y, self._widget_z]] if self._widget_x else self._value

    def set_value(self, value):
        super(FloatField, self).set_value(value)
        if self._widget_x:
            self._widget_x.setText(value[0])
            self._widget_y.setText(value[1])
            self._widget_z.setText(value[2])

    def copy(self):
        """Returns a copy of the Field"""
        return VectorField(name=self.name, value=self.value(), help_text=self.help_text, precision=self.precision)


class ChoiceField(Field):
    """A Field with a dropdown."""

    def __init__(self, name, choices, value='', *args, **kwargs):
        super(ChoiceField, self).__init__(name, value, *args, **kwargs)
        self._widget = None
        self.choices = choices
        if not self._value:
            self._value = choices[0]

    def widget(self):
        """Get the QWidget of the Field."""
        self._widget = QtGui.QComboBox()
        self._widget.setToolTip(self.help_text)
        self._widget.addItems(self.choices)
        self._widget.setCurrentIndex(self._widget.findText(self._value))
        return self._widget

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


class ListField(Field):
    def __init__(self, name, value=None, maximum_height=60, *args, **kwargs):
        super(ListField, self).__init__(name, value, *args, **kwargs)
        self._widget = None
        self._maximum_height = maximum_height
        if not self._value:
            self._value = []

    def widget(self):
        """Get the QWidget of the Field."""
        self._widget = QtGui.QListWidget()
        self._widget.setToolTip(self.help_text)
        self._widget.setMaximumHeight(self._maximum_height)
        if self._value:
            self._widget.addItems(self._value)
        return self._widget

    def value(self):
        return [self._widget.item(x).text() for x in range(self._widget.count())]

    def set_value(self, value):
        super(ListField, self).set_value(value)
        if self._widget:
            self._widget.clear()
            self._widget.addItems(value)

    def copy(self):
        """Returns a copy of the Field"""
        return ListField(name=self.name, value=self.value(), maximum_height=self._maximum_height,
                         help_text=self.help_text)




class FilePathField(Field):
    """A Field that holds a file path and presents a Browse file dialog."""

    def __init__(self, name, value='', filter='Any File (*)', *args, **kwargs):
        super(FilePathField, self).__init__(name, value, *args, **kwargs)
        self.filter = filter
        self._widget = None

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
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

    def __init__(self, name, value='', multi=False, height=45, *args, **kwargs):
        super(MayaNodeField, self).__init__(name, value, *args, **kwargs)
        self._widget = None
        self._multi = multi
        self._height = height
        if multi and isinstance(self._value, basestring):
            self._value = [self._value, ]

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        if self._multi:
            self._widget = QtGui.QListWidget()
            self._widget.addItems(self._value)
            self._widget.setMaximumHeight(self._height)
        else:
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
        sel = cmds.ls(sl=True) or []
        self.set_value(sel)

    def value(self):
        if self._multi:
            if self._widget:
                count = self._widget.count()
                return [self._widget.item(x).text() for x in range(count)]
            else:
                return self._value
        else:
            return self._widget.text() if self._widget else self._value

    def set_value(self, value):
        if self._multi and isinstance(value, basestring):
            value = [value, ]
        elif not self._multi and not isinstance(value, basestring):
            value = value[0]
        super(MayaNodeField, self).set_value(value)
        if self._widget:
            if self._multi:
                self._widget.clear()
                self._widget.addItems(self._value)
            else:
                self._widget.setText(value)

    def copy(self):
        """Returns a copy of the Field"""
        return MayaNodeField(name=self.name, value=self.value(), multi=self._multi, height=self._height,
                             help_text=self.help_text)


class ContainerField(Field):
    """A field that can contain many other fields.  This is usually used with ArrayField to add
    multiple groups of Fields.  It can also be use to orient groups of Fields horizontally or
    vertically.
    """
    horizontal = 0
    vertical = 1
    form = 2

    def __init__(self, name, orientation=horizontal, border=True, stretch=False):
        """Constructor
        :param orientation: ContainerField.horizontal or ContainerField.vertical.
        :param border: True to display a border around the container.
        :param stretch: True to add a stretch at the end of the fields.
        """
        super(ContainerField, self).__init__(name)
        self.orientation = orientation
        self.border = border
        self.stretch = stretch
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
        if self.orientation == ContainerField.form:
            layout = QtGui.QFormLayout(widget)
            if not self.border:
                layout.setContentsMargins(0, 0, 0, 0)
            for field in self.fields:
                layout.addRow(field.name, field.widget())
        else:
            if self.orientation == ContainerField.horizontal:
                layout = QtGui.QHBoxLayout(widget)
            else:
                layout = QtGui.QVBoxLayout(widget)
            if not self.border:
                layout.setContentsMargins(0, 0, 0, 0)
            for field in self.fields:
                if field.name:
                    layout.addWidget(field.name_label())
                layout.addWidget(field.widget())
            if self.stretch:
                layout.addStretch()
        return widget

    def copy(self):
        """Returns a copy of the Field"""
        container = ContainerField(self.name, orientation=self.orientation, border=self.border, stretch=self.stretch)
        for field in self.fields:
            container.add_field(field.copy())
        return container

    def value(self):
        return [field.value() for field in self.fields]


class ArrayField(Field):
    """A field that can dynamically add or remove fields."""

    def __init__(self, name, add_label_text='Add New Element'):
        super(ArrayField, self).__init__(name)
        self.fields = []
        self.add_label_text = add_label_text
        self.__current = 0  # For iterator
        self.button_layout = None
        self.field_layout = None

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
        self.field_layout = QtGui.QVBoxLayout(widget)
        self.field_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout = QtGui.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.field_layout.addLayout(self.button_layout)
        button = QtGui.QPushButton(self.add_label_text)
        button.released.connect(self.add_element)
        self.button_layout.addWidget(button)
        for field in self.fields:
            self.add_element(field)
        return widget

    def copy(self):
        """Returns a copy of the Field"""
        array_field = ArrayField(self.name, add_label_text=self.add_label_text)
        for field in self.fields:
            array_field.add_field(field.copy())
        return array_field

    def add_element(self, field=None):
        """Adds a new field to the Array.

        :param field: Optional field to add. If omitted, a copy of the last element will be added.
        """
        if field is None:
            if not self.fields:
                raise RuntimeError('No default field set in the ArrayField.')
            field = self.fields[-1].copy()
            self.fields.append(field)
        element_widget = QtGui.QWidget()
        self.field_layout.addWidget(element_widget)
        hbox = QtGui.QHBoxLayout(element_widget)
        hbox.setContentsMargins(0, 0, 0, 0)

        field_widget = field.widget()
        hbox.addWidget(field_widget)

        action = QtGui.QAction('Remove', self.field_layout)
        action.triggered.connect(partial(self.remove_element, self.field_layout, element_widget))

        icon = QtGui.QIcon(QtGui.QPixmap(':/smallTrash.png'))
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

    def value(self):
        return [field.value() for field in self.fields]
