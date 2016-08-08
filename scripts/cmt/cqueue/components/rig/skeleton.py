import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.rig.skeleton as skeleton
from cmt.qt import QtWidgets


class Component(core.Component):
    """A Component that generations a skeleton using the cmt.rig.skeleton serializer."""
    file_path = fields.FilePathField('file_path',
                                     filter='Skeleton Files (*.json)',
                                     help_text='The Skeleton file path.')

    @classmethod
    def image_path(cls):
        return ':/kinJoint.png'

    def execute(self):
        file_path = self.file_path.get_path()
        skeleton.load(file_path)

    def widget(self):
        """Get a the QWidget displaying the Component data.

        Users can override this method if they wish to customize the layout of the component.
        :return: A QWidget containing all the Component fields.
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(QtWidgets.QLabel(self.file_path.verbose_name))
        layout.addWidget(self.file_path.widget())
        button = QtWidgets.QPushButton('Export Selected')
        button.released.connect(self.export_skeleton)
        layout.addWidget(button)
        return widget

    def export_skeleton(self):
        file_path = self.file_path.get_path() or None
        data = skeleton.dump(file_path=file_path)
        if data:
            self.file_path.set_value(data[1])
