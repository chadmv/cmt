"""Contains the attribute Field types.  The Fields are pre-made classes that the Components should use
in order to facilitate in the rendering of the available arguments in the cqueue ui.
"""

import copy
import os
import re
import logging
from cmt.qt import QtWidgets
from cmt.qt import QtGui
from functools import partial
import maya.cmds as cmds

logger = logging.getLogger(__name__)


class Field(object):
    """Base class for all field types.

    Derived classes should implement the widget, value
    """
    def __init__(self, name, default=None, verbose_name=None, parent=None, display_name=True,
                 help_text=''):
        """Constructor.  No QWidgets should be created in the constructor or else Maya will crash
        in batch/testing mode."""
        self.name = name
        self.verbose_name = verbose_name if verbose_name else self.name.replace('_', ' ').title()
        self.default = default
        self._value = default
        self.help_text = help_text
        self.display_name = display_name
        self.parent = parent
        if parent:
            parent.add_field(self)

    def widget(self):
        """Get the QWidget of the Field."""
        raise NotImplementedError('No widget implemented for Field.')

    def value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def data(self):
        return {self.name: self.value()}

    def has_changed(self):
        """Return True if data differs from initial."""
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or initial value we get
        # is None, replace it with ''.
        initial_value = self.default if self.default is not None else ''
        data_value = self._value if self._value is not None else ''
        return initial_value != data_value


class BooleanField(Field):
    """A checkbox field that holds True or False."""
    def __init__(self, name, default=False, *args, **kwargs):
        super(BooleanField, self).__init__(name, default, *args, **kwargs)

    def set_value(self, value):
        self._value = bool(value)

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QCheckBox(self.verbose_name)
        widget.setChecked(self._value)
        widget.setToolTip(self.help_text)
        widget.toggled.connect(self.set_value)
        return widget


class CharField(Field):
    """A Field that holds a string value."""
    def __init__(self, name, default='', choices=None, editable=False, *args, **kwargs):
        super(CharField, self).__init__(name, default, *args, **kwargs)
        self.choices = choices
        self.editable = editable

    def widget(self):
        """Get the QWidget of the Field."""
        if self.choices:
            widget = QtWidgets.QComboBox()
            widget.setEditable(self.editable)
            for choice in self.choices:
                widget.addItem(choice, choice)
            index = widget.findText(self._value)
            if index == -1:
                widget.addItem(self._value, self._value)
                widget.setCurrentIndex(widget.count() - 1)
            else:
                widget.setCurrentIndex(index)

            widget.currentIndexChanged.connect(self.set_value)
        else:
            widget = QtWidgets.QLineEdit(self._value)
            widget.textChanged.connect(self.set_value)
        widget.setToolTip(self.help_text)
        return widget

    def set_value(self, value):
        if self.choices and isinstance(value, int):
            value = self.choices[value]
        else:
            value = str(value)
        super(CharField, self).set_value(value)


class FloatField(Field):
    """A Field that holds a float value."""

    def __init__(self, name, default=0.0, min_value=0.0, max_value=100.0, precision=2, single_step=0.1, *args, **kwargs):
        super(FloatField, self).__init__(name, default, *args, **kwargs)
        self._value = self._value or 0.0
        self.min_value = min_value
        self.max_value = max_value
        self.precision = precision
        self.single_step = single_step

    def set_value(self, value):
        self._value = float(value)

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QDoubleSpinBox()
        widget.setRange(self.min_value, self.max_value)
        widget.setValue(self._value)
        widget.setDecimals(self.precision)
        widget.setSingleStep(self.single_step)
        widget.setToolTip(self.help_text)
        widget.valueChanged.connect(self.set_value)
        return widget


