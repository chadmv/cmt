import maya.cmds as cmds
import cmt.rig.common as common
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
