import maya.cmds as cmds
import cmt.shortcuts as shortcuts


def create_spine(start_joint, end_joint, lower_control, upper_control, name="spine"):
    spline_chain, original_chain = shortcuts.duplicate_chain(
        start_joint, end_joint, prefix="ikSpine_"
    )

    # Create the spline ik
    ikh, effector, curve = cmds.ikHandle(
        name="{0}_ikh".format(name),
        solver="ikSplineSolver",
        startJoint=spline_chain[0],
        endEffector=spline_chain[-1],
        parentCurve=False,
        simplifyCurve=False,
    )
    effector = cmds.rename(effector, "{0}_eff".format(name))
    curve = cmds.rename(curve, "{0}_crv".format(name))

    # Create the joints to skin the curve
    curve_start_joint = cmds.duplicate(
        start_joint, parentOnly=True, name="{0}CurveStart_jnt".format(name)
    )
    cmds.parent(curve_start_joint, lower_control)
    curve_end_joint = cmds.duplicate(
        end_joint, parentOnly=True, name="{0}CurveEnd_jnt".format(name)
    )
    cmds.parent(curve_end_joint, upper_control)

    # Skin curve
    cmds.skinCluster(
        curve_start_joint, curve_end_joint, curve, name="{0}_scl".format(name), tsb=True
    )

    # Create stretch network
    curve_info = cmds.arclen(curve, constructionHistory=True)
    mdn = cmds.createNode("multiplyDivide", name="{0}Stretch_mdn".format(name))
    cmds.connectAttr("{0}.arcLength".format(curve_info), "{0}.input1X".format(mdn))
    cmds.setAttr(
        "{0}.input2X".format(mdn), cmds.getAttr("{0}.arcLength".format(curve_info))
    )
    cmds.setAttr("{0}.operation".format(mdn), 2)  # Divide

    # Connect to joints
    for joint in spline_chain[1:]:
        tx = cmds.getAttr("{0}.translateX".format(joint))
        mdl = cmds.createNode("multDoubleLinear", name="{0}Stretch_mdl".format(joint))
        cmds.setAttr("{0}.input1".format(mdl), tx)
        cmds.connectAttr("{0}.outputX".format(mdn), "{0}.input2".format(mdl))
        cmds.connectAttr("{0}.output".format(mdl), "{0}.translateX".format(joint))

    # Setup advanced twist
    cmds.setAttr("{0}.dTwistControlEnable".format(ikh), True)
    cmds.setAttr("{0}.dWorldUpType".format(ikh), 4)  # Object up
    cmds.setAttr("{0}.dWorldUpAxis".format(ikh), 0)  # Positive Y Up
    cmds.setAttr("{0}.dWorldUpVectorX".format(ikh), 0)
    cmds.setAttr("{0}.dWorldUpVectorY".format(ikh), 1)
    cmds.setAttr("{0}.dWorldUpVectorZ".format(ikh), 0)
    cmds.setAttr("{0}.dWorldUpVectorEndX".format(ikh), 0)
    cmds.setAttr("{0}.dWorldUpVectorEndY".format(ikh), 1)
    cmds.setAttr("{0}.dWorldUpVectorEndZ".format(ikh), 0)
    cmds.connectAttr(
        "{0}.worldMatrix[0]".format(lower_control), "{0}.dWorldUpMatrix".format(ikh)
    )
    cmds.connectAttr(
        "{0}.worldMatrix[0]".format(upper_control), "{0}.dWorldUpMatrixEnd".format(ikh)
    )

    # Constrain original chain back to spline chain
    for ik_joint, joint in zip(spline_chain, original_chain):
        if joint == end_joint:
            cmds.pointConstraint(ik_joint, joint, mo=True)
            cmds.orientConstraint(upper_control, joint, mo=True)
        else:
            cmds.parentConstraint(ik_joint, joint)
