"""Contains the base Component class and the ComponentQueue, which are the two main classes
of the component execution system.

To create a new Component, inherit from the core.Component class and implement the execute method:

class Component(core.Component):
    def __init__(self, sphere_name='', **kwargs):
        super(Component, self).__init__(**kwargs)
        self.sphere_name = fields.CharField(name='Sphere Name', value=sphere_name)
        self.add_field(self.sphere_name)

    def execute(self):
        cmds.polySphere(name=self.sphere_name.value())

    def draw(self, layout):
        layout.addWidget(self.sphere_name.widget())
"""

from PySide import QtGui
import importlib
import json
import os
import pprint
import traceback
import uuid
import logging
logger = logging.getLogger(__name__)


class Component(object):
    """A Component is an independent operation that will be executed in the ComponentQueue.  New components deriving
    from this class must implement the execute method.  For UI support, derived components must override the draw
    method.
    """
    @classmethod
    def image(cls, size=32):
        """Get the icon path of the Component.

        To create an icon for a Component, create a png, jpg or svg with the same name as the
        Component in the same directory.

        :param size: Desired dimension of the image.
        :return: The path of the icon image.
        """
        module = importlib.import_module(cls.__module__)
        path = module.__file__
        base = os.path.splitext(path)[0]
        for ext in ['png', 'jpg', 'jpeg', 'svg']:
            full_path = '{0}.{1}'.format(base, ext)
            if os.path.exists(full_path):
                path = full_path
                break
        else:
            path = ':/hsNothing.png'
        return QtGui.QPixmap(path).scaled(size, size)

    @classmethod
    def name(cls):
        """Get the module path to this Component.  It will be the Python package path used to import the Component."""
        return cls.__module__

    def __init__(self, **kwargs):
        # True or False to skip execution of this component
        self.enabled = kwargs.get('enabled', True)
        # True or False to pause the queue execution after this component runs
        self.break_point = kwargs.get('break_point', False)
        # The unique id of this component
        self.uuid = str(kwargs.get('uuid', uuid.uuid4()))
        # The list of fields
        self.fields = []

    def set_enabled(self, value):
        """Set whether this Component is enabled or not.

        Disabled components will be skipped during ComponentQueue execution.  This function
        is implemented because the UI needs a function to call and can't set the value
        directly in the variable.

        :param value: True to enable the Component.
        """
        self.enabled = value

    def execute(self):
        """Executes the Component.

        Derived classes must implement this method to execute the desired operation.
        """
        raise NotImplementedError('execute method not implemented.')

    def capture_execute(self, on_error=None):
        """Executes the Component allowing the caller to pass in a callback function to call if the execution
        fails.

        :param on_error: An optional callback function that gets called when an exception occurs.
                         The callback function has the signature func(message, component).
        :return: True if the component successfully ran.
        """
        comp_data = pprint.pformat(self.data(), indent=4)
        logger.info('Executing {0} with data:\n{1}'.format(self.name(), comp_data))
        try:
            self.execute()
        except:
            error = traceback.format_exc()
            if on_error:
                on_error(message=error, component=self)
            logger.critical(error)
            return False
        return True

    def data(self):
        """Get the component data dictionary used for rebuilding the component.

        :return: A dictionary containing all the data required to rebuild the component.
        """
        data = {
            'name': self.name(),
            'enabled': self.enabled,
            'break_point': self.break_point,
            'uuid': self.uuid,
        }
        data.update(self.component_data())
        return data

    def component_data(self):
        """Get the component data dictionary used for rebuilding the component.

        This function can be overridden if the user wants to customize how the data is serialized to disk.

        :return: A dictionary containing all the input data required to rebuild the component.
        """
        data = {}
        for field in self.fields:
            data.update(field.data())
        return data

    def add_field(self, field):
        """Adds a field to the Component.

        Fields must be added to a Component in order to be automatically serialized on export.  Note that
        fields inside an ArrayField or ContainerField do not need to be explicitly added to a Component as the
        ArrayField or ContainerField will automatically pass the serialized data to the Component.

        :param field: Field to add.
        """
        self.fields.append(field)

    def draw(self, layout):
        """Renders the component PySide widgets into the given layout.

        Derived classes should implement this method to render the component in the UI.

        :param layout: The parent layout to add the Component widgets to.
        """
        layout.addWidget(QtGui.QLabel('No arguments required.'))

    def help_url(self):
        """Get the url of help documentation for the Component.

        :return: The help url.
        """
        return ''


