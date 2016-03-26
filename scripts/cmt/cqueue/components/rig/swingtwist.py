import maya.cmds as cmds
from PySide import QtGui
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.shortcuts as shortcuts
import logging
logger = logging.getLogger(__name__)


class Component(core.Component):
    """A Component that creates swingTwist nodes."""
    twist_axis = {
        0: 'X',
        1: 'Y',
        2: 'Z',
    }

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(shortcuts.get_icon_path('swingTwist')).scaled(size, size)

    def __init__(self, swing_twists=None, **kwargs):
        """Constructor
        :param swing_twists: A list of dictionaries describing the swingTwist nodes that need to be
                           created:
            {
                'driven': node,
                'driver': nodes,
                'name': name,
                'twist': 1.0,
                'swing': 0.2,
            }
        """
        super(Component, self).__init__(**kwargs)
        self.swingtwists = fields.ArrayField(name='Swing Twists', add_label_text='Add SwingTwist')
        self.add_field(self.swingtwists)
        if not swing_twists:
            # Create default entries if none specified
            swing_twists = [
                {'name': 'swingTwist#'}
            ]
        twist_axes = self.twist_axis.values()
        twist_axes.sort()
        # The fields will be arranged in two row containers
        # [[driver, driven], [name, twist, swing, invertTwist, invertSwing, twistAxis]]
        for swingtwist in swing_twists:
            container = fields.ContainerField(name='Swing Twist',
                                              orientation=fields.ContainerField.vertical,
                                              stretch=True)
            self.swingtwists.add_field(container)

            row_container = fields.ContainerField(name='', border=False)
            container.add_field(row_container)
            row_container.add_field(fields.MayaNodeField(name='Driver',
                                                         value=swingtwist.get('driver', ''),
                                                         help_text='The node to drive the swingtwist'))
            row_container.add_field(fields.MayaNodeField(name='Driven',
                                                         value=swingtwist.get('driven', ''),
                                                         help_text='The node to be driven'))

            row_container = fields.ContainerField(name='', border=False)
            container.add_field(row_container)
            row_container.add_field(fields.CharField(
                name='Name', value=swingtwist.get('name', 'swingTwist#'),
                help_text='The name of the created swingTwist node.'))
            row_container.add_field(fields.FloatField(name='Twist',
                                                      value=swingtwist.get('twist', 1.0),
                                                      help_text='The twist amount',
                                                      min_value=-1.0,
                                                      max_value=1.0))
            row_container.add_field(fields.FloatField(name='Swing',
                                                      value=swingtwist.get('swing', 1.0),
                                                      help_text='The swing amount',
                                                      min_value=-1.0,
                                                      max_value=1.0))
            row_container.add_field(fields.ChoiceField(
                name='Twist Axis',
                value=Component.twist_axis[swingtwist.get('twistAxis', 0)],
                choices=twist_axes,
                help_text='The twist axis'))

    def execute(self):
        cmds.loadPlugin('cmt_py', qt=True)
        for container in self.swingtwists:
            driver = container[0][0].value()
            driven = container[0][1].value()
            if not cmds.objExists(driver) or not cmds.objExists(driven):
                logger.warning('{0} or {1} does not exist.'.format(driver, driven))
                continue
            logger.info('Creating swingtwist on {0} from {1}'.format(driven, driver))
            name = container[1][0].value()
            twist = container[1][1].value()
            swing = container[1][2].value()
            twist_axis = 'XYZ'.index(container[1][3].value())
            cmds.swingTwist(driver, driven, name=name, twist=twist, swing=swing, twistAxis=twist_axis)

    def component_data(self):
        """Override data to export with customized format

        :return: A list of the component data in the queue.
        """
        swingtwists = []
        for container in self.swingtwists:
            swingtwists.append({
                'driver': container[0][0].value(),
                'driven': container[0][1].value(),
                'name': container[1][0].value(),
                'twist': container[1][1].value(),
                'swing': container[1][2].value(),
                'twistAxis': 'XYZ'.index(container[1][3].value()),
            })
        data = {
            'swing_twists': swingtwists
        }
        return data

