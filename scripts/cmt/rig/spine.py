import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import cmt.rig.common as common


class SpineRig(object):
    def __init__(
        self, start_joint, end_joint, start_control, end_control, name="spine"
    ):
        self.effector = None
        self.ik_handle = None
        self.start_joint = start_joint
        self.end_joint = end_joint
        self.start_control = start_control
        self.end_control = end_control
        self.name = name
        self.curve = None
        self.spline_chain = None

    def create(self, global_scale_attr=None):
        self.spline_chain, original_chain = common.duplicate_chain(
            self.start_joint, self.end_joint, prefix="ikSpine_"
        )

        # Create the spline ik
        self.ik_handle, self.effector, self.curve = cmds.ikHandle(
            name="{}_ikh".format(self.name),
            solver="ikSplineSolver",
            startJoint=self.spline_chain[0],
            endEffector=self.spline_chain[-1],
            parentCurve=False,
            simplifyCurve=False,
        )
        self.effector = cmds.rename(self.effector, "{}_eff".format(self.name))
        self.curve = cmds.rename(self.curve, "{}_crv".format(self.name))

        # Create the joints to skin the curve
        curve_start_joint = cmds.duplicate(
            self.start_joint, parentOnly=True, name="{}CurveStart_jnt".format(self.name)
        )[0]
        start_parent = cmds.listRelatives(self.start_control, parent=True, path=True)
        if start_parent:
            cmds.parent(curve_start_joint, start_parent[0])
        cmds.pointConstraint(self.start_control, curve_start_joint)

        curve_end_joint = cmds.duplicate(
            self.end_joint, parentOnly=True, name="{}CurveEnd_jnt".format(self.name)
        )[0]
        cmds.parent(curve_end_joint, self.end_control)
        for node in [curve_start_joint, curve_end_joint]:
            cmds.setAttr("{}.v".format(node), 0)

        # Skin curve
        cmds.skinCluster(
            curve_start_joint,
            curve_end_joint,
            self.curve,
            name="{}_scl".format(self.name),
            tsb=True,
        )

        # Create stretch network
        curve_info = cmds.arclen(self.curve, constructionHistory=True)
        scale_mdn = cmds.createNode(
            "multiplyDivide", name="{}_global_scale_mdn".format(self.name)
        )
        cmds.connectAttr(
            "{}.arcLength".format(curve_info), "{}.input1X".format(scale_mdn)
        )
        if global_scale_attr:
            cmds.connectAttr(global_scale_attr, "{}.input2X".format(scale_mdn))
        else:
            cmds.setAttr("{}.input2X".format(scale_mdn), 1)
        cmds.setAttr("{}.operation".format(scale_mdn), 2)  # Divide

        mdn = cmds.createNode("multiplyDivide", name="{}Stretch_mdn".format(self.name))
        cmds.connectAttr("{}.outputX".format(scale_mdn), "{}.input1X".format(mdn))
        cmds.setAttr(
            "{}.input2X".format(mdn), cmds.getAttr("{}.arcLength".format(curve_info))
        )
        cmds.setAttr("{}.operation".format(mdn), 2)  # Divide

        # Connect to joints
        for joint in self.spline_chain[1:]:
            tx = cmds.getAttr("{}.translateX".format(joint))
            mdl = cmds.createNode(
                "multDoubleLinear", name="{}Stretch_mdl".format(joint)
            )
            cmds.setAttr("{}.input1".format(mdl), tx)
            cmds.connectAttr("{}.outputX".format(mdn), "{}.input2".format(mdl))
            cmds.connectAttr("{}.output".format(mdl), "{}.translateX".format(joint))

        joint_up = OpenMaya.MVector(0.0, 1.0, 0.0)
        start_joint_path = shortcuts.get_dag_path2(self.start_joint)
        start_control_path = shortcuts.get_dag_path2(self.start_control)
        up_vector_start = (
            joint_up
            * start_joint_path.inclusiveMatrix()
            * start_control_path.inclusiveMatrixInverse()
        )

        end_joint_path = shortcuts.get_dag_path2(self.end_joint)
        end_control_path = shortcuts.get_dag_path2(self.end_control)
        up_vector_end = (
            joint_up
            * end_joint_path.inclusiveMatrix()
            * end_control_path.inclusiveMatrixInverse()
        )

        # Setup advanced twist
        cmds.setAttr("{}.dTwistControlEnable".format(self.ik_handle), True)
        cmds.setAttr("{}.dWorldUpType".format(self.ik_handle), 4)  # Object up
        cmds.setAttr("{}.dWorldUpAxis".format(self.ik_handle), 0)  # Positive Y Up
        cmds.setAttr("{}.dWorldUpVectorX".format(self.ik_handle), up_vector_start.x)
        cmds.setAttr("{}.dWorldUpVectorY".format(self.ik_handle), up_vector_start.y)
        cmds.setAttr("{}.dWorldUpVectorZ".format(self.ik_handle), up_vector_start.z)
        cmds.setAttr("{}.dWorldUpVectorEndX".format(self.ik_handle), up_vector_end.x)
        cmds.setAttr("{}.dWorldUpVectorEndY".format(self.ik_handle), up_vector_end.y)
        cmds.setAttr("{}.dWorldUpVectorEndZ".format(self.ik_handle), up_vector_end.z)
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(self.start_control),
            "{}.dWorldUpMatrix".format(self.ik_handle),
        )
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(self.end_control),
            "{}.dWorldUpMatrixEnd".format(self.ik_handle),
        )

        # Constrain original chain back to spline chain
        for ik_joint, joint in zip(self.spline_chain, original_chain):
            if joint == self.end_joint:
                cmds.pointConstraint(ik_joint, joint, mo=True)
                cmds.orientConstraint(self.end_control, joint, mo=True)
            elif joint == self.start_joint:
                cmds.parentConstraint(self.start_control, joint, mo=True)
            else:
                cmds.parentConstraint(ik_joint, joint)
