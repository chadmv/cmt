import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.deform.skinio as skinio


class Component(core.Component):
    """A Component that imports skin weights using skinio."""
    files = fields.ArrayField(
        'files',
        add_label_text='Add Skin File',
        display_name=False)
    file_path = fields.FilePathField(
        'file_path',
        filter='Skin Files (*.skin)',
        help_text='The Skeleton file path.',
        parent=files)

    @classmethod
    def image_path(cls):
        return ':/importSmoothSkin.png'

    def execute(self):
        for file_field in self.files:
            file_path = file_field.get_path()
            skinio.import_skin(file_path)