class VectorField(Field):
    """A Field that holds 3 floats."""

    def __init__(self, name, default=None, precision=4, *args, **kwargs):
        default = default or [0.0, 0.0, 0.0]
        super(VectorField, self).__init__(name, default, *args, **kwargs)
        self._value = self._value or [0.0, 0.0, 0.0]
        self.precision = precision

    def set_value(self, value):
        if not isinstance(value, list) and not isinstance(value, tuple):
            raise TypeError('Invalid value for VectorField: {0}'.format(value))
        if len(value) != 3:
            raise ValueError('Vector must be of length 3: {0}'.format(value))
        self._value = value[:]

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        validator = QtGui.QDoubleValidator(-999999.0, 999999.0, self.precision)
        widget_x = QtWidgets.QLineEdit(str(self._value[0]))
        widget_x.setToolTip(self.help_text)
        widget_x.setValidator(validator)
        widget_x.textChanged.connect(self.set_value_x)
        hbox.addWidget(widget_x)

        widget_y = QtWidgets.QLineEdit(str(self._value[1]))
        widget_y.setToolTip(self.help_text)
        widget_y.setValidator(validator)
        widget_y.textChanged.connect(self.set_value_y)
        hbox.addWidget(widget_y)

        widget_z = QtWidgets.QLineEdit(str(self._value[2]))
        widget_z.setToolTip(self.help_text)
        widget_z.setValidator(validator)
        widget_z.textChanged.connect(self.set_value_z)
        hbox.addWidget(widget_z)
        return widget

    def set_value_x(self, value):
        self._value[0] = value

    def set_value_y(self, value):
        self._value[1] = value

    def set_value_z(self, value):
        self._value[2] = value


class ListField(Field):
    def __init__(self, name, default=None, *args, **kwargs):
        default = default or []
        super(ListField, self).__init__(name, default, *args, **kwargs)
        self._value = self._value or []

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QListWidget()
        widget.setToolTip(self.help_text)
        if self._value:
            widget.addItems(self._value)

        def on_rows_changed(*args, **kwargs):
            values = [widget.item(x).text() for x in range(widget.count())]
            self.set_value(values)

        model = widget.model()  # Maya crashes if we chain calls and model isn't saved in a variable
        model.rowsInserted.connect(on_rows_changed)
        model.rowsRemoved.connect(on_rows_changed)
        return widget


class FilePathField(Field):
    """A Field that holds a file path and presents a Browse file dialog."""

    project_root = 'Project Root'
    full_path = 'Full Path'
    relative_to_choices = [project_root, full_path] +\
                          [x for x in os.environ.get('CMT_CQUEUE_FILEPATH_RELATIVE_TO', '').split(os.pathsep) if x]

    def __init__(self, name, default='', filter='Any File (*)', relative_to=project_root, *args, **kwargs):
        super(FilePathField, self).__init__(name, default, *args, **kwargs)
        self.filter = filter

        if isinstance(self._value, list):
            self._value, self.relative_to = self._value
        else:
            self._value = self._value or ''
            self.relative_to = relative_to

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel('Relative to')
        label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        hbox.addWidget(label)
        relative_combobox = QtWidgets.QComboBox()
        relative_combobox.addItems(FilePathField.relative_to_choices)
        index = relative_combobox.findText(self.relative_to)
        if index != -1:
            relative_combobox.setCurrentIndex(index)
        relative_combobox.currentIndexChanged.connect(self.set_relative_to)
        hbox.addWidget(relative_combobox)

        line_edit = QtWidgets.QLineEdit(self._value)
        line_edit.setToolTip(self.help_text)
        line_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        line_edit.textChanged.connect(self.set_value)
        hbox.addWidget(line_edit)
        button = QtWidgets.QPushButton('Browse')
        button.released.connect(partial(self.browse, line_edit, relative_combobox))
        hbox.addWidget(button)
        return widget

    def set_relative_to(self, relative_to):
        if isinstance(relative_to, int):
            relative_to = FilePathField.relative_to_choices[relative_to]
        self.relative_to = relative_to

    def browse(self, line_edit, relative_to_combobox):
        root = cmds.workspace(q=True, rd=True)
        file_path = cmds.fileDialog2(fileFilter=self.filter, dialogStyle=2, caption=self.name,
                                     fileMode=1, returnFilter=False, startingDirectory=root)
        if file_path:
            # Modify the file path to be a path based on the relative_to value
            file_path = file_path[0].replace('\\', '/')
            relative_to = relative_to_combobox.currentText().replace('\\', '/')
            if relative_to == FilePathField.project_root:
                project_root = cmds.workspace(q=True, rd=True).replace('\\', '/')
                file_path = file_path.replace(project_root, '')
            elif relative_to == FilePathField.full_path:
                # Do nothing, just take the full path
                pass
            else:
                # Account for if the relative_to is an environment variable.
                file_path = os.path.expandvars(file_path)
                # Account for if the relative_to is an actual file path.
                file_path = re.sub('^{0}'.format(relative_to), '', file_path)
            line_edit.setText(file_path)

    def get_path(self):
        """Get the resolved absolute file path."""
        relative_to = self.relative_to
        file_path = self._value
        if relative_to == FilePathField.project_root:
            root = cmds.workspace(q=True, rd=True)
            path = os.path.join(root, file_path)
        elif relative_to == FilePathField.full_path:
            path = file_path
        elif relative_to and '$' not in relative_to:
            path = os.path.join(relative_to, file_path)
        path = os.path.expandvars(path)
        return path.replace('\\', '/')

    def value(self):
        """Override to save relative_to value."""
        return self._value, self.relative_to


