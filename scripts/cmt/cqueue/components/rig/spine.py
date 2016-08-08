import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.rig.splineik as splineik
import cmt.shortcuts as shortcuts


class Component(core.Component):
    """A Component that generations a skeleton using the cmt.rig.skeleton serializer."""
    start_joint = fields.MayaNodeField('start_joint', help_text='The ik spline start joint.')
    end_joint = fields.MayaNodeField('end_joint', help_text='The ik spline end joint.')
    start_control = fields.MayaNodeField('start_control', help_text='The control at the base of the spine.')
    end_control = fields.MayaNodeField('end_control', help_text='The control at the top of the spine.')
    system_name = fields.CharField('system_name', default='spine', help_text='The name of the system used with all the created nodes.')

    @classmethod
    def image_path(cls):
        return shortcuts.get_icon_path('spine')

    def execute(self):
        start_joint = self.start_joint.value()
        end_joint = self.end_joint.value()
        start_control = self.start_control.value()
        end_control = self.end_control.value()
        name = self.system_name.value()
        splineik.create_spine(start_joint, end_joint, start_control, end_control, name)

