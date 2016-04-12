import maya.cmds as cmds
from PySide import QtGui
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields
import cmt.rig.control
import logging
logger = logging.getLogger(__name__)


class Component(core.Component):
    """A Component that creates animation controls nodes."""

    @classmethod
    def image(cls, size=32):
        return QtGui.QPixmap(':/circle.png').scaled(size, size)

    def __init__(self, controls=None, **kwargs):
        """Constructor
        :param controls: A list of dictionaries describing the contorls nodes that need to be created.
                         See cmt.rig.control.dump.
            {
                'name': node,
                'cvs': cmds.getAttr('{0}.cv[*]'.format(node)),
                'degree': cmds.getAttr('{0}.degree'.format(node)),
                'form': cmds.getAttr('{0}.form'.format(node)),
                'xform': cmds.xform(node, q=True, matrix=True),
                'knots': get_knots(node),
                'pivot': cmds.xform(node, q=True, rp=True),
                'overrideEnabled': cmds.getAttr('{0}.overrideEnabled'.format(node)),
                'overrideRGBColors': cmds.getAttr('{0}.overrideRGBColors'.format(node)),
                'overrideColorRGB': cmds.getAttr('{0}.overrideColorRGB'.format(node))[0],
                'overrideColor': cmds.getAttr('{0}.overrideColor'.format(node)),
            }
        """
        super(Component, self).__init__(**kwargs)
        self.controls = controls or []
        self.control_list = fields.ListField(name='', value=[control['name'] for control in self.controls],
                                             help_text='Controls that will be created.')

    def execute(self):
        cmt.rig.control.create_curves(self.controls)

    def widget(self):
        """Get a the QWidget displaying the Component data.

        Users can override this method if they wish to customize the layout of the component.
        :return: A QWidget containing all the Component fields.
        """
        widget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.control_list.widget())

        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(vbox)
        button = QtGui.QPushButton('Create Controls')
        button.released.connect(self.execute)
        vbox.addWidget(button)
        button = QtGui.QPushButton('Store Controls')
        button.released.connect(self.store_controls)
        vbox.addWidget(button)
        vbox.addStretch()
        return widget

    def store_controls(self):
        selected = cmds.ls(sl=True) or []
        self.controls = cmt.rig.control.dump(selected, stack=True)
        if selected:
            cmds.select(selected)
        self.control_list.set_value([control['name'] for control in self.controls])

    def component_data(self):
        """Override data to export with customized format

        :return: A list of the component data in the queue.
        """
        data = {
            'controls': self.controls
        }
        return data

