import maya.cmds as cmds
from cmt.dge import dge
from cmt.test import TestCase
import math


class ControlTests(TestCase):

    def test_add(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x+3", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 8.0)

    def test_add_two_attrs(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x+x", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 10.0)

    def test_add_3_to_1(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x+3", x="{}.t".format(loc))
        cmds.connectAttr(result, "{}.r".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.rx".format(loc))
        self.assertAlmostEquals(y, 8.0, places=6)

    def test_add_1_to_3(self):
        loc = cmds.spaceLocator()[0]
        result = dge("3+x", x="{}.t".format(loc))
        cmds.connectAttr(result, "{}.r".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.rx".format(loc))
        self.assertAlmostEquals(y, 8.0, places=6)

    def test_subtract(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x-3", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 2.0)

    def test_subtract_3_to_1(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x-3", x="{}.t".format(loc))
        cmds.connectAttr(result, "{}.r".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.rx".format(loc))
        self.assertAlmostEquals(y, 2.0, places=6)

    def test_subtract_1_to_3(self):
        loc = cmds.spaceLocator()[0]
        result = dge("3-x", x="{}.t".format(loc))
        cmds.connectAttr(result, "{}.r".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.rx".format(loc))
        self.assertAlmostEquals(y, -2.0, places=6)

    def test_two_op_add_subtract(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x+3-y", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.connectAttr(result, "{}.tz".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        cmds.setAttr("{}.ty".format(loc), 2)
        z = cmds.getAttr("{}.tz".format(loc))
        self.assertAlmostEquals(z, 6.0)

    def test_multiply(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x*3", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 15.0)

    def test_divide(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x/2", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 2.5)

    def test_pow(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x^2", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 25)

    def test_pow_precendence(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x^(2*2)", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 625)

    def test_exp(self):
        loc = cmds.spaceLocator()[0]
        result = dge("exp(x)", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, math.exp(5), places=3)

    def test_clamp(self):
        loc = cmds.spaceLocator()[0]
        result = dge("clamp(x, 0, 5)", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 6)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 5.0)
        cmds.setAttr("{}.tx".format(loc), -1)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 0.0)
        cmds.setAttr("{}.tx".format(loc), 1)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 1.0)

    def test_unary(self):
        loc = cmds.spaceLocator()[0]
        result = dge("-x", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, -5)
