import os
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

    def help_url(self):
        return 'https://github.com/chadmv/cmt/wiki/File-Component'

    def __init__(self, files=None, **kwargs):
        """

        :param files: [
            {
                'operation': Component.import_operation,
                'file_path': [FilePathField.project_root, 'scenes/file.ma'],
                'namespace': 'GEOM'
        ]
        :param kwargs:
        """
        super(Component, self).__init__(**kwargs)
        self.files = fields.ArrayField(name='files', add_label_text='Add File', display_name=False, parent=self)
        if not files:
            # Create default entries if none specified
            files = [
                {'operation': Component.import_operation}
            ]
        for f in files:
            container = fields.ContainerField(name='file', parent=self.files,
                                              container_view=FileView())

            fields.CharField(name='operation',
                             choices=[Component.import_operation, Component.reference_operation],
                             value=f.get('operation', Component.import_operation),
                             help_text='Whether to import or reference the file.',
                             parent=container)
            fields.FilePathField(name='file_path',
                                 value=f.get('file_path', ''),
                                 filter='Maya Files (*.ma *.mb)',
                                 help_text='The Maya file path.',
                                 parent=container)
            fields.CharField(name='namespace',
                             value=f.get('namespace', ''),
                             help_text='The import or reference namespace.',
                             parent=container)

    def execute(self):
        for container in self.files:
            operation = container['operation'].value()
            file_path = container['file_path'].get_path()
            namespace = container['namespace'].value()

            flag = 'i' if operation == Component.import_operation else 'r'
            kwargs = {
                flag: True,
                'type': {
                    '.ma': 'mayaAscii',
                    '.mb': 'mayaBinary',
                    '.fbx': 'FBX',
                }[os.path.splitext(file_path.lower())[-1]]
            }
            if namespace:
                kwargs['namespace'] = namespace

            cmds.file(file_path, **kwargs)


class FileView(fields.ContainerView):
    """Customize the view of the container."""
    def widget(self, container):
        widget = QtGui.QFrame()
        widget.setFrameStyle(QtGui.QFrame.NoFrame)
        layout = QtGui.QHBoxLayout(widget)
        layout.addWidget(container['operation'].widget())

        file_path_widget = container['file_path'].widget()
        file_path_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        layout.addWidget(file_path_widget)

        layout.addWidget(QtGui.QLabel(container['namespace'].verbose_name))
        namespace_widget = container['namespace'].widget()
        namespace_widget.setMaximumWidth(150)
        namespace_widget.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        layout.addWidget(namespace_widget)

        return widget
