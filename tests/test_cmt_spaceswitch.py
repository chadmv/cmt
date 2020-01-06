import maya.cmds as cmds
import cmt.rig.spaceswitch as ss
from cmt.test import TestCase
import math


class SpaceSwitchTests(TestCase):
    def test_create(self):
        target = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(target), 0, 1, 2)
        driver1 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(driver1), 10, 0, 5)
        driver2 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(driver2), -5, 2, 1)
        cmds.setAttr("{}.r".format(driver2), 40, 0, 0)

        m_orig = cmds.getAttr("{}.worldMatrix[0]".format(target))

        ss.create_space_switch(target, [(driver1, "local"), (driver2, "world")])

        m = cmds.getAttr("{}.worldMatrix[0]".format(target))
        self.assertListAlmostEqual(m_orig, m)

        cmds.setAttr("{}.space".format(target), 1)
        m = cmds.getAttr("{}.worldMatrix[0]".format(target))
        self.assertListAlmostEqual(m_orig, m)

        cmds.setAttr("{}.tx".format(driver2), -10)
        pos = cmds.xform(target, q=True, ws=True, t=True)
        self.assertListAlmostEqual(pos, [-5.0, 1.0, 2.0])

        cmds.setAttr("{}.space".format(target), 0)
        m = cmds.getAttr("{}.worldMatrix[0]".format(target))
        self.assertListAlmostEqual(m_orig, m)

        cmds.setAttr("{}.rx".format(driver1), 30)
        m = cmds.getAttr("{}.worldMatrix[0]".format(target))
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
            0.0,
            2.3660254037844384,
            2.9019237886466835,
            1.0,
        ]
        self.assertListAlmostEqual(expected, m)

    def test_seamless_switch(self):
        target = cmds.spaceLocator()[0]
        driver1 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(driver1), 10, 0, 5)
        driver2 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.t".format(driver2), -5, 2, 1)
        cmds.setAttr("{}.r".format(driver2), 40, 0, 0)

        ss.create_space_switch(
            target, [(driver1, "local"), (driver2, "world")], "space"
        )

        cmds.setAttr("{}.rx".format(driver1), 30)
        m1 = cmds.getAttr("{}.worldMatrix[0]".format(target))

        ss.switch_space(target, "space", 1)

        m2 = cmds.getAttr("{}.worldMatrix[0]".format(target))
        self.assertListAlmostEqual(m1, m2)
