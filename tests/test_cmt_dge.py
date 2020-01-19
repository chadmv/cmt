import maya.cmds as cmds
from cmt.dge import dge
from cmt.test import TestCase
import math


class DGETests(TestCase):
    def test_add(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x+3.5", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 8.5)

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

    def test_parentheses(self):
        loc = cmds.spaceLocator()[0]
        result = dge("(x+3)*(2+x)", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 56.0)

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

    def test_ternary(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x < 1 ? x : 4", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 4)
        cmds.setAttr("{}.tx".format(loc), 0)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 0)

    def test_ternary_is_equal(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x == 1 ? x : 4", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 4)
        cmds.setAttr("{}.tx".format(loc), 1)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 1)

    def test_ternary_with_function(self):
        loc = cmds.spaceLocator()[0]
        result = dge("x < 1 ? x : exp(x)", x="{}.tx".format(loc))
        cmds.connectAttr(result, "{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, math.exp(5), places=3)
        cmds.setAttr("{}.tx".format(loc), 0)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 0)

    def test_assignment(self):
        loc = cmds.spaceLocator()[0]
        result = dge("y=x^2", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 25)

    def test_reuse_nodes(self):
        loc = cmds.spaceLocator()[0]
        result = dge(
            "y=(1-x)*(1-x)+(1-x)", x="{}.tx".format(loc), y="{}.ty".format(loc)
        )
        cmds.setAttr("{}.tx".format(loc), 5)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 12)
        pma = cmds.ls(type="plusMinusAverage")
        self.assertEqual(len(pma), 2)

    def test_lerp(self):
        loc = cmds.spaceLocator()[0]
        dge("y=lerp(4, 8, x)", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 1)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 8)

        cmds.setAttr("{}.tx".format(loc), 0)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 4)

        cmds.setAttr("{}.tx".format(loc), 0.25)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 5)

    def test_min(self):
        loc = cmds.spaceLocator()[0]
        dge("y=min(x, 2)", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 1)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 1)

        cmds.setAttr("{}.tx".format(loc), 4)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 2)

    def test_max(self):
        loc = cmds.spaceLocator()[0]
        dge("y=max(x, 2)", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 1)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 2)

        cmds.setAttr("{}.tx".format(loc), 4)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 4)

    def test_sqrt(self):
        loc = cmds.spaceLocator()[0]
        dge("y=sqrt(x)", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 10.2)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, math.sqrt(10.2), places=5)

    def test_cos(self):
        loc = cmds.spaceLocator(name="cos")[0]
        loc2 = cmds.spaceLocator()[0]
        dge("y=cos(x)", x="{}.tx".format(loc), y="{}.ty".format(loc2))
        for i in range(100):
            v = -10.0 + 0.1 * i
            cmds.setAttr("{}.tx".format(loc), v)
            y = cmds.getAttr("{}.ty".format(loc2))
            self.assertAlmostEquals(y, math.cos(v), places=5)

    def test_sin(self):
        loc = cmds.spaceLocator(name="sin")[0]
        loc2 = cmds.spaceLocator()[0]
        dge("y=sin(x)", x="{}.tx".format(loc), y="{}.ty".format(loc2))
        for i in range(100):
            v = -math.pi * 0.5 + 0.1 * i
            cmds.setAttr("{}.tx".format(loc), v)
            y = cmds.getAttr("{}.ty".format(loc2))
            self.assertAlmostEquals(y, math.sin(v), places=5)

    def test_tan(self):
        loc = cmds.spaceLocator(name="tan")[0]
        loc2 = cmds.spaceLocator()[0]
        dge("y=tan(x)", x="{}.tx".format(loc), y="{}.ty".format(loc2))
        v = -math.pi * 0.5 + 0.02
        while v < math.pi * 0.5:
            v += 0.02
            cmds.setAttr("{}.tx".format(loc), v)
            y = cmds.getAttr("{}.ty".format(loc2))
            self.assertAlmostEquals(y, math.tan(v), places=1)

    def test_acos(self):
        loc = cmds.spaceLocator(name="acos")[0]
        loc2 = cmds.spaceLocator()[0]
        dge("y=acos(x)", x="{}.tx".format(loc), y="{}.ty".format(loc2))
        for i in range(101):
            v = -1.0 + 0.02 * i
            cmds.setAttr("{}.tx".format(loc), v)
            y = cmds.getAttr("{}.ty".format(loc2))
            self.assertAlmostEquals(y, math.degrees(math.acos(v)), places=4)

    def test_asin(self):
        loc = cmds.spaceLocator(name="asin")[0]
        loc2 = cmds.spaceLocator()[0]
        dge("y=asin(x)", x="{}.tx".format(loc), y="{}.ty".format(loc2))
        for i in range(101):
            v = -1.0 + 0.02 * i
            cmds.setAttr("{}.tx".format(loc), v)
            y = cmds.getAttr("{}.ty".format(loc2))
            self.assertAlmostEquals(y, math.degrees(math.asin(v)), places=4)

    def test_atan(self):
        loc = cmds.spaceLocator(name="atan")[0]
        loc2 = cmds.spaceLocator()[0]
        dge("y=atan(x)", x="{}.tx".format(loc), y="{}.ty".format(loc2))
        for i in range(100):
            v = -5.0 + 0.1 * i
            cmds.setAttr("{}.tx".format(loc), v)
            y = cmds.getAttr("{}.ty".format(loc2))
            self.assertAlmostEquals(y, math.degrees(math.atan(v)), places=5)

    def test_abs(self):
        loc = cmds.spaceLocator()[0]
        dge("y=abs(x)", x="{}.tx".format(loc), y="{}.ty".format(loc))
        cmds.setAttr("{}.tx".format(loc), 0.75)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 0.75)

        cmds.setAttr("{}.tx".format(loc), -0.75)
        y = cmds.getAttr("{}.ty".format(loc))
        self.assertAlmostEquals(y, 0.75)

    def test_distance(self):
        loc = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        cmds.setAttr("{}.tx".format(loc), 2.5)
        result = dge("distance(i, j)", container="mydistance", i=loc, j=loc2)
        d = cmds.getAttr(result)
        self.assertAlmostEquals(d, 2.5)
