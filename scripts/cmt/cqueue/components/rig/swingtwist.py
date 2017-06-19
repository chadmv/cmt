import maya.cmds as cmds
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
from cmt.qt import QtWidgets
import cmt.shortcuts as shortcuts
import logging
logger = logging.getLogger(__name__)


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


class Component(core.Component):
    """A Component that creates swingTwist nodes."""
    twist_axis = {
        0: 'X',
        1: 'Y',
        2: 'Z',
    }

    swingtwists = fields.ArrayField('swing_twists', add_label_text='Add SwingTwist', display_name=False)
    container = fields.ContainerField('swing_twist', parent=swingtwists, container_view=SwingTwistView())
    driver = fields.MayaNodeField('driver', help_text='The node to drive the swingtwist', parent=container)
    driven = fields.MayaNodeField('driven', help_text='The node to be driven', parent=container)
    name = fields.CharField('name',
                            default='swingTwist#',
                            help_text='The name of the created swingTwist node.',
                            parent=container)
    twist = fields.FloatField('twist',
                              default=1.0,
                              help_text='The twist amount',
                              min_value=-1.0,
                              max_value=1.0,
                              parent=container)
    swing = fields.FloatField('swing',
                              default=1.0,
                              help_text='The swing amount',
                              min_value=-1.0,
                              max_value=1.0,
                              parent=container)
    twist_axis = fields.CharField('twist_axis',
                                  default='X',
                                  choices=['X', 'Y', 'Z'],
                                  help_text='The twist axis',
                                  parent=container)

    @classmethod
    def image_path(cls):
        return shortcuts.get_icon_path('swingTwist')

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


