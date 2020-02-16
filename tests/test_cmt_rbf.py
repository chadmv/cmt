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
        node.add_sample(input_values=[5, 4, 6], output_values=[2, 1, 2])
        node.add_sample(input_values=[-5, -6, -4], output_values=[0.5, 2, 3])
        cmds.setAttr("{}.t".format(loc1), 0, 0, 0)
        s = cmds.getAttr("{}.s".format(loc1))[0]
        self.assertListAlmostEqual(s, [1.0, 1.0, 1.0])
        cmds.setAttr("{}.t".format(loc1), 5, 4, 6)
        s = cmds.getAttr("{}.s".format(loc1))[0]
        self.assertListAlmostEqual(s, [2.0, 1.0, 2.0])
        cmds.setAttr("{}.t".format(loc1), -5, -6, -4)
        s = cmds.getAttr("{}.s".format(loc1))[0]
        self.assertListAlmostEqual(s, [0.5, 2.0, 3.0])

    def test_create_plot_demo(self):
        loc1 = cmds.spaceLocator()[0]
        node = rbf.RBF.create(
            inputs=["{}.t{}".format(loc1, x) for x in "xy"],
            outputs=["{}.tz".format(loc1)],
            add_neutral_sample=False,
        )
        node.add_sample(input_values=[0, 0], output_values=[1])
        node.add_sample(input_values=[2, 3], output_values=[0.5])
        node.add_sample(input_values=[3, -1], output_values=[1.5])
        node.add_sample(input_values=[-4, -2], output_values=[-1])
        node.add_sample(input_values=[-2, 3], output_values=[2])
        cmds.setAttr("{}.tx".format(loc1), 0)
        cmds.setAttr("{}.ty".format(loc1), 0)
        tz = cmds.getAttr("{}.tz".format(loc1))
        self.assertAlmostEqual(tz, 1.0)

    def test_input_rotation(self):
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        node = rbf.RBF.create(
            input_transforms=[loc1], outputs=["{}.s{}".format(loc2, x) for x in "xyz"]
        )
        input_transforms = node.input_transforms()
        self.assertEqual(input_transforms, [loc1])
        outputs = node.outputs()
        self.assertEqual(outputs, ["{}.scale{}".format(loc2, x) for x in "XYZ"])
        node.add_sample(input_rotations=[[90, 45, 0]], output_values=[2, 1, 2])
        node.add_sample(input_rotations=[[-90, -60, 0]], output_values=[0.5, 2, 3])
        cmds.setAttr("{}.rx".format(loc1), 90)
        cmds.setAttr("{}.ry".format(loc1), 45)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [2.0, 1.0, 2.0])
        cmds.setAttr("{}.rx".format(loc1), -90)
        cmds.setAttr("{}.ry".format(loc1), -60)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [0.5, 2.0, 3.0])
        cmds.setAttr("{}.rx".format(loc1), 0)
        cmds.setAttr("{}.ry".format(loc1), 0)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [1.0, 1.0, 1.0])

    def test_input_rotation_with_orient(self):
        joint1 = cmds.createNode("joint")
        cmds.setAttr("{}.jo".format(joint1), -27.291, 3.273, 9.352)
        joint2 = cmds.createNode("joint")
        node = rbf.RBF.create(
            input_transforms=[joint1],
            outputs=["{}.s{}".format(joint2, x) for x in "xyz"],
        )
        node.add_sample(input_rotations=[[90, 45, 0]], output_values=[2, 1, 2])
        node.add_sample(input_rotations=[[-90, -60, 0]], output_values=[0.5, 2, 3])
        cmds.setAttr("{}.rx".format(joint1), 90)
        cmds.setAttr("{}.ry".format(joint1), 45)
        s = cmds.getAttr("{}.s".format(joint2))[0]
        self.assertListAlmostEqual(s, [2.0, 1.0, 2.0])
        cmds.setAttr("{}.rx".format(joint1), -90)
        cmds.setAttr("{}.ry".format(joint1), -60)
        s = cmds.getAttr("{}.s".format(joint2))[0]
        self.assertListAlmostEqual(s, [0.5, 2.0, 3.0])
        cmds.setAttr("{}.rx".format(joint1), 0)
        cmds.setAttr("{}.ry".format(joint1), 0)
        s = cmds.getAttr("{}.s".format(joint2))[0]
        self.assertListAlmostEqual(s, [1.0, 1.0, 1.0])

    def test_output_rotation(self):
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        node = rbf.RBF.create(
            inputs=["{}.t{}".format(loc1, x) for x in "xz"],
            output_transforms=[loc2],
            add_neutral_sample=False,
        )
        outputs = node.output_transforms()
        self.assertEqual(outputs, [loc2])
        for inputs, outputs in [
            [[-2, -2], [-45, 0, 135]],
            [[2, -2], [-45, 0, -45]],
            [[2, 2], [45, 0, -45]],
            [[-2, 2], [45, 0, 135]],
        ]:
            node.add_sample(input_values=inputs, output_rotations=[outputs])
            loc = cmds.spaceLocator()[0]
            cmds.setAttr("{}.tx".format(loc), inputs[0])
            cmds.setAttr("{}.tz".format(loc), inputs[1])
            cmds.setAttr("{}.r".format(loc), *outputs)

        cmds.setAttr("{}.t".format(loc1), -2, 0, -2)
        r = cmds.getAttr("{}.r".format(loc2))[0]
        self.assertListAlmostEqual(r, [-45.0, 0.0, 135])

        cmds.setAttr("{}.t".format(loc1), 2, 0, 2)
        r = cmds.getAttr("{}.r".format(loc2))[0]
        self.assertListAlmostEqual(r, [45.0, 0.0, -45])

        cmds.setAttr("{}.t".format(loc1), 0, 0, 0)
        r = cmds.getAttr("{}.r".format(loc2))[0]
        self.assertListAlmostEqual(r, [0.0, 0.0, 45.0])

    def test_input_rotation_swing(self):
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        node = rbf.RBF.create(
            input_transforms=[loc1], outputs=["{}.s{}".format(loc2, x) for x in "xyz"]
        )
        node.add_sample(
            input_rotations=[[0, 0, 90]],
            output_values=[2, 1, 2],
            rotation_type=rbf.RBF.swing,
        )
        node.add_sample(
            input_rotations=[[0, 0, -90]],
            output_values=[0.5, 2, 3],
            rotation_type=rbf.RBF.swing,
        )
        cmds.setAttr("{}.rx".format(loc1), 90)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [1.0, 1.0, 1.0])
        cmds.setAttr("{}.rx".format(loc1), 0)
        cmds.setAttr("{}.rz".format(loc1), 90)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [2, 1, 2])
        cmds.setAttr("{}.rx".format(loc1), 90)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [2, 1, 2])

    def test_input_rotation_twist(self):
        loc1 = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        node = rbf.RBF.create(
            input_transforms=[loc1], outputs=["{}.s{}".format(loc2, x) for x in "xyz"]
        )
        node.add_sample(
            input_rotations=[[90, 0, 0]],
            output_values=[2, 1, 2],
            rotation_type=rbf.RBF.twist,
        )
        node.add_sample(
            input_rotations=[[-90, 0, 0]],
            output_values=[0.5, 2, 3],
            rotation_type=rbf.RBF.twist,
        )
        cmds.setAttr("{}.ry".format(loc1), 90)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [1.0, 1.0, 1.0])
        cmds.setAttr("{}.ry".format(loc1), 0)
        cmds.setAttr("{}.rx".format(loc1), 90)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [2, 1, 2])
        cmds.setAttr("{}.rz".format(loc1), 90)
        s = cmds.getAttr("{}.s".format(loc2))[0]
        self.assertListAlmostEqual(s, [2, 1, 2])

    def test_input_rotation_twist_with_orient(self):
        parent = cmds.createNode("joint")
        cmds.setAttr("{}.t".format(parent), 32.007, 124.970, 0.052)
        cmds.setAttr("{}.jo".format(parent), 116.326, -13.544, -67.100)
        joint1 = cmds.createNode("joint")
        cmds.parent(joint1, parent)
        cmds.setAttr("{}.jo".format(joint1), -27.291, 3.273, 9.352)
        cmds.setAttr("{}.t".format(joint1), 28.424, 0, 0)
        joint2 = cmds.createNode("joint")
        cmds.setAttr("{}.t".format(joint2), 41.465, 108.325, 6.714)
        node = rbf.RBF.create(
            input_transforms=[joint1],
            outputs=["{}.t{}".format(joint2, x) for x in "xyz"],
            output_transforms=[joint2],
        )
        node.add_sample(
            input_rotations=[[-90, 0, 0]],
            output_values=[42.303, 108.277, 4.090],
            output_rotations=[[-24.665, 48.300, -21.075]],
            rotation_type=rbf.RBF.twist,
        )
        node.add_sample(
            input_rotations=[[90, 0, 0]],
            output_values=[39.146, 107.559, 7.016],
            output_rotations=[[18.226, -43.161, -1.089]],
            rotation_type=rbf.RBF.twist,
        )

        cmds.setAttr("{}.sampleMode".format(node.name), 0)
        cmds.setAttr("{}.rx".format(joint1), 0)
        r = cmds.getAttr("{}.r".format(joint2))[0]
        self.assertListAlmostEqual(r, [0.0, 0.0, 0.0], places=6)
        cmds.setAttr("{}.sampleMode".format(node.name), 1)
        r = cmds.getAttr("{}.r".format(joint2))[0]
        self.assertListAlmostEqual(r, [0.0, 0.0, 0.0], places=6)

        cmds.setAttr("{}.sampleMode".format(node.name), 0)
        cmds.setAttr("{}.rx".format(joint1), -90)
        r = cmds.getAttr("{}.r".format(joint2))[0]
        self.assertListAlmostEqual(r, [-24.665, 48.300, -21.075], places=6)
        cmds.setAttr("{}.sampleMode".format(node.name), 1)
        r = cmds.getAttr("{}.r".format(joint2))[0]
        self.assertListAlmostEqual(r, [-24.665, 48.300, -21.075], places=6)

        cmds.setAttr("{}.sampleMode".format(node.name), 0)
        cmds.setAttr("{}.rx".format(joint1), 90)
        r = cmds.getAttr("{}.r".format(joint2))[0]
        self.assertListAlmostEqual(r, [18.226, -43.161, -1.089], places=6)
        cmds.setAttr("{}.sampleMode".format(node.name), 1)
        r = cmds.getAttr("{}.r".format(joint2))[0]
        self.assertListAlmostEqual(r, [18.226, -43.161, -1.089], places=6)
