import maya.cmds as cmds
from cmt.qt import QtWidgets
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import logging
logger = logging.getLogger(__name__)


class AimConstraintView(fields.ContainerView):
    """Customize the view of the container."""
    def widget(self, container):
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        main_vbox = QtWidgets.QVBoxLayout(widget)

        hbox = QtWidgets.QHBoxLayout(widget)
        main_vbox.addLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel(container['drivers'].verbose_name)
        hbox.addWidget(label)
        drivers_widget = container['drivers'].widget()
        drivers_widget.setMaximumHeight(65)
        hbox.addWidget(drivers_widget)

        vbox = QtWidgets.QVBoxLayout()
        hbox.addLayout(vbox)

        hbox1 = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox1)
        label = QtWidgets.QLabel(container['driven'].verbose_name)
        hbox1.addWidget(label)
        hbox1.addWidget(container['driven'].widget())
        hbox1.addWidget(container['maintain_offset'].widget())

        hbox2 = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox2)
        hbox2.setContentsMargins(0, 0, 0, 0)
        hbox2.addWidget(container['skip_x'].widget())
        hbox2.addWidget(container['skip_y'].widget())
        hbox2.addWidget(container['skip_z'].widget())
        hbox2.addStretch()

        hbox = QtWidgets.QHBoxLayout(widget)
        main_vbox.addLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QtWidgets.QLabel(container['aim_vector'].verbose_name))
        hbox.addWidget(container['aim_vector'].widget())
        hbox.addWidget(QtWidgets.QLabel(container['up_vector'].verbose_name))
        hbox.addWidget(container['up_vector'].widget())

        hbox = QtWidgets.QHBoxLayout(widget)
        main_vbox.addLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QtWidgets.QLabel(container['world_up_type'].verbose_name))
        hbox.addWidget(container['world_up_type'].widget())
        hbox.addWidget(QtWidgets.QLabel(container['world_up_object'].verbose_name))
        hbox.addWidget(container['world_up_object'].widget())
        hbox.addWidget(QtWidgets.QLabel(container['world_up_vector'].verbose_name))
        hbox.addWidget(container['world_up_vector'].widget())

        return widget


class Component(core.Component):
    """A Component that creates aimConstraints."""
    constraints = fields.ArrayField('constraints', add_label_text='Add Aim Constraint')
    container = fields.ContainerField('constraint', parent=constraints, container_view=AimConstraintView())
    drivers = fields.MayaNodeField('drivers', multi=True, help_text='The nodes to aim at.', parent=container)
    driven = fields.MayaNodeField('driven', help_text='The node to aim', parent=container)
    maintain_offset = fields.BooleanField('maintain_offset', default=True, parent=container)
    aim_vector = fields.VectorField('aim_vector', default=(1.0, 0.0, 0.0), parent=container)
    up_vector = fields.VectorField('up_vector', default=(0.0, 1.0, 0.0), parent=container)
    world_up_type = fields.CharField('world_up_type',
                                     choices=['scene', 'object', 'objectrotation', 'vector', 'none'],
                                     default='object',
                                     parent=container)
    world_up_vector = fields.VectorField('world_up_vector', default=(0.0, 1.0, 0.0), parent=container)
    world_up_object = fields.MayaNodeField('world_up_object', parent=container)
    skip_x = fields.BooleanField('skip_x', parent=container)
    skip_y = fields.BooleanField('skip_y', parent=container)
    skip_z = fields.BooleanField('skip_z', parent=container)

    @classmethod
    def image_path(cls):
        return ':/aimConstraint.png'

    def execute(self):
        for container in self.constraints:
            drivers = container['drivers'].value()
            driven = container['driven'].value()
            skip = [x for x in 'xyz' if container['skip_{0}'.format(x)].value()]
            cmds.aimConstraint(drivers, driven,
                               maintainOffset=container['maintain_offset'].value(),
                               aimVector=container['aim_vector'].value(),
                               upVector=container['up_vector'].value(),
                               worldUpType=container['world_up_type'].value(),
                               worldUpVector=container['world_up_vector'].value(),
                               worldUpObject=container['world_up_object'].value(),
                               skip=skip)

