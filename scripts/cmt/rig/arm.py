import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import cmt.rig.common as common
from cmt.dge import dge
import cmt.rig.twoboneik as twoboneik

reload(twoboneik)


class ArmRig(object):
    def __init__(self, upper_arm_joint, hand_joint, name="arm"):
        self.two_bone_ik = twoboneik.TwoBoneIk(upper_arm_joint, hand_joint, name)
        self.name = name
        self.group = "{}_grp".format(self.name)

    def create(
        self,
        ik_control,
        pole_vector=None,
        global_scale_attr=None,
        scale_stretch=True,
    ):
        if not cmds.objExists(self.group):
            self.group = cmds.createNode("transform", name=self.group)

        # self.__create_pivots(ik_control, pivots)
        self.two_bone_ik.create(
            ik_control,
            pole_vector,
            soft_ik_parent=ik_control,
            global_scale_attr=global_scale_attr,
            scale_stretch=scale_stretch,
        )
        cmds.parent(self.two_bone_ik.start_loc, self.group)

        is_right_leg = "_r" in self.name.lower()

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
        hierarchy.parent_to_toe_ctrl(self.ik_handle_toe)
        common.lock_and_hide(hierarchy.heel_ctrl, "t")
        common.lock_and_hide(hierarchy.toe_pivot_ctrl, "t")
        cmds.setAttr("{}.rotateOrder".format(hierarchy.heel_ctrl), 2)  # zxy

        self.hierarchy = hierarchy
