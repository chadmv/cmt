from PySide import QtGui
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.deform.skinio as skinio


class Component(core.Component):
    """A Component that imports skin weights using skinio."""

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(':/importSmoothSkin.png').scaled(size, size)

    def __init__(self, file_paths=None, **kwargs):
        super(Component, self).__init__(**kwargs)
        self.array_field = fields.ArrayField(name='File Paths', add_label_text='Add Skin File')
        self.add_field(self.array_field)
        if file_paths is None:
            file_paths = ['']
        if isinstance(file_paths, basestring):
            file_paths = [file_paths]
        for file_path in file_paths:
            self.array_field.add_field(fields.FilePathField(
                name='File Path', value=file_path,
                filter='Skin Files (*.skin)',
                help_text='The Skeleton file path.'))

    def execute(self):
        for file_field in self.array_field:
            file_path = file_field.value()
            skinio.import_skin(file_path)

    def draw(self, layout):
        """Renders the component PySide widgets into the given layout."""
        layout.addWidget(self.array_field.widget())

