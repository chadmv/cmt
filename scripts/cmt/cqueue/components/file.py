import maya.cmds as cmds
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
from PySide import QtGui


class Component(core.Component):
    """A Component that imports or references in a Maya file."""
    import_operation = 'Import'
    reference_operation = 'Reference'

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(':/fileOpen.png').scaled(size, size)

    def __init__(self, file_path='', namespace='', **kwargs):
        super(Component, self).__init__(**kwargs)
        self.operation = fields.ChoiceField(name='Operation',
                                            choices=[Component.import_operation, Component.reference_operation],
                                            help_text='Whether to import or reference the file.')
        self.file_path = fields.FilePathField(name='File Path', value=file_path,
                                              filter='Maya Files (*.ma *.mb)', help_text='The Maya file path.')
        self.namespace = fields.CharField(name='Namespace', value=namespace,
                                          help_text='The import or reference namespace.')

    def execute(self):
        operation = self.operation.value()
        file_path = self.file_path.value()
        namespace = self.namespace.value()

        kwargs = {}
        if operation == Component.import_operation:
            kwargs['i'] = True
        else:
            kwargs['r'] = True

        if namespace:
            kwargs['namespace'] = namespace

        kwargs['type'] = 'mayaAscii' if file_path.lower().endswith('.ma') else 'mayaBinary'

        cmds.file(file_path, **kwargs)

    def _data(self):
        return {
            'operation': self.operation.value(),
            'file_path': self.file_path.value(),
            'namespace': self.namespace.value(),
        }

    def draw(self, layout):
        """Renders the component PySide widgets into the given layout."""
        layout.addWidget(self.operation.widget())
        layout.addWidget(self.file_path.widget())
        layout.addWidget(self.namespace.widget())