import maya.cmds as cmds
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
    def image_path(cls):
        return shortcuts.get_icon_path('swingTwist')

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
        self.swingtwists = fields.ArrayField(name='Swing Twists', add_label_text='Add SwingTwist', display_name=False,
                                             parent=self)
        if not swing_twists:
            # Create default entries if none specified
            swing_twists = [
                {'name': 'swingTwist#'}
            ]
        twist_axes = self.twist_axis.values()
        twist_axes.sort()
        for swingtwist in swing_twists:
            container = fields.ContainerField(name='Swing Twist',
                                              parent=self.swingtwists,
                                              container_view=SwingTwistView())
            fields.MayaNodeField(name='driver',
                                 value=swingtwist.get('driver', ''),
                                 help_text='The node to drive the swingtwist',
                                 parent=container)
            fields.MayaNodeField(name='driven',
                                 value=swingtwist.get('driven', ''),
                                 help_text='The node to be driven',
                                 parent=container)
            fields.CharField(name='name',
                             value=swingtwist.get('name', 'swingTwist#'),
                             help_text='The name of the created swingTwist node.',
                             parent=container)
            fields.FloatField(name='twist',
                              value=swingtwist.get('twist', 1.0),
                              help_text='The twist amount',
                              min_value=-1.0,
                              max_value=1.0,
                              parent=container)
            fields.FloatField(name='swing',
                              value=swingtwist.get('swing', 1.0),
                              help_text='The swing amount',
                              min_value=-1.0,
                              max_value=1.0,
                              parent=container)
            fields.CharField(name='twist_axis',
                             value=swingtwist.get('twistAxis', 'X'),
                             choices=['X', 'Y', 'Z'],
                             help_text='The twist axis',
                             parent=container)

    def execute(self):
        cmds.loadPlugin('cmt_py', qt=True)
        for container in self.swingtwists:
            driver = container['driver'].value()
            driven = container['driven'].value()
            if not cmds.objExists(driver) or not cmds.objExists(driven):
                logger.warning('{0} or {1} does not exist.'.format(driver, driven))
                continue
            logger.info('Creating swingtwist on {0} from {1}'.format(driven, driver))
            name = container['name'].value()
            twist = container['twist'].value()
            swing = container['swing'].value()
            twist_axis = 'XYZ'.index(container['twist_axis'].value())
            cmds.swingTwist(driver, driven, name=name, twist=twist, swing=swing, twistAxis=twist_axis)


class SwingTwistView(fields.ContainerView):
    """Customize the view of the container."""
    def widget(self, container):
        # The fields will be arranged in two row containers
        # [[driver, driven], [name, twist, swing, twistAxis]]
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        vbox = QtWidgets.QVBoxLayout(widget)

        for attrs in [
            ['driver', 'driven'],
            ['name', 'twist', 'swing', 'twist_axis'],
        ]:
            hbox = QtWidgets.QHBoxLayout(widget)
            vbox.addLayout(hbox)
            hbox.setContentsMargins(0, 0, 0, 0)
            for attr in attrs:
                hbox.addWidget(QtWidgets.QLabel(container[attr].verbose_name))
                hbox.addWidget(container[attr].widget())

        return widget