class MayaNodeField(Field):
    """A Field that holds the name of a Maya node and presents a set from selected button."""

    def __init__(self, name, default='', multi=False, *args, **kwargs):
        if multi:
            default = default or []
        super(MayaNodeField, self).__init__(name, default, *args, **kwargs)
        self._multi = multi
        self._value = self._value or ''
        if multi and isinstance(self._value, basestring):
            self._value = [self._value, ]

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)
        if self._multi:
            node_widget = QtWidgets.QListWidget()
            node_widget.addItems(self._value)

            def on_rows_changed(*args, **kwargs):
                field = kwargs['field']
                node_widget = kwargs['node_widget']
                values = [node_widget.item(x).text() for x in range(node_widget.count())]
                field.set_value(values)

            model = node_widget.model()
            model.rowsInserted.connect(partial(on_rows_changed, field=self, node_widget=node_widget))
            model.rowsRemoved.connect(partial(on_rows_changed, field=self, node_widget=node_widget))
        else:
            node_widget = QtWidgets.QLineEdit(self._value)
            node_widget.textChanged.connect(self.set_value)
        node_widget.setToolTip(self.help_text)
        hbox.addWidget(node_widget)
        button = QtWidgets.QPushButton('Set')
        button.setToolTip('Populate the field with the selected node.')
        button.released.connect(partial(self.set_from_selected, node_widget))
        hbox.addWidget(button)
        return widget

    def set_from_selected(self, node_widget):
        """Populate the QLineEdit from the first selected node."""
        sel = cmds.ls(sl=True) or []
        if self._multi:
            node_widget.clear()
            if sel:
                node_widget.addItems(sel)
        else:
            text = sel[0] if sel else ''
            node_widget.setText(text)