class ComponentQueue(object):
    """A queue of Components to execute"""

    def __init__(self):
        self.__components = []
        self.__current = 0  # For iterator

    def __iter__(self):
        return self

    def next(self):
        if self.__current >= len(self.__components):
            self.__current = 0
            raise StopIteration
        else:
            self.__current += 1
            return self.__components[self.__current - 1]

    def add(self, component):
        """Add a new component to the queue.

        :param component: Component instance to add.
        """
        self.__components.append(component)

    def insert(self, index, component):
        """Insert a component at the given index.

        :param index: Index to insert the component.
        :param component: The component to insert.
        """
        self.__components.insert(index, component)

    def remove(self, index):
        """Remove a component from the queue.

        :param index: The index or Component to remove.
        :return: The removed Component.
        """
        if isinstance(index, Component):
            comp = index
            self.__components.remove(comp)
        else:
            comp = self.__components.pop(index)
        return comp

    def clear(self):
        """Clears all the Components in the ComponentQueue."""
        self.__components = []

    def index(self, component):
        """Return the index of the given component.

        :param component: A Component object.
        :return: Index of the Component in the ComponentQueue.
        :raises: ValueError if the Component is not in the queue.
        """
        return self.__components.index(component)

    def length(self):
        """Get the number of components in the queue."""
        return len(self.__components)

    def execute(self, on_error=None):
        """Execute all the Components in the queue.

        :param on_error: An optional callback function that gets called when an exception occurs.
                         The callback function has the signature func(message, component).
        """
        for comp in self.__components:
            if comp.enabled and not comp.capture_execute(on_error):
                break

            if comp.break_point:
                break

    def data(self):
        """Get the queue component data.

        :return: A list of the component data in the queue.
        """
        data = []
        for comp in self.__components:
            data.append(comp.data())
        return data

    def export(self, file_path):
        """Export the queue to disk.

        :param file_path: Export file path.
        """
        data = self.data()
        fh = open(file_path, 'w')
        json.dump(data, fh, indent=4)
        fh.close()


def load_queue(file_path):
    """Load a queue from disk.

    :param file_path: Path to a json file.
    :return A ComponentQueue loaded with Components.
    """
    fh = open(file_path, 'r')
    data = json.load(fh)
    fh.close()
    return load_data(data)


def load_data(data):
    """Generates a queue from a list of Component data.

    :param data: A list of Component data generated from ComponentQueue.data.
    :return: A ComponentQueue full of Components.
    """
    queue = ComponentQueue()
    for component_data in data:
        component = load_component_data(component_data)
        if component:
            queue.add(component)
    return queue


def load_component_data(data):
    """Instantiate a Component from a Component data dictionary.

    :param data: A Component data dictionary generated from Component.data
    :return: The instantiated Component.
    """
    component_name = data.get('name')
    if not component_name:
        logger.warning('Component missing name.')
        return None
    try:
        component = load_component_class(**data)
    except ImportError:
        raise RuntimeError('Component {0} does not exist.'.format(component_name))
    return component


def get_components(directory=None):
    """Given a directory path, returns a list of all the component names that are available.

    :param directory: Directory path containing component files.
    :return: A list of component module paths or an empty list if no components are found.
    """
    if directory is None:
        component_paths = os.environ.get('CMT_CQUEUE_COMPONENT_PATH', '').split(os.pathsep)
        component_paths.insert(0, 'cmt.cqueue.components')
    elif isinstance(directory, basestring):
        component_paths = [directory, ]
    else:
        component_paths = directory

    result = []
    for component_path in component_paths:
        if not component_path:
            continue
        try:
            module = importlib.import_module(component_path)
        except ImportError:
            logger.warning('Could not import {0}.  Is it in the PYTHONPATH?'.format(component_path))
            continue
        full_path = module.__path__[0]
        # Create the full importable path to each component
        for root, dirs, files in os.walk(full_path):
            result = extract_component_module_path(component_path, files, full_path, root, result)
    return result


def extract_component_module_path(component_path, files, full_path, root, result):
    """Extracts any component files from the given component path.

    :param component_path: Base component path (e.g. cmt.cqueue.components)
    :param files: List of files in the the directory.
    :param full_path: Full path on disk to the component path.
    :param root: The path to the current directory.
    :param result: Storage for the component module paths.
    :return: The list of discovered component module paths.
    """
    partial_path = root.replace(full_path, '')
    if root != full_path:
        partial_path = partial_path[1:]
    partial_path = '{0}.{1}'.format(component_path, partial_path)
    partial_path = partial_path.replace(os.path.sep, '.')
    if not partial_path.endswith('.'):
        partial_path += '.'
    result += ['{0}{1}'.format(partial_path, os.path.splitext(f)[0]) for f in files
               if f[0] not in ('_', '.') and f.endswith('.py')]
    return result


def get_component_class(name):
    """Given a component name, returns the Component class.

    :param name: Name of the component module path.
    """
    module = importlib.import_module(name)
    try:
        return module.Component
    except AttributeError:
        return None


def load_component_class(name, *args, **kwargs):
    """Given a component name, returns the Component class instance.

    :param name: Name of the component module path.
    :param args: Any positional arguments to pass into  the Component constructor.
    :param kwargs: Any keyword arguments to pass into the Component constructor.
    """
    component_class = get_component_class(name)
    return component_class(*args, **kwargs)


