import maya.cmds as cmds
from PySide import QtGui
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import logging
logger = logging.getLogger(__name__)


def constraint_data(constraint):
    """Gets the parentConstraint data dictionary of the given constraint.

    The data dictionary can be used as input into the Component.
    :param constraint: Name of a parentConstraint node.
    :return: The parentConstraint data dictionary.
    """
    driven = cmds.listConnections('{0}.constraintParentInverseMatrix'.format(constraint), d=False)[0]
    offset = cmds.getAttr('{0}.target[0].targetOffsetTranslate'.format(constraint))[0]
    offset += cmds.getAttr('{0}.target[0].targetOffsetRotate'.format(constraint))[0]
    maintain_offset = False
    for value in offset:
        if abs(value) > 0.000001:
            maintain_offset = True
            break
    skip_translate = []
    skip_rotate = []
    for x in 'xyz':
        connection = cmds.listConnections('{0}.t{1}'.format(driven, x), d=False)
        if not connection or connection[0] != constraint:
            skip_translate.append(x)

        connection = cmds.listConnections('{0}.r{1}'.format(driven, x), d=False)
        if not connection or connection[0] != constraint:
            skip_rotate.append(x)

    return {
        'drivers': cmds.parentConstraint(constraint, q=True, targetList=True),
        'driven': driven,
        'maintainOffset': maintain_offset,
        'skipTranslate': skip_translate,
        'skipRotate': skip_rotate,
    }


class Component(core.Component):
    """A Component that creates parentConstraints."""

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(':/parentConstraint.png').scaled(size, size)

    def __init__(self, constraints=None, **kwargs):
        """Constructor
        :param constraints: A list of dictionaries describing the aimConstraints that need to be created:
            {
                'drivers': nodes,
                'driven': node,
                'maintainOffset': True,
                'skipTranslate': ['x', 'y', 'z']
                'skipRotate': ['x', 'y', 'z']
            }
        """
        super(Component, self).__init__(**kwargs)
        self.constraints = fields.ArrayField(name='Parent Constraints', add_label_text='Add Parent Constraint')
        self.add_field(self.constraints)
        if not constraints:
            # Create default entries if none specified
            constraints = [
                {'driven': 'node'}
            ]
        # The fields will be arranged in two row containers
        # [[driver, driven], [name, twist, swing, invertTwist, invertSwing, twistAxis]]
        for constraint in constraints:
            self.add_constraint_data(constraint)

    def add_constraint_data(self, constraint):
        container = fields.ContainerField(name='Constraint',
                                          orientation=fields.ContainerField.vertical,
                                          stretch=True)
        self.constraints.add_field(container)
        row_container = fields.ContainerField(name='', border=False)
        container.add_field(row_container)
        row_container.add_field(fields.MayaNodeField(name='Drivers',
                                                     value=constraint.get('drivers', []),
                                                     multi=True,
                                                     help_text='The nodes to constrain to.'))
        row_container.add_field(fields.MayaNodeField(name='Driven',
                                                     value=constraint.get('driven', ''),
                                                     help_text='The node to constrain.'))
        row_container.add_field(fields.BooleanField(name='Maintain offset',
                                                    value=constraint.get('maintainOffset', True)))
        skip = constraint.get('skipTranslate', [])
        row_container = fields.ContainerField(name='', border=False, stretch=True)
        container.add_field(row_container)
        row_container.add_field(fields.BooleanField(name='Skip tx', value='x' in skip))
        row_container.add_field(fields.BooleanField(name='Skip ty', value='y' in skip))
        row_container.add_field(fields.BooleanField(name='Skip tz', value='z' in skip))
        skip = constraint.get('skipRotate', [])
        row_container.add_field(fields.BooleanField(name='Skip rx', value='x' in skip))
        row_container.add_field(fields.BooleanField(name='Skip ry', value='y' in skip))
        row_container.add_field(fields.BooleanField(name='Skip rz', value='z' in skip))

    def execute(self):
        data = self.component_data()
        for constraint in data['constraints']:
            drivers = constraint['drivers']
            del constraint['drivers']
            driven = constraint['driven']
            del constraint['driven']
            cmds.parentConstraint(drivers, driven, **constraint)

    def widget(self):
        widget = QtGui.QWidget()
        layout = QtGui.QFormLayout(widget)
        layout.addRow(self.constraints.name, self.constraints.widget())
        button = QtGui.QPushButton('Add from Selected')
        button.released.connect(self.add_from_selected)
        self.constraints.button_layout.addWidget(button)
        return widget

    def add_from_selected(self):
        # Get parentConstraints from the selected nodes
        sel = cmds.ls(sl=True) or []
        constraints = [x for x in sel if cmds.nodeType(x) == 'parentConstraint']
        transforms = [x for x in sel if cmds.nodeType(x) in ['transform', 'joint']]
        for transform in transforms:
            constraints += (cmds.listConnections(transform, type='parentConstraint') or [])
        constraints = list(set(constraints))
        for constraint in constraints:
            data = constraint_data(constraint)
            self.add_constraint_data(data)
            self.constraints.add_element()

    def component_data(self):
        """Override data to export with customized format

        :return: A list of the component data in the queue.
        """
        constraints = []
        for container in self.constraints:
            skipTranslate = []
            skipRotate = []
            for i, x in enumerate('xyz'):
                if container[1][i].value():
                    skipTranslate.append(x)
                if container[1][i+3].value():
                    skipRotate.append(x)
            constraints.append({
                'drivers': container[0][0].value(),
                'driven': container[0][1].value(),
                'maintainOffset': container[0][2].value(),
                'skipTranslate': skipTranslate,
                'skipRotate': skipRotate,
            })
        data = {
            'constraints': constraints
        }
        return data