class ContainerField(Field):
    """A field that can contain many other fields.  This is usually used with ArrayField to add
    multiple groups of Fields.
    """

    def __init__(self, name, container_view=None, *args, **kwargs):
        """Constructor
        """
        super(ContainerField, self).__init__(name, *args, **kwargs)
        if container_view is None:
            container_view = ContainerView()
        if not isinstance(container_view, ContainerView):
            raise TypeError('Invalid container view given to ContainerField {0}'.format(self.name))
        self.fields = []
        self._field_look_up = {}
        self.container_view = container_view

    def __getitem__(self, index):
        """Get the Field at the specified index.

        :param index: Index of the field in the Container.
        :raises: IndexError if the index is out of range.
        """
        if isinstance(index, int):
            return self.fields[index]
        elif isinstance(index, str):
            field = self._field_look_up.get(index)
            if not field:
                raise ValueError('Field {0} does not exist in Container {1}'.format(index, self.name))
            return field
        raise TypeError('Invalid field index {0}.  Must be an integer or string.'.format(index))

    def add_field(self, field):
        """Add a new Field to the container.

        :param field: Field to add.
        """
        self.fields.append(field)
        self._field_look_up[field.name] = field

    def set_value(self, value):
        """Override set_value to set Container Field values from a dictionary.

        :param value: Dictionary of data where the keys are Field names in the container and the values are the
        individual Field values.
        """
        for key, v in value.iteritems():
            field = self._field_look_up.get(key)
            if field:
                field.set_value(v)
            else:
                logger.warning('Invalid container data {0}: {1}'.format(key, v))

    def widget(self):
        """Get the QWidget of the Field."""
        return self.container_view.widget(self)

    def value(self):
        return dict([(field.name, field.value()) for field in self.fields])


class ContainerView(object):
    """Users can derive from ContainerView and pass an instance into a ContainerField to customize the
    the display of a ContainerField."""

    def widget(self, container):
        """Get a widget containing all the fields of the given container.

        :param container: ContainerField instance.
        """
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(QtGui.QFrame.StyledPanel)
        layout = QtWidgets.QFormLayout(widget)
        for field in container.fields:
            layout.addRow(field.name, field.widget())
        return widget


class ArrayField(Field):
    """A field that can dynamically add or remove fields."""

    def __init__(self, name, add_label_text='Add New Element', *args, **kwargs):
        super(ArrayField, self).__init__(name, *args, **kwargs)
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

    def set_value(self, value):
        self.fields = [copy.deepcopy(self.fields[-1]) for v in value]
        for field, v in zip(self.fields, value):
            field.set_value(v)

    def add_field(self, field):
        """Add a new Field to dynamic list.

        :param field: Field to add.
        """
        self.fields.append(field)

    def widget(self):
        """Get the QWidget of the Field."""
        widget = QtWidgets.QWidget()
        field_layout = QtWidgets.QVBoxLayout(widget)
        field_layout.setContentsMargins(0, 0, 0, 0)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        # Monkey path the button_layout onto the widget in case Components want to add more buttons to it.
        widget.field_layout = field_layout
        widget.button_layout = button_layout
        button = QtWidgets.QPushButton(self.add_label_text)
        button.released.connect(partial(self.add_element, field_layout=field_layout))
        button.setToolTip('Add a new element to list.')
        button_layout.addWidget(button)
        for field in self.fields:
            self.add_element(field, field_layout)
        field_layout.addLayout(button_layout)
        return widget

    def add_element(self, field=None, field_layout=None):
        """Adds a new field to the Array.

        :param field: Optional field to add. If omitted, a copy of the last element will be added.
        """
        if field is None:
            if not self.fields:
                raise RuntimeError('No default field set in the ArrayField.')
            field = copy.deepcopy(self.fields[-1])
            self.fields.append(field)
        if field_layout:
            element_widget = QtWidgets.QWidget()
            field_layout.insertWidget(field_layout.count()-1, element_widget)
            hbox = QtWidgets.QHBoxLayout(element_widget)
            hbox.setContentsMargins(0, 0, 0, 0)

            field_widget = field.widget()
            hbox.addWidget(field_widget)

            action = QtWidgets.QAction('Remove', field_layout)
            action.triggered.connect(partial(self.remove_element, field_layout, element_widget))

            icon = QtGui.QIcon(QtGui.QPixmap(':/smallTrash.png'))
            action.setIcon(icon)
            action.setToolTip('Remove')
            action.setStatusTip('Remove')
            delete_button = QtWidgets.QToolButton()
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
