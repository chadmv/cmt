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
        self.constraints = fields.ArrayField(name='Aim Constraints', add_label_text='Add Aim Constraint')
        self.add_field(self.constraints)
        if not constraints:
            # Create default entries if none specified
            constraints = [
                {'driven': 'node'}
            ]
        # The fields will be arranged in two row containers
        # [[driver, driven], [name, twist, swing, invertTwist, invertSwing, twistAxis]]
        for constraint in constraints:
            container = fields.ContainerField(name='Constraint', orientation=fields.ContainerField.vertical)
            self.constraints.add_field(container)

            row_container = fields.ContainerField(name='Row', border=False)
            container.add_field(row_container)
            row_container.add_field(fields.MayaNodeField(name='Drivers',
                                                         value=constraint.get('drivers', []),
                                                         multi=True,
                                                         help_text='The nodes to aim at.'))
            row_container.add_field(fields.MayaNodeField(name='Driven',
                                                         value=constraint.get('driven', ''),
                                                         help_text='The node to aim'))
            row_container.add_field(fields.BooleanField(name='Maintain offset',
                                                        value=constraint.get('maintainOffset', True)))

            row_container = fields.ContainerField(name='Row', border=False)
            container.add_field(row_container)
            row_container.add_field(fields.VectorField(name='Aim vector',
                                                       value=constraint.get('aimVector', (1.0, 0.0, 0.0))))
            row_container.add_field(fields.VectorField(name='Up vector',
                                                       value=constraint.get('upVector', (0.0, 1.0, 0.0))))

            row_container = fields.ContainerField(name='Row', border=False)
            container.add_field(row_container)
            choices = ['scene', 'object', 'objectrotation', 'vector', 'none']
            row_container.add_field(fields.ChoiceField(name='World up type',
                                                       choices=choices,
                                                       value=constraint.get('worldUpType')))
            row_container.add_field(fields.VectorField(name='World up vector',
                                                       value=constraint.get('worldUpVector', (0.0, 1.0, 0.0))))
            row_container.add_field(fields.MayaNodeField(name='World up object',
                                                         value=constraint.get('worldUpObject', '')))

            row_container = fields.ContainerField(name='Skip', border=False)
            container.add_field(row_container)
            skip = constraint.get('skip', [])
            row_container.add_field(fields.BooleanField(name='Skip x', value='x' in skip))
            row_container.add_field(fields.BooleanField(name='Skip y', value='y' in skip))
            row_container.add_field(fields.BooleanField(name='Skip z', value='z' in skip))

    def execute(self):
        data = self.component_data()
        for constraint in data['constraints']:
            drivers = constraint['drivers']
            del constraint['drivers']
            driven = constraint['driven']
            del constraint['driven']
            cmds.aimConstraint(drivers, driven, **constraint)

    def draw(self, layout):
        """Renders the component PySide widgets into the given layout."""
        layout.addWidget(self.constraints.widget())

    def component_data(self):
        """Override data to export with customized format

        :return: A list of the component data in the queue.
        """
        constraints = []
        for container in self.constraints:
            skip = []
            if container[3][0].value():
                skip.append('x')
            if container[3][1].value():
                skip.append('y')
            if container[3][2].value():
                skip.append('z')
            constraints.append({
                'drivers': container[0][0].value(),
                'driven': container[0][1].value(),
                'maintainOffset': container[0][2].value(),
                'aimVector': container[1][0].value(),
                'upVector': container[1][1].value(),
                'worldUpType': container[2][0].value(),
                'worldUpVector': container[2][1].value(),
                'worldUpObject': container[2][2].value(),
                'skip': skip,
            })
        data = {
            'constraints': constraints
        }
        return data
