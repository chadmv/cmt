import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import cmt.rig.common as common


class LegRig(object):
    def __init__(self, up_leg_joint, ankle_joint, ball_joint, toe_joint, name="leg"):
        self.ik_handle_leg = None
        self.ik_handle_ball = None
        self.ik_handle_toe = None
        self.up_leg_joint = up_leg_joint
        self.knee_joint = cmds.listRelatives(ankle_joint, parent=True, path=True)[0]
        self.ankle_joint = ankle_joint
        self.ball_joint = ball_joint
        self.toe_joint = toe_joint
        self.hierarchy = None
        self.name = name

    def create(self, ik_control, global_scale_attr=None, pivots=None):
        # Create ik handles
        self.ik_handle_leg = cmds.ikHandle(
            name="{}_leg_ikh".format(self.name),
            solver="ikRPsolver",
            startJoint=self.up_leg_joint,
            endEffector=self.ankle_joint,
        )[0]
        self.ik_handle_ball = cmds.ikHandle(
            name="{}_ball_ikh".format(self.name),
            solver="ikSCsolver",
            startJoint=self.ankle_joint,
            endEffector=self.ball_joint,
        )[0]
        self.ik_handle_toe = cmds.ikHandle(
            name="{}_toe_ikh".format(self.name),
            solver="ikSCsolver",
            startJoint=self.ball_joint,
            endEffector=self.toe_joint,
        )[0]

        self.__create_pivots(ik_control, pivots)
        self.__create_stretch(ik_control)

        is_right_leg = "_r" in self.name.lower()
        cmds.addAttr(ik_control, ln="kneeRotate", keyable=True)
        common.connect_attribute(
            "{}.kneeRotate".format(ik_control),
            "{}.ry".format(self.hierarchy.pole_vector_rotate),
            negate=is_right_leg,
        )
        cmds.addAttr(ik_control, ln="ballPivot", keyable=True)
        common.connect_attribute(
            "{}.ballPivot".format(ik_control),
            "{}.ry".format(self.hierarchy.ball_pivot),
            negate=is_right_leg,
        )
        cmds.addAttr(ik_control, ln="footRoll", keyable=True)
        common.connect_attribute(
            "{}.footRoll".format(ik_control),
            "{}.rx".format(self.hierarchy.heel_pivot),
            clamp=[-90.0, 0.0],
        )
        cmds.addAttr(ik_control, ln="raiseHeel", keyable=True)
        common.connect_attribute(
            "{}.raiseHeel".format(ik_control), "{}.rx".format(self.hierarchy.heel_raise)
        )
        cmds.addAttr(ik_control, ln="tilt", keyable=True)
        common.connect_attribute(
            "{}.tilt".format(ik_control),
            "{}.rz".format(self.hierarchy.out_pivot),
            clamp=[-90.0, 0.0] if not is_right_leg else [0.0, 90.0],
            negate=is_right_leg,
        )
        common.connect_attribute(
            "{}.tilt".format(ik_control),
            "{}.rz".format(self.hierarchy.in_pivot),
            clamp=[0.0, 90.0] if not is_right_leg else [-90.0, 0.0],
            negate=is_right_leg,
        )

    def __create_pivots(self, ik_control, pivots):
        """
        """
        hierarchy = {
            "soft_ik": {
                "ball_pivot": {
                    "heel_pivot": {
                        "out_pivot": {
                            "in_pivot": {
                                "toe_pivot": {
                                    "toe_lift": None,
                                    "heel_raise": {
                                        "pole_vector_rotate": {"pole_vector": None}
                                    },
                                }
                            }
                        }
                    }
                }
            }
        }
        hierarchy = common.RigHierarchy(
            hierarchy,
            prefix="{}_".format(self.name),
            suffix="",
            lock_and_hide=["s", "v"],
        )
        hierarchy.create()
        cmds.parent(hierarchy.soft_ik, ik_control)
        for driver, driven in [
            [self.ankle_joint, hierarchy.soft_ik],
            [self.ball_joint, hierarchy.ball_pivot],
            [self.ankle_joint, hierarchy.heel_pivot],
            [self.ball_joint, hierarchy.out_pivot],
            [self.ball_joint, hierarchy.in_pivot],
            [self.toe_joint, hierarchy.toe_pivot],
            [self.ball_joint, hierarchy.toe_lift],
            [self.ball_joint, hierarchy.heel_raise],
            [self.ankle_joint, hierarchy.pole_vector_rotate],
        ]:
            common.snap_to_position(driven, driver)
        for node, position in pivots.items():
            node = getattr(hierarchy, node)
            if not node:
                continue
            children = cmds.listRelatives(node, children=True, path=True)
            if children:
                cmds.parent(children, world=True)
            cmds.xform(node, ws=True, t=position)
            if children:
                cmds.parent(children, node)

        hierarchy.parent_to_toe_lift(self.ik_handle_ball)
        hierarchy.parent_to_toe_lift(self.ik_handle_toe)
        hierarchy.parent_to_heel_raise(self.ik_handle_leg)

        cmds.poleVectorConstraint(hierarchy.pole_vector, self.ik_handle_leg)
        cmds.xform(hierarchy.pole_vector, ws=True, r=True, t=(50, 0, 0))
        cmds.setAttr("{}.twist".format(self.ik_handle_leg), 90)

        self.hierarchy = hierarchy

    def __create_stretch(self, ik_control, global_scale_attr=None):
        cmds.addAttr(
            ik_control,
            ln="stretch",
            minValue=0.0,
            maxValue=1.0,
            defaultValue=1.0,
            keyable=True,
        )
        # Locator for start distance measurement
        self.start_loc = cmds.spaceLocator(name="{}_stretch_start".format(self.name))[0]
        common.snap_to_position(self.start_loc, self.up_leg_joint)
        parent = cmds.listRelatives(self.up_leg_joint, parent=True, path=True)
        if parent:
            cmds.parentConstraint(parent[0], self.start_loc, mo=True)
            cmds.scaleConstraint(parent[0], self.start_loc)
        start_loc = cmds.listRelatives(self.start_loc, children=True, shapes=True)[0]

        # Locator for end distance measurement
        self.end_loc = cmds.spaceLocator(name="{}_stretch_end".format(self.name))[0]
        cmds.setAttr("{}.v".format(self.end_loc), 0)
        common.snap_to_position(self.end_loc, self.ankle_joint)
        cmds.parent(self.end_loc, ik_control)
        end_loc = cmds.listRelatives(self.end_loc, children=True, shapes=True)[0]

        distance_between = cmds.createNode(
            "distanceBetween", name="{}_distance".format(self.name)
        )
        cmds.connectAttr(
            "{}.worldPosition".format(start_loc), "{}.point1".format(distance_between)
        )
        cmds.connectAttr(
            "{}.worldPosition".format(end_loc), "{}.point2".format(distance_between)
        )
        mdn = cmds.createNode(
            "multiplyDivide", name="{}_stretch_scale".format(self.name)
        )
        rest_length = shortcuts.distance(self.up_leg_joint, self.knee_joint)
        rest_length += shortcuts.distance(self.knee_joint, self.ankle_joint)
        cmds.setAttr("{}.operation".format(mdn), 2)  # divide
        cmds.connectAttr(
            "{}.distance".format(distance_between), "{}.input1X".format(mdn)
        )

        if global_scale_attr:
            global_scale = cmds.createNode(
                "multDoubleLinear", name="{}_global_scale".format(self.name)
            )
            cmds.setAttr("{}.input1".format(global_scale), rest_length)
            cmds.connectAttr(global_scale_attr, "{}.input2".format(global_scale))
            cmds.connectAttr("{}.output".format(global_scale), "{}.input2X".format(mdn))
        else:
            cmds.setAttr("{}.input2X".format(mdn), rest_length)
        self.percent_rest_distance = "{}.outputX".format(mdn)

        softik_percentage = self.__create_soft_ik(ik_control)

        # Create the locators used to calculate the actual position we want the ik to
        # be placed
        loc = cmds.spaceLocator(name="{}_softik_aim".format(self.name))[0]
        offset_loc = cmds.spaceLocator(name="{}_softik_goal".format(self.name))[0]
        cmds.parent(offset_loc, loc)
        cmds.parent(loc, self.start_loc)
        common.snap_to_position(loc, self.start_loc)
        cmds.aimConstraint(self.end_loc, loc, worldUpType="none")

        # Calculate length for the target position to allow stretch with soft ik
        # rest_length = rest_length * min(1, percent_rest) * stretch)

        # min(1, percent_rest)
        clamp = cmds.createNode("clamp", name="{}_stretch_clamp".format(self.name))
        cmds.setAttr("{}.minR".format(clamp), 1)
        cmds.setAttr("{}.maxR".format(clamp), 100)
        cmds.connectAttr(self.percent_rest_distance, "{}.inputR".format(clamp))
        stretch_percent = "{}.outputR".format(clamp)

        # min(1, percent_rest) * stretch
        enable_stretch = cmds.createNode(
            "blendTwoAttr", name="{}_stretch_enable".format(self.name)
        )
        cmds.setAttr("{}.input[0]".format(enable_stretch), 1)
        cmds.connectAttr(stretch_percent, "{}.input[1]".format(enable_stretch))
        cmds.connectAttr(
            "{}.stretch".format(ik_control),
            "{}.attributesBlender".format(enable_stretch),
        )
        stretch_factor = "{}.output".format(enable_stretch)

        # rest_length * min(1, percent_rest) * stretch
        mdl = cmds.createNode(
            "multDoubleLinear", name="{}_stretch_target_length".format(self.name)
        )
        cmds.setAttr("{}.input1".format(mdl), rest_length)
        cmds.connectAttr(stretch_factor, "{}.input2".format(mdl))

        target_rest_length = "{}.output".format(mdl)

        # Now the final position will be the percentage of the rest length calculated
        # from soft ik
        mdl = cmds.createNode("multDoubleLinear")
        cmds.connectAttr(softik_percentage, "{}.input1".format(mdl))
        cmds.connectAttr(target_rest_length, "{}.input2".format(mdl))
        cmds.connectAttr("{}.output".format(mdl), "{}.tx".format(offset_loc))
        cmds.pointConstraint(offset_loc, self.hierarchy.soft_ik)

        # Inverse scale for volume preservation
        inverse_scale = cmds.createNode(
            "multiplyDivide", name="{}_inverse_scale".format(self.name)
        )
        cmds.setAttr("{}.operation".format(inverse_scale), 2)  # divide
        cmds.setAttr("{}.input1X".format(inverse_scale), 1)
        cmds.connectAttr(stretch_factor, "{}.input2X".format(inverse_scale))
        for node in [self.up_leg_joint, self.knee_joint]:
            cmds.connectAttr(stretch_factor, "{}.sx".format(node))
            cmds.connectAttr("{}.outputX".format(inverse_scale), "{}.sy".format(node))
            cmds.connectAttr("{}.outputX".format(inverse_scale), "{}.sz".format(node))

    def __create_soft_ik(self, ik_control):
        """Create the node network to allow soft ik

        :param ik_control: Name of the ik control
        :return: The attribute containing the percentage length from start joint to handle
        that the ik should be placed
        """
        cmds.addAttr(
            ik_control,
            ln="softIk",
            minValue=0.0,
            maxValue=1.0,
            defaultValue=0.0,
            keyable=True,
        )

        clamp = cmds.createNode("clamp", name="{}_softik_clamp".format(self.name))
        cmds.setAttr("{}.minR".format(clamp), 0.001)
        cmds.setAttr("{}.maxR".format(clamp), 1)
        cmds.connectAttr("{}.softIk".format(ik_control), "{}.inputR".format(clamp))
        softik = "{}.outputR".format(clamp)

        # We need to adjust how far the ik handle is from the start to create the soft
        # effect
        # x = current % of rest distance
        # if x > (1.0-softIk):
        #     x = (1.0 - softIk) + softIk * (1.0 - exp(-(x - (1.0 - softIk)) / softIk))

        # (1.0 - softik)
        one_minus = cmds.createNode(
            "plusMinusAverage", name="{}_one_minus_softik".format(self.name)
        )
        cmds.setAttr("{}.operation".format(one_minus), 2)
        cmds.setAttr("{}.input1D[0]".format(one_minus), 1)
        cmds.connectAttr(softik, "{}.input1D[1]".format(one_minus))

        # x - (1.0 - softik)
        x_minus = cmds.createNode(
            "plusMinusAverage", name="{}_x_minus_one_minus_softik".format(self.name)
        )
        cmds.setAttr("{}.operation".format(x_minus), 2)
        cmds.connectAttr(self.percent_rest_distance, "{}.input1D[0]".format(x_minus))
        cmds.connectAttr(
            "{}.output1D".format(one_minus), "{}.input1D[1]".format(x_minus)
        )

        # -(x - (1.0 - softik))
        negate = cmds.createNode(
            "multDoubleLinear", name="{}_softik_negate".format(self.name)
        )
        cmds.setAttr("{}.input1".format(negate), -1)
        cmds.connectAttr("{}.output1D".format(x_minus), "{}.input2".format(negate))

        # -(x - (1.0 - softik)) / softik
        divide = cmds.createNode(
            "multiplyDivide", name="{}_softik_divide".format(self.name)
        )
        cmds.setAttr("{}.operation".format(divide), 2)  # divide
        cmds.connectAttr("{}.output".format(negate), "{}.input1X".format(divide))
        cmds.connectAttr(softik, "{}.input2X".format(divide))

        # exp(-(x - (1.0 - softIk)) / softIk)
        exp = cmds.createNode("multiplyDivide", name="{}_softik_exp".format(self.name))
        cmds.setAttr("{}.operation".format(exp), 3)  # pow
        cmds.setAttr("{}.input1X".format(exp), 2.71828)
        cmds.connectAttr("{}.outputX".format(divide), "{}.input2X".format(exp))

        # 1.0 - exp(-(x - (1.0 - softIk)) / softIk)
        one_minus_exp = cmds.createNode(
            "plusMinusAverage", name="{}_one_minus_exp".format(self.name)
        )
        cmds.setAttr("{}.operation".format(one_minus_exp), 2)
        cmds.setAttr("{}.input1D[0]".format(one_minus_exp), 1)
        cmds.connectAttr(
            "{}.outputX".format(exp), "{}.input1D[1]".format(one_minus_exp)
        )

        # softik * (1.0 - exp(-(x - (1.0 - softIk)) / softIk))
        mdl = cmds.createNode(
            "multDoubleLinear", name="{}_softik_mdl".format(self.name)
        )
        cmds.connectAttr(softik, "{}.input1".format(mdl))
        cmds.connectAttr("{}.output1D".format(one_minus_exp), "{}.input2".format(mdl))

        # (1.0 - softik) + softik * (1.0 - exp(-(x - (1.0 - softIk)) / softIk))
        adl = cmds.createNode("addDoubleLinear", name="{}_softik_adl".format(self.name))
        cmds.connectAttr("{}.output1D".format(one_minus), "{}.input1".format(adl))
        cmds.connectAttr("{}.output".format(mdl), "{}.input2".format(adl))
        # Now output of adl is the % of the rest distance the ik handle should be from
        # the start joint

        # Only adjust the ik handle if it is less than the soft percentage threshold
        cnd = cmds.createNode(
            "condition",
            name="{}_current_length_greater_than_soft_length".format(self.name),
        )
        cmds.setAttr("{}.operation".format(cnd), 2)  # greater than
        cmds.connectAttr(self.percent_rest_distance, "{}.firstTerm".format(cnd))
        cmds.connectAttr("{}.output1D".format(one_minus), "{}.secondTerm".format(cnd))
        cmds.connectAttr("{}.output".format(adl), "{}.colorIfTrueR".format(cnd))
        cmds.connectAttr(self.percent_rest_distance, "{}.colorIfFalseR".format(cnd))

        softik_percentage = "{}.outColorR".format(cnd)

        return softik_percentage
