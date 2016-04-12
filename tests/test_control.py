import maya.cmds as cmds
import cmt.rig.control as control
from cmt.test import TestCase


class ControlTests(TestCase):

    def test_set_transform_stack(self):
        loc = cmds.spaceLocator(name='spine_ctrl')[0]
        nulls = control.create_transform_stack(loc, 2)
        self.assertEqual(2, len(nulls))
        parent = cmds.listRelatives(loc, parent=True, path=True)[0]
        self.assertEqual('spine_1nul', parent)
        parent = cmds.listRelatives(parent, parent=True, path=True)[0]
        self.assertEqual('spine_2nul', parent)

        nulls = control.create_transform_stack(loc, 3)
        self.assertEqual(3, len(nulls))
        parent = cmds.listRelatives(loc, parent=True, path=True)[0]
        self.assertEqual('spine_1nul', parent)
        parent = cmds.listRelatives(parent, parent=True, path=True)[0]
        self.assertEqual('spine_2nul', parent)
        parent = cmds.listRelatives(parent, parent=True, path=True)[0]
        self.assertEqual('spine_3nul', parent)
