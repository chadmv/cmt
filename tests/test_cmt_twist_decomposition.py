from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.rig.swingtwist as st
from cmt.test import TestCase

import math


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
        self.world_plug = "{}.worldMatrix[0]".format(self.twist_joint)
        self.rest_m = self.local_matrix()
        self.tx = cmds.getAttr("{}.tx".format(self.twist_joint))

    def local_matrix(self):
        m = OpenMaya.MMatrix(cmds.getAttr("{}.worldMatrix[0]".format(self.twist_joint)))
        pinv = OpenMaya.MMatrix(
            cmds.getAttr("{}.worldInverseMatrix[0]".format(self.start_joint))
        )
        return m * pinv

    def test_create_twist_composition(self):
        st.create_swing_twist(
            self.start_joint, self.twist_joint, twist_weight=-1, swing_weight=0
        )
        self.assertTrue(
            cmds.connectionInfo("{}.opm".format(self.twist_joint), isDestination=True)
        )
        m = self.local_matrix()
        self.assertListAlmostEqual(m, self.rest_m)
        cmds.setAttr("{}.rz".format(self.start_joint), 90)
        m = self.local_matrix()
        self.assertListAlmostEqual(m, self.rest_m)
        cmds.setAttr("{}.rz".format(self.start_joint), 0)
        cmds.setAttr("{}.rx".format(self.start_joint), 45)
        m = self.local_matrix()
        tm = OpenMaya.MTransformationMatrix()
        tm.rotateBy(
            OpenMaya.MEulerRotation(math.radians(-45), 0, 0), OpenMaya.MSpace.kTransform
        )
        tm.translateBy(OpenMaya.MVector(self.tx, 0, 0), OpenMaya.MSpace.kTransform)
        self.assertListAlmostEqual(m, tm.asMatrix())

    def test_create_twist_composition_at_p5(self):
        st.create_swing_twist(
            self.start_joint, self.twist_joint, twist_weight=-0.5, swing_weight=0.0
        )
        cmds.setAttr("{}.rx".format(self.start_joint), 45)
        m = self.local_matrix()
        tm = OpenMaya.MTransformationMatrix()
        tm.rotateBy(
            OpenMaya.MEulerRotation(math.radians(-22.5), 0, 0),
            OpenMaya.MSpace.kTransform,
        )
        tm.translateBy(OpenMaya.MVector(self.tx, 0, 0), OpenMaya.MSpace.kTransform)
        self.assertListAlmostEqual(m, tm.asMatrix())

    def test_create_twist_composition_at_p5_non_inverted(self):
        st.create_swing_twist(self.start_joint, self.twist_joint, twist_weight=0.5)
        cmds.setAttr("{}.rx".format(self.start_joint), 45)
        m = self.local_matrix()
        tm = OpenMaya.MTransformationMatrix()
        tm.rotateBy(
            OpenMaya.MEulerRotation(math.radians(22.5), 0, 0),
            OpenMaya.MSpace.kTransform,
        )
        tm.translateBy(OpenMaya.MVector(self.tx, 0, 0), OpenMaya.MSpace.kTransform)
        self.assertListAlmostEqual(m, tm.asMatrix())
