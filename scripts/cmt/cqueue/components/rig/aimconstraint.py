import maya.cmds as cmds
from PySide import QtGui
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import logging
logger = logging.getLogger(__name__)


class Component(core.Component):
    """A Component that creates aimConstraints."""

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(':/aimConstraint.png').scaled(size, size)

    def __init__(self, constraints=None, **kwargs):
        """Constructor
        :param constraints: A list of dictionaries describing the aimConstraints that need to be created:
            {
                'drivers': nodes,
                'driven': node,
                'maintainOffset': True,
                'aimVector': (1.0, 0.0, 0.0),
                'upVector': (0.0, 1.0, 0.0),
                'worldUpType': "scene", "object", "objectrotation", "vector", or "none"
                'worldUpVector': node,
                'worldUpObject': node,
                'skip': ['x', 'y', 'z']
            }
        """
        super(Component, self).__init__(**kwargs)
        self.constraints = fields.ArrayField(name='constraints', add_label_text='Add Aim Constraint', parent=self)
        if not constraints:
            # Create default entries if none specified
            constraints = [
                {'driven': 'node'}
            ]
        for constraint in constraints:
            container = fields.ContainerField(name='constraint', parent=self.constraints,
                                              container_view=AimConstraintView())

            fields.MayaNodeField(name='drivers',
                                 value=constraint.get('drivers', []),
                                 multi=True,
                                 help_text='The nodes to aim at.',
                                 parent=container)
            fields.MayaNodeField(name='driven',
                                 value=constraint.get('driven', ''),
                                 help_text='The node to aim',
                                 parent=container)
            fields.BooleanField(name='maintain_offset',
                                value=constraint.get('maintainOffset', True),
                                parent=container)
            fields.VectorField(name='aim_vector',
                               value=constraint.get('aimVector', (1.0, 0.0, 0.0)),
                               parent=container)
            fields.VectorField(name='up_vector',
                               value=constraint.get('upVector', (0.0, 1.0, 0.0)),
                               parent=container)
            fields.CharField(name='world_up_type',
                             choices=['scene', 'object', 'objectrotation', 'vector', 'none'],
                             value=constraint.get('worldUpType', 'object'),
                             default='object',
                             parent=container)
            fields.VectorField(name='world_up_vector',
                               value=constraint.get('worldUpVector', (0.0, 1.0, 0.0)),
                               parent=container)
            fields.MayaNodeField(name='world_up_object',
                                 value=constraint.get('worldUpObject', ''),
                                 parent=container)
            skip = constraint.get('skip', [])
            fields.BooleanField(name='skip_x', value='x' in skip, parent=container)
            fields.BooleanField(name='skip_y', value='y' in skip, parent=container)
            fields.BooleanField(name='skip_z', value='z' in skip, parent=container)

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


class AimConstraintView(fields.ContainerView):
    """Customize the view of the container."""
    def widget(self, container):
        widget = QtGui.QFrame()
        widget.setFrameStyle(QtGui.QFrame.StyledPanel)
        main_vbox = QtGui.QVBoxLayout(widget)

        hbox = QtGui.QHBoxLayout(widget)
        main_vbox.addLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        label = QtGui.QLabel(container['drivers'].verbose_name)
        hbox.addWidget(label)
        drivers_widget = container['drivers'].widget()
        drivers_widget.setMaximumHeight(65)
        hbox.addWidget(drivers_widget)

        vbox = QtGui.QVBoxLayout()
        hbox.addLayout(vbox)

        hbox1 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox1)
        label = QtGui.QLabel(container['driven'].verbose_name)
        hbox1.addWidget(label)
        hbox1.addWidget(container['driven'].widget())
        hbox1.addWidget(container['maintain_offset'].widget())

        hbox2 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox2)
        hbox2.setContentsMargins(0, 0, 0, 0)
        hbox2.addWidget(container['skip_x'].widget())
        hbox2.addWidget(container['skip_y'].widget())
        hbox2.addWidget(container['skip_z'].widget())
        hbox2.addStretch()

        hbox = QtGui.QHBoxLayout(widget)
        main_vbox.addLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QtGui.QLabel(container['aim_vector'].verbose_name))
        hbox.addWidget(container['aim_vector'].widget())
        hbox.addWidget(QtGui.QLabel(container['up_vector'].verbose_name))
        hbox.addWidget(container['up_vector'].widget())

        hbox = QtGui.QHBoxLayout(widget)
        main_vbox.addLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QtGui.QLabel(container['world_up_type'].verbose_name))
        hbox.addWidget(container['world_up_type'].widget())
        hbox.addWidget(QtGui.QLabel(container['world_up_object'].verbose_name))
        hbox.addWidget(container['world_up_object'].widget())
        hbox.addWidget(QtGui.QLabel(container['world_up_vector'].verbose_name))
        hbox.addWidget(container['world_up_vector'].widget())

        return widget

