from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import maya.cmds as cmds
import cmt.rig.twistdecomposition as td
from cmt.test import TestCase


class TwistDecompositionTests(TestCase):
    def setUp(self):
        self.start_joint = cmds.joint(p=(-0.3, -0.5, 0), name="start_joint")
        self.end_joint = cmds.joint(p=(0.5, 2.0, 0), name="end_joint")
        cmds.joint(
            self.start_joint, e=True, oj="xyz", secondaryAxisOrient="yup", zso=True
        )
        cmds.setAttr("{}.jo".format(self.end_joint), 0, 0, 0)
        self.twist_joint = cmds.duplicate(self.end_joint, name="twist_joint")[0]
        cmds.delete(
            cmds.pointConstraint(self.start_joint, self.end_joint, self.twist_joint)
        )
        self.rotate_plug = "{}.r".format(self.twist_joint)

    def test_create_twist_composition(self):
        td.create_twist_decomposition(self.start_joint, self.twist_joint, invert=True)
        self.assertTrue(cmds.connectionInfo(self.rotate_plug, isDestination=True))
        r = cmds.getAttr(self.rotate_plug)[0]
        self.assertListAlmostEqual(r, [0.0, 0.0, 0.0])
        cmds.setAttr("{}.rz".format(self.start_joint), 90)
        r = cmds.getAttr(self.rotate_plug)[0]
        self.assertListAlmostEqual(r, [0.0, 0.0, 0.0])
        cmds.setAttr("{}.rz".format(self.start_joint), 0)
        cmds.setAttr("{}.rx".format(self.start_joint), 45)
        r = cmds.getAttr(self.rotate_plug)[0]
        self.assertListAlmostEqual(r, [-45.0, 0.0, 0.0])

    def test_create_twist_composition_at_p5(self):
        td.create_twist_decomposition(
            self.start_joint, self.twist_joint, invert=True, twist_weight=0.5
        )
        cmds.setAttr("{}.rx".format(self.start_joint), 45)
        r = cmds.getAttr(self.rotate_plug)[0]
        self.assertListAlmostEqual(r, [-22.5, 0.0, 0.0])

    def test_create_twist_composition_at_p5_non_inverted(self):
        td.create_twist_decomposition(
            self.start_joint, self.twist_joint, invert=False, twist_weight=0.5
        )
        cmds.setAttr("{}.rx".format(self.start_joint), 45)
        r = cmds.getAttr(self.rotate_plug)[0]
        self.assertListAlmostEqual(r, [22.5, 0.0, 0.0])
