import maya.cmds as cmds
import cmt.rig.common as common
import unittest
from cmt.test import TestCase


class RigCommonTests(TestCase):
    def test_duplicate_chain(self):
        for i in range(5):
            cmds.joint(p=(0, i, 0))
        cmds.select(cl=True)
        for i in range(5):
            cmds.joint(p=(i + 1, 0, 0))
        cmds.parent("joint6", "joint2")
        joints, original_joints = common.duplicate_chain(
            "joint1", "joint5", search_for="joint", replace_with="dupejoint"
        )
        self.assertEqual(5, len(joints))
        self.assertListEqual(["dupejoint{0}".format(x) for x in range(1, 6)], joints)
        self.assertListEqual(
            ["joint{0}".format(x) for x in range(1, 6)], original_joints
        )

    @unittest.skipIf(
        cmds.about(api=True) < 20200000, "offsetParentMatrix only in 2020+"
    )
    def test_opm_parent_constraint(self):
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(loc1), 1, 2, 3)
        cmds.setAttr("{}.t".format(loc2), 2, 2, 4)
        m1 = cmds.getAttr("{}.worldMatrix[0]".format(loc1))
        common.opm_parent_constraint(loc2, loc1, maintain_offset=True)
        m2 = cmds.getAttr("{}.worldMatrix[0]".format(loc1))
        self.assertListAlmostEqual(m1, m2)
        cmds.setAttr("{}.rx".format(loc2), 30)
        m2 = cmds.getAttr("{}.worldMatrix[0]".format(loc1))
        expected = [
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.8660254037844387,
            0.49999999999999994,
            0.0,
            0.0,
            -0.49999999999999994,
            0.8660254037844387,
            0.0,
            1.0,
            2.5,
            3.133974596215561,
            1.0,
        ]
        self.assertListAlmostEqual(expected, m2)

    @unittest.skipIf(
        cmds.about(api=True) < 20200000, "offsetParentMatrix only in 2020+"
    )
    def test_opm_point_constraint(self):
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(loc1), 1, 2, 3)
        cmds.setAttr("{}.t".format(loc2), 2, 2, 4)
        common.opm_point_constraint(loc2, loc1)
        m1 = cmds.getAttr("{}.worldMatrix[0]".format(loc1))
        m2 = cmds.getAttr("{}.worldMatrix[0]".format(loc2))
        self.assertListAlmostEqual(m1, m2)
        cmds.setAttr("{}.tx".format(loc2), 5)
        m1 = cmds.getAttr("{}.worldMatrix[0]".format(loc1))
        m2 = cmds.getAttr("{}.worldMatrix[0]".format(loc2))
        self.assertListAlmostEqual(m1, m2)

        cmds.setAttr("{}.rx".format(loc2), 30)
        m1 = cmds.getAttr("{}.worldMatrix[0]".format(loc1))
        self.assertListAlmostEqual(m1, m2)
