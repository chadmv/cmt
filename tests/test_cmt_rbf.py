import maya.cmds as cmds
import cmt.rig.rbf as rbf
from cmt.test import TestCase
import math


class RBFTests(TestCase):
    def test_create(self):
        loc1 = cmds.spaceLocator()[0]
        node = rbf.RBF.create(
            inputs=["{}.t{}".format(loc1, x) for x in "xyz"],
            outputs=["{}.s{}".format(loc1, x) for x in "xyz"],
        )
        inputs = node.inputs()
        self.assertEqual(inputs, ["{}.translate{}".format(loc1, x) for x in "XYZ"])
        outputs = node.outputs()
        self.assertEqual(outputs, ["{}.scale{}".format(loc1, x) for x in "XYZ"])
        node.add_sample()
        node.add_sample(input_values=[5, 4, 6], output_values=[2, 1, 2])
        node.add_sample(input_values=[-5, -6, -4], output_values=[0.5, 2, 3])
        cmds.setAttr("{}.t".format(loc1), 5, 4, 6)
        s = cmds.getAttr("{}.s".format(loc1))[0]
        self.assertListAlmostEqual(s, [2.0, 1.0, 2.0])
