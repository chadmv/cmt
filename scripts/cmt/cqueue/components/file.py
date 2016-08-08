import os
import maya.cmds as cmds
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
from cmt.qt import QtWidgets


class Component(core.Component):
    """A Component that imports or references in a Maya file."""
    import_operation = 'Import'
    reference_operation = 'Reference'

    files = fields.ArrayField('files', add_label_text='Add File', display_name=False)
    container = fields.ContainerField('file', parent=files, container_view=FileView())
    operation = fields.CharField('operation',
                                 choices=[import_operation, reference_operation],
                                 default=import_operation,
                                 help_text='Whether to import or reference the file.',
                                 parent=container)
    file_path = fields.FilePathField('file_path',
                                     filter='Maya Files (*.ma *.mb)',
                                     help_text='The Maya file path.',
                                     parent=container)
    namespace = fields.CharField('namespace',
                                 help_text='The import or reference namespace.',
                                 parent=container)

    @classmethod
    def image_path(cls):
        return ':/fileOpen.png'

    def help_url(self):
        return 'https://github.com/chadmv/cmt/wiki/File-Component'

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
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(QtWidgets.QFrame.NoFrame)
        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(container['operation'].widget())

        file_path_widget = container['file_path'].widget()
        file_path_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(file_path_widget)

        layout.addWidget(QtWidgets.QLabel(container['namespace'].verbose_name))
        namespace_widget = container['namespace'].widget()
        namespace_widget.setMaximumWidth(150)
        namespace_widget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(namespace_widget)

        return widget
