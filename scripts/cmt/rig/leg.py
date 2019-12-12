import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import cmt.rig.common as common

reload(common)


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

        self.__create_stretch(ik_control)
        self.__create_pivots(ik_control, pivots)

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
        hierarchy = common.RigHierarchy(
            hierarchy,
            prefix="{}_".format(self.name),
            suffix="",
            lock_and_hide=["s", "v"],
        )
        hierarchy.create()
        cmds.parent(hierarchy.ball_pivot, ik_control)
        for driver, driven in [
            [self.ball_joint, hierarchy.ball_pivot],
            [self.ankle_joint, hierarchy.heel_pivot],
            [self.ball_joint, hierarchy.out_pivot],
            [self.ball_joint, hierarchy.in_pivot],
            [self.toe_joint, hierarchy.toe_pivot],
            [self.ball_joint, hierarchy.toe_lift],
            [self.ball_joint, hierarchy.heel_raise],
            [self.ankle_joint, hierarchy.pole_vector_rotate],
        ]:
            cmds.delete(cmds.pointConstraint(driver, driven))
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

    def __create_stretch(self, ik_control):
        start_loc = cmds.spaceLocator(name="{}_stretch_start".format(self.name))[0]
        common.snap_to_position(start_loc, self.up_leg_joint)
        parent = cmds.listRelatives(self.up_leg_joint, parent=True, path=True)
        if parent:
            cmds.parentConstraint(parent[0], start_loc, mo=True)
            cmds.scaleConstraint(parent[0], start_loc)

        end_loc = cmds.spaceLocator(name="{}_stretch_end".format(self.name))[0]
        cmds.setAttr("{}.v".format(end_loc), 0)
        common.snap_to_position(end_loc, self.ankle_joint)
        cmds.parent(end_loc, ik_control)

        distance_between = cmds.createNode(
            "distanceBetween", name="{}_distance".format(self.name)
        )
        start_loc = cmds.listRelatives(start_loc, children=True, shapes=True)[0]
        cmds.connectAttr(
            "{}.worldPosition".format(start_loc),
            "{}.point1".format(distance_between),
        )
        end_loc = cmds.listRelatives(end_loc, children=True, shapes=True)[0]
        cmds.connectAttr(
            "{}.worldPosition".format(end_loc),
            "{}.point2".format(distance_between),
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
        cmds.setAttr("{}.input2X".format(mdn), rest_length)

        # Clamp scale at min 1
        clamp = cmds.createNode("clamp", name="{}_stretch_clamp".format(self.name))
        cmds.setAttr("{}.minR".format(clamp), 1)
        cmds.setAttr("{}.maxR".format(clamp), 100)
        cmds.connectAttr("{}.outputX".format(mdn), "{}.inputR".format(clamp))

        inverse_scale = cmds.createNode("multiplyDivide", name="{}_inverse_scale".format(self.name))
        cmds.setAttr("{}.operation".format(inverse_scale), 2)  # divide
        cmds.setAttr("{}.input1X".format(inverse_scale), 1)
        cmds.connectAttr("{}.outputR".format(clamp), "{}.input2X".format(inverse_scale))
        for node in [self.up_leg_joint, self.knee_joint]:
            cmds.connectAttr("{}.outputR".format(clamp), "{}.sx".format(node))
        cmds.connectAttr("{}.outputX".format(inverse_scale), "{}.sy".format(self.knee_joint))
        cmds.connectAttr("{}.outputX".format(inverse_scale), "{}.sz".format(self.knee_joint))
