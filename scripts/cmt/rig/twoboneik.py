"""Two bone stretchy soft ik setup"""
import maya.cmds as cmds
import cmt.shortcuts as shortcuts
import cmt.rig.common as common
from cmt.dge import dge


class TwoBoneIk(object):
    def __init__(self, start_joint, end_joint, name):
        self.ik_handle = None
        self.start_joint = start_joint
        self.mid_joint = cmds.listRelatives(end_joint, parent=True, path=True)[0]
        self.end_joint = end_joint
        self.name = name

    def create(
        self,
        ik_control,
        pole_vector,
        soft_ik_parent,
        global_scale_attr=None,
        scale_stretch=True,
    ):
        """Create the two bone ik system.

        :param ik_control: Name of the node to use as the ik control.
        :param pole_vector: Name of the node to use as the pole vector control.
        :param soft_ik_parent: Name of the node to parent the soft ik transform to.
        :param global_scale_attr: Optional attribute containing global scale value.
        :param scale_stretch: True to stretch with scale, False to use translate.
        """
        self.ik_handle = cmds.ikHandle(
            name="{}_ikh".format(self.name),
            solver="ikRPsolver",
            startJoint=self.start_joint,
            endEffector=self.end_joint,
        )[0]

        cmds.setAttr("{}.v".format(self.ik_handle), 0)

        self.soft_ik = cmds.createNode("transform", name="{}_soft_ik".format(self.name))
        common.snap_to_position(self.soft_ik, self.end_joint)
        cmds.parent(self.ik_handle, self.soft_ik)
        cmds.parent(self.soft_ik, soft_ik_parent)

        self.__create_stretch(ik_control, global_scale_attr, scale_stretch)
        cmds.parent(self.end_loc, soft_ik_parent)

        cmds.poleVectorConstraint(pole_vector, self.ik_handle)

    def __create_stretch(self, ik_control, global_scale_attr=None, scale_stretch=True):
        """Create the stretchy soft ik setup.

        :param ik_control: Name of the node to use as the ik control.
        :param global_scale_attr: Optional attribute containing global scale value.
        :param scale_stretch: True to stretch with scale, False to use translate.
        """
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
        parent = cmds.listRelatives(self.start_joint, parent=True, path=True)
        if parent:
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(parent[0]),
                "{}.offsetParentMatrix".format(self.start_loc),
            )
        common.snap_to_position(self.start_loc, self.start_joint)

        # Locator for end distance measurement
        self.end_loc = cmds.spaceLocator(name="{}_stretch_end".format(self.name))[0]
        cmds.setAttr("{}.v".format(self.end_loc), 0)
        common.snap_to_position(self.end_loc, self.end_joint)

        rest_length = shortcuts.distance(self.start_joint, self.mid_joint)
        rest_length += shortcuts.distance(self.mid_joint, self.end_joint)

        length_ratio = dge(
            "distance(start, end) / (restLength * globalScale)",
            container="{}_percent_from_rest".format(self.name),
            start=self.start_loc,
            end=self.end_loc,
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

        compose_matrix = cmds.createNode("composeMatrix")

        # Set the effector position
        dge(
            "tx = restLength * lerp(softIk, lengthRatio, stretch)",
            container="{}_effector_position".format(self.name),
            tx="{}.inputTranslate.inputTranslateX".format(compose_matrix),
            restLength=rest_length,
            lengthRatio=length_ratio,
            softIk=softik_scale,
            stretch="{}.stretch".format(ik_control),
        )

        # Drive the joint scale for stretch
        scale = dge(
            "lerp(1, lengthRatio / softIk, stretch)",
            container="{}_stretch_scale".format(self.name),
            lengthRatio=length_ratio,
            softIk=softik_scale,
            stretch="{}.stretch".format(ik_control),
        )
        if scale_stretch:
            inverse_scale = dge("1/scale", scale=scale)
            for node in [self.start_joint, self.mid_joint]:
                cmds.connectAttr(scale, "{}.sx".format(node))
                cmds.connectAttr(inverse_scale, "{}.sy".format(node))
                cmds.connectAttr(inverse_scale, "{}.sz".format(node))
        else:
            for node in [self.mid_joint, self.end_joint]:
                tx = cmds.getAttr("{}.tx".format(node))
                dge("x = {} * s".format(tx), x="{}.tx".format(node), s=scale)

        # Drive the soft ik transform
        aim = cmds.createNode("aimMatrix")
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(self.start_loc), "{}.inputMatrix".format(aim)
        )
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(self.end_loc),
            "{}.primary.primaryTargetMatrix".format(aim),
        )
        mult = cmds.createNode("multMatrix")
        cmds.connectAttr(
            "{}.outputMatrix".format(compose_matrix), "{}.matrixIn[0]".format(mult)
        )
        cmds.connectAttr("{}.outputMatrix".format(aim), "{}.matrixIn[1]".format(mult))
        parent = cmds.listRelatives(self.soft_ik, parent=True, path=True)[0]
        if parent:
            cmds.connectAttr(
                "{}.worldInverseMatrix[0]".format(parent), "{}.matrixIn[2]".format(mult)
            )
        pick = cmds.createNode("pickMatrix")
        cmds.connectAttr("{}.matrixSum".format(mult), "{}.inputMatrix".format(pick))
        for attr in ["Scale", "Shear", "Rotate"]:
            cmds.setAttr("{}.use{}".format(pick, attr), 0)
        cmds.connectAttr(
            "{}.outputMatrix".format(pick),
            "{}.offsetParentMatrix".format(self.soft_ik),
        )
        cmds.setAttr("{}.t".format(self.soft_ik), 0, 0, 0)
