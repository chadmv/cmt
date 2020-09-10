import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import cmt.rig.common as common
from cmt.dge import dge
import cmt.rig.twoboneik as twoboneik
import cmt.rig.spaceswitch as spaceswitch

reload(common)
reload(twoboneik)


class LegRig(object):
    def __init__(self, up_leg_joint, ankle_joint, ball_joint, toe_joint, name="leg"):
        self.two_bone_ik = twoboneik.TwoBoneIk(up_leg_joint, ankle_joint, name)
        self.ik_handle_ball = None
        self.ik_handle_toe = None
        self.ball_joint = ball_joint
        self.toe_joint = toe_joint
        self.hierarchy = None
        self.name = name
        self.group = "{}_grp".format(self.name)

    def create(
        self,
        ik_control,
        pole_vector=None,
        global_scale_attr=None,
        pivots=None,
        scale_stretch=True,
        parent=None,
    ):
        if not cmds.objExists(self.group):
            self.group = cmds.createNode("transform", name=self.group)
            cmds.setAttr("{}.v".format(self.group), 0)
            common.lock_and_hide(self.group, "trsv")

        self.__create_ik(
            ik_control, pole_vector, global_scale_attr, pivots, scale_stretch, parent
        )
        self.__create_fk()

    def __create_ik(
        self,
        ik_control,
        pole_vector=None,
        global_scale_attr=None,
        pivots=None,
        scale_stretch=True,
        parent=None,
    ):
        # Create ik handles
        self.ik_handle_ball = cmds.ikHandle(
            name="{}_ball_ikh".format(self.name),
            solver="ikSCsolver",
            startJoint=self.two_bone_ik.end_joint,
            endEffector=self.ball_joint,
        )[0]
        if self.toe_joint:
            self.ik_handle_toe = cmds.ikHandle(
                name="{}_toe_ikh".format(self.name),
                solver="ikSCsolver",
                startJoint=self.ball_joint,
                endEffector=self.toe_joint,
            )[0]
        for node in [self.ik_handle_ball, self.ik_handle_toe]:
            if node:
                cmds.setAttr("{}.v".format(node), 0)

        self.__create_pivots(ik_control, pivots)
        self.two_bone_ik.create(
            ik_control,
            pole_vector,
            soft_ik_parent=self.hierarchy.heel_ctrl,
            global_scale_attr=global_scale_attr,
            scale_stretch=scale_stretch,
            parent=parent,
        )
        self.config_control = self.two_bone_ik.config_control
        self.upper_fk_control = self.two_bone_ik.start_fk_control
        cmds.parent(self.two_bone_ik.start_loc, self.group)

        is_right_leg = "_r" in self.name.lower()

        cmds.addAttr(ik_control, ln="ballPivot", keyable=True)
        common.connect_attribute(
            "{}.ballPivot".format(ik_control),
            "{}.ry".format(self.hierarchy.ball_pivot),
            negate=is_right_leg,
        )
        # cmds.addAttr(ik_control, ln="footRoll", keyable=True)
        # common.connect_attribute(
        #     "{}.footRoll".format(ik_control),
        #     "{}.rx".format(self.hierarchy.heel_pivot),
        #     clamp=[-90.0, 0.0],
        # )
        # cmds.addAttr(ik_control, ln="raiseHeel", keyable=True)
        # common.connect_attribute(
        #     "{}.raiseHeel".format(ik_control), "{}.rx".format(self.hierarchy.heel_ctrl)
        # )
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
                "heel_pivot_ctrl": {
                    "out_pivot": {
                        "in_pivot": {
                            "toe_pivot_ctrl": {"toe_ctrl": None, "heel_ctrl": None}
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
            [self.two_bone_ik.end_joint, hierarchy.heel_pivot_ctrl],
            [self.ball_joint, hierarchy.out_pivot],
            [self.ball_joint, hierarchy.in_pivot],
            [self.toe_joint, hierarchy.toe_pivot_ctrl],
            [self.ball_joint, hierarchy.toe_ctrl],
            [self.ball_joint, hierarchy.heel_ctrl],
        ]:
            if driver and driven:
                common.snap_to_position(driven, driver)
        for node, position in pivots.items():
            node = getattr(hierarchy, node, None)
            if not node:
                continue
            children = cmds.listRelatives(node, children=True, path=True)
            if children:
                cmds.parent(children, world=True)
            cmds.xform(node, ws=True, t=position)
            if children:
                cmds.parent(children, node)

        hierarchy.parent_to_heel_ctrl(self.ik_handle_ball)
        if self.ik_handle_toe:
            hierarchy.parent_to_toe_ctrl(self.ik_handle_toe)
        for node in hierarchy:
            common.lock_and_hide(node, "t")

        cmds.setAttr("{}.rotateOrder".format(hierarchy.heel_ctrl), 2)  # zxy

        self.hierarchy = hierarchy

    def __create_fk(self):
        ik_switch = cmds.listConnections(
            "{}.ikBlend".format(self.two_bone_ik.ik_handle), d=False, plugs=True
        )[0]
        for ikh in [self.ik_handle_ball, self.ik_handle_toe]:
            if ikh:
                cmds.connectAttr(ik_switch, "{}.ikBlend".format(ikh))
        self.ball_fk_ctrl = cmds.createNode(
            "transform", name="{}_fk_ctrl".format(self.ball_joint)
        )
        common.snap_to(self.ball_fk_ctrl, self.ball_joint)
        common.lock_and_hide(self.ball_fk_ctrl, "sv")
        cmds.parent(self.ball_fk_ctrl, self.two_bone_ik.end_fk_control)
        common.freeze_to_parent_offset(self.ball_fk_ctrl)

        if self.ik_handle_toe:
            ori = cmds.orientConstraint(self.ball_fk_ctrl, self.ball_joint)[0]
        else:
            # Without a toe joint, like in the UE4 Mannequin, use a constraint instead of ik
            ori_target = cmds.duplicate(
                self.hierarchy.toe_ctrl,
                name="{}_ori".format(self.hierarchy.toe_pivot_ctrl),
                po=True,
            )[0]
            cmds.parent(ori_target, self.hierarchy.toe_ctrl)
            common.snap_to(ori_target, self.ball_joint)

            ori = cmds.orientConstraint(
                self.ball_fk_ctrl, ori_target, self.ball_joint,
            )[0]
            cmds.connectAttr(ik_switch, "{}.{}W1".format(ori, ori_target))

        cmds.connectAttr(
            "{}.ikFk".format(self.two_bone_ik.config_control),
            "{}.{}W0".format(ori, self.ball_fk_ctrl),
        )
