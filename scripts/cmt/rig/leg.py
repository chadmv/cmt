import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import cmt.rig.common as common
from cmt.dge import dge


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

    def create(self, ik_control, pole_vector=None, global_scale_attr=None, pivots=None):
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

        self.__create_pivots(ik_control, pole_vector, pivots)
        self.__create_stretch(ik_control, global_scale_attr)

        is_right_leg = "_r" in self.name.lower()

        if pole_vector:
            cmds.poleVectorConstraint(pole_vector, self.ik_handle_leg)
        else:
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

    def __create_pivots(self, ik_control, pole_vector, pivots):
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

        if pole_vector:
            # An explicit pole vector is being used to remove the one in the hierarchy
            hierarchy.delete("pole_vector_rotate")
        else:
            # Use a twist pole vector
            cmds.poleVectorConstraint(hierarchy.pole_vector, self.ik_handle_leg)
            cmds.xform(hierarchy.pole_vector, ws=True, r=True, t=(50, 0, 0))
            cmds.setAttr("{}.twist".format(self.ik_handle_leg), 90)

        self.hierarchy = hierarchy

    def __create_stretch(self, ik_control, global_scale_attr=None):
        for attr in ["stretch", "softIk"]:
            cmds.addAttr(
                ik_control,
                ln=attr,
                minValue=0.0,
                maxValue=1.0,
                defaultValue=0.0,
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

        # Create the locators used to calculate the actual position we want the ik to
        # be placed
        loc = cmds.spaceLocator(name="{}_softik_aim".format(self.name))[0]
        offset_loc = cmds.spaceLocator(name="{}_softik_goal".format(self.name))[0]
        cmds.parent(offset_loc, loc)
        cmds.parent(loc, self.start_loc)
        common.snap_to_position(loc, self.start_loc)
        cmds.aimConstraint(self.end_loc, loc, worldUpType="none")

        distance_between = cmds.createNode(
            "distanceBetween", name="{}_distance".format(self.name)
        )
        cmds.connectAttr(
            "{}.worldPosition".format(start_loc), "{}.point1".format(distance_between)
        )
        cmds.connectAttr(
            "{}.worldPosition".format(end_loc), "{}.point2".format(distance_between)
        )

        rest_length = shortcuts.distance(self.up_leg_joint, self.knee_joint)
        rest_length += shortcuts.distance(self.knee_joint, self.ankle_joint)

        length_ratio = dge(
            "distance / (restLength * globalScale)",
            container="{}_percent_from_rest".format(self.name),
            distance="{}.distance".format(distance_between),
            restLength=rest_length,
            globalScale=global_scale_attr or 1.0,
        )

        # Prevent divide by 0
        softik = dge("max(x, 0.001)", x="{}.softIk".format(ik_control))

        # We need to adjust offset the ik handle and scale the joints to create the soft
        # effect
        # See this graph to see the the softIk and scale values plotted
        # https://www.desmos.com/calculator/csi40rsztl
        # x = length_ratio
        # f(x) = softik_scale
        # c(x) = Scale x of the joints
        # s = softIk attribute
        # t = stretch attribute
        softik_scale = dge(
            "x > (1.0 - softIk)"
            "? (1.0 - softIk) + softIk * (1.0 - exp(-(x - (1.0 - softIk)) / softIk)) "
            ": x",
            container="{}_softik".format(self.name),
            x=length_ratio,
            softIk=softik,
        )

        # Set the effector position
        dge(
            "tx = restLength * lerp(softIk, lengthRatio, stretch)",
            container="{}_effector_position".format(self.name),
            tx="{}.tx".format(offset_loc),
            restLength=rest_length,
            lengthRatio=length_ratio,
            softIk=softik_scale,
            stretch="{}.stretch".format(ik_control),
        )
        cmds.pointConstraint(offset_loc, self.hierarchy.soft_ik)

        # Drive the joint scale for stretch
        scale = dge(
            "lerp(1, lengthRatio / softIk, stretch)",
            lengthRatio=length_ratio,
            softIk=softik_scale,
            stretch="{}.stretch".format(ik_control),
        )
        inverse_scale = dge("1/scale", scale=scale)
        for node in [self.up_leg_joint, self.knee_joint]:
            cmds.connectAttr(scale, "{}.sx".format(node))
            cmds.connectAttr(inverse_scale, "{}.sy".format(node))
            cmds.connectAttr(inverse_scale, "{}.sz".format(node))
