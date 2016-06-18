import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.rig.splineik as splineik
import cmt.shortcuts as shortcuts
from PySide import QtGui


class Component(core.Component):
    """A Component that generations a skeleton using the cmt.rig.skeleton serializer."""

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(shortcuts.get_icon_path('spine')).scaled(size, size)

    def __init__(self, start_joint='', end_joint='', start_control='', end_control='', name='spine', **kwargs):
        super(Component, self).__init__(**kwargs)
        self.start_joint = fields.MayaNodeField(name='Start Joint', value=start_joint,
                                                help_text='The ik spline start joint.', parent=self)
        self.end_joint = fields.MayaNodeField(name='End Joint', value=end_joint,
                                              help_text='The ik spline end joint.', parent=self)
        self.start_control = fields.MayaNodeField(name='Start Control', value=start_control,
                                                  help_text='The control at the base of the spine.',
                                                  parent=self)
        self.end_control = fields.MayaNodeField(name='End Control', value=end_control,
                                                help_text='The control at the top of the spine.',
                                                parent=self)
        self.system_name = fields.CharField(name='Name', value=name,
                                            help_text='The name of the system used with all the created nodes.',
                                            parent=self)

    def execute(self):
        start_joint = self.start_joint.value()
        end_joint = self.end_joint.value()
        start_control = self.start_control.value()
        end_control = self.end_control.value()
        name = self.system_name.value()
        splineik.create_spine(start_joint, end_joint, start_control, end_control, name)

