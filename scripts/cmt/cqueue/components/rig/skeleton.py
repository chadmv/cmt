import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.rig.skeleton as skeleton
from PySide import QtGui


class Component(core.Component):
    """A Component that generations a skeleton using the cmt.rig.skeleton serializer."""

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(':/kinJoint.png').scaled(size, size)

    def __init__(self, file_path='', **kwargs):
        super(Component, self).__init__(**kwargs)
        self.file_path = fields.FilePathField(name='File Path', value=file_path,
                                              filter='Skeleton Files (*.json)', help_text='The Skeleton file path.')
        self.add_field(self.file_path)

    def execute(self):
        file_path = self.file_path.value()
        skeleton.load(file_path)

    def draw(self, layout):
        """Renders the component PySide widgets into the given layout."""
        layout.addWidget(self.file_path.widget())
        button = QtGui.QPushButton('Export Selected')
        button.released.connect(self.export_skeleton)
        layout.addWidget(button)

    def export_skeleton(self):
        data = skeleton.dump()
        if data:
            self.file_path.set_value(data[1])
