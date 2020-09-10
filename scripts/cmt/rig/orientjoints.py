"""A tool used to orient joints with common orientations.

The tool mostly assumes the X axis is the primary axis and joints always rotate forward on the Z axis.

Usage:
import cmt.rig.orientjoints
cmt.rig.orientjoints.OrientJointsWindow()
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial
import logging
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

import cmt.rig.skeleton as skeleton
reload(skeleton)

log = logging.getLogger(__name__)
MESSAGE_ATTRIBUTE = "cmt_jointOrient"
ORIENT_GROUP = "cmt_orient_grp"


class OrientJointsWindow(object):
    def __init__(self):
        name = "cmt_orientjoints"
        if cmds.window(name, exists=True):
            cmds.deleteUI(name, window=True)
        if cmds.windowPref(name, exists=True):
            cmds.windowPref(name, remove=True)
        self.window = cmds.window(
            name, title="CMT Orient Joints", widthHeight=(358, 380)
        )
        cmds.columnLayout(adjustableColumn=True)
        margin_width = 4
        cmds.frameLayout(
            bv=False, label="Operations", collapsable=True, mw=margin_width
        )
        cmds.rowColumnLayout(numberOfColumns=2, adj=1)

        self.insert_joint_field = cmds.intField(minValue=1, value=1)
        cmds.button(label="Insert Joints", c=self.insert_joints)

        cmds.setParent("..")

        cmds.gridLayout(numberOfColumns=3, cellWidthHeight=(116, 30))
        cmds.button(label="Left", c=self.set_left)
        cmds.button(label="Center", c=self.set_center)
        cmds.button(label="Right", c=self.set_right)

        cmds.setParent("..")

        cmds.setParent("..")

        cmds.frameLayout(
            bv=False, label="Quick Actions", collapsable=True, mw=margin_width
        )
        cmds.gridLayout(numberOfColumns=2, cellWidthHeight=(175, 65))
        cmds.button(label="Make Planar Orientation", command=self.make_planar)
        cmds.button(
            label="Project to Planar Position", command=partial(make_position_planar)
        )
        cmds.button(label="Align Up With Child", command=self.align_with_child)
        cmds.button(label="Zero Orient", command=self.zero_orient)
        cmds.button(label="Orient to World", command=self.orient_to_world)
        cmds.rowColumnLayout(numberOfColumns=4)

        height = 20
        label_width = 60
        icon_left = "nudgeLeft.png"
        icon_right = "nudgeRight.png"
        cmds.text(label="Offset X", align="right", width=label_width)
        cmds.iconTextButton(
            style="iconOnly",
            image1=icon_left,
            label="spotlight",
            h=height,
            w=height,
            c=partial(self.offset_orient_x, direction=-1),
        )
        self.offset_x = cmds.floatField(value=90.0)
        cmds.iconTextButton(
            style="iconOnly",
            image1=icon_right,
            label="spotlight",
            h=height,
            w=height,
            c=partial(self.offset_orient_x, direction=1),
        )
        cmds.text(label="Offset Y", align="right", width=label_width)
        cmds.iconTextButton(
            style="iconOnly",
            image1=icon_left,
            label="spotlight",
            h=height,
            w=height,
            c=partial(self.offset_orient_y, direction=-1),
        )
        self.offset_y = cmds.floatField(value=90.0)
        cmds.iconTextButton(
            style="iconOnly",
            image1=icon_right,
            label="spotlight",
            h=height,
            w=height,
            c=partial(self.offset_orient_y, direction=1),
        )
        cmds.text(label="Offset Z", align="right", width=label_width)
        cmds.iconTextButton(
            style="iconOnly",
            image1=icon_left,
            label="spotlight",
            h=height,
            w=height,
            c=partial(self.offset_orient_z, direction=-1),
        )
        self.offset_z = cmds.floatField(value=90.0)
        cmds.iconTextButton(
            style="iconOnly",
            image1=icon_right,
            label="spotlight",
            h=height,
            w=height,
            c=partial(self.offset_orient_z, direction=1),
        )

        cmds.setParent("..")
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.frameLayout(
            bv=False, label="Manual Orient", collapsable=True, mw=margin_width
        )
        cmds.columnLayout(adj=True)
        cmds.rowLayout(numberOfColumns=2, cw2=(150, 150))
        self.reorient_children = cmds.checkBox(
            label="Reorient children", value=True, align="left"
        )
        self.reset_orientation = cmds.checkBox(
            label="Reset orientation", value=True, align="left"
        )
        cmds.setParent("..")
        cmds.gridLayout(numberOfColumns=2, cellWidthHeight=(175, 65))
        cmds.button(label="Template Joints", command=partial(self.template_joints))
        cmds.button(label="Rebuild Joints", command=partial(rebuild_joints))
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.showWindow(self.window)

    def insert_joints(self, *args):
        joint_count = cmds.intField(self.insert_joint_field, q=True, v=True)
        skeleton.insert_joints(joint_count=joint_count)

    def template_joints(self, dummy):
        reorient_children = cmds.checkBox(
            self.reorient_children, query=True, value=True
        )
        reset_orientation = cmds.checkBox(
            self.reset_orientation, query=True, value=True
        )
        template_joints(
            reorient_children=reorient_children, reset_orientation=reset_orientation
        )

    def make_planar(self, *args):
        joints = cmds.ls(sl=True, type="joint") or []
        make_planar(joints)

    def zero_orient(self, *args):
        joints = cmds.ls(sl=True, type="joint") or []
        zero_orient(joints)

    def align_with_child(self, *args):
        joints = cmds.ls(sl=True, type="joint") or []
        align_with_child(joints)

    def orient_to_world(self, *args):
        joints = cmds.ls(sl=True, type="joint") or []
        orient_to_world(joints)

    def offset_orient_x(self, direction):
        joints = cmds.ls(sl=True, type="joint") or []
        amount = cmds.floatField(self.offset_x, q=True, value=True) * direction
        offset_orient(joints, amount, Axis.x)

    def offset_orient_y(self, direction):
        joints = cmds.ls(sl=True, type="joint") or []
        amount = cmds.floatField(self.offset_y, q=True, value=True) * direction
        offset_orient(joints, amount, Axis.y)

    def offset_orient_z(self, direction):
        joints = cmds.ls(sl=True, type="joint") or []
        amount = cmds.floatField(self.offset_z, q=True, value=True) * direction
        offset_orient(joints, amount, Axis.z)

    def set_left(self, *args):
        self.set_side(1)

    def set_center(self, *args):
        self.set_side(0)

    def set_right(self, *args):
        self.set_side(2)

    def set_side(self, side):
        nodes = cmds.ls(sl=True)
        for n in nodes:
            hierarchy = cmds.listRelatives(n, ad=True)
            hierarchy.append(n)
            for node in hierarchy:
                attr = "{}.side".format(node)
                if cmds.objExists(attr):
                    cmds.setAttr(attr, side)

        pass


class Axis:
    x = "X"
    y = "Y"
    z = "Z"


def make_planar(joints):
    for joint in joints:
        parent = cmds.listRelatives(joint, parent=True, path=True)
        if not parent:
            log.warning(
                "Cannot make %s planar because it does not have a parent.", joint
            )
            continue
        children = _unparent_children(joint)
        if not children:
            log.warning(
                "Cannot make %s planar because it does not have any children.", joint
            )
            continue
        cmds.delete(
            cmds.aimConstraint(
                children[0],
                joint,
                aim=(1, 0, 0),
                u=(0, 1, 0),
                worldUpType="object",
                worldUpObject=parent[0],
            )
        )
        cmds.makeIdentity(joint, apply=True)
        _reparent_children(joint, children)

    if joints:
        cmds.select(joints)


def make_position_planar(*args):
    sel = cmds.ls(sl=True, type="joint")
    if len(sel) <= 3:
        raise RuntimeError(
            "Select 3 joints to make a plane and then additional joints to move onto that plane."
        )
    a, b, c = [get_position(sel[i]) for i in range(3)]
    ab = (b - a).normal()
    ac = (c - a).normal()
    normal = (ab ^ ac).normal()
    joints = sel[3:]
    for joint in joints:
        children = _unparent_children(joint)
        p = get_position(joint)
        pa = a - p
        dot = pa * normal
        p = p + (normal * dot)
        cmds.xform(joint, ws=True, t=(p.x, p.y, p.z))
        _reparent_children(joint, children)

    if sel:
        cmds.select(sel)


def align_with_child(joints):
    """Aligns the up axis of the given joints with their respective child joint.

    @param joints: List of joints to orient.
    """
    for joint in joints:
        children = _unparent_children(joint)
        if children:
            cmds.delete(
                cmds.aimConstraint(
                    children[0],
                    joint,
                    aim=(1, 0, 0),
                    upVector=(0, 1, 0),
                    worldUpType="objectrotation",
                    worldUpVector=(0, 1, 0),
                    worldUpObject=children[0],
                )
            )
            cmds.makeIdentity(joint, apply=True)
        _reparent_children(joint, children)

    if joints:
        cmds.select(joints)


def zero_orient(joints):
    for joint in joints:
        children = _unparent_children(joint)
        cmds.setAttr("{0}.jointOrient".format(joint), 0, 0, 0)
        _reparent_children(joint, children)

    if joints:
        cmds.select(joints)


def orient_to_world(joints):
    """Orients the given joints with the world.

    @param joints: Joints to orient.
    """
    for joint in joints:
        children = _unparent_children(joint)
        parent = cmds.listRelatives(joint, parent=True, path=True)
        orig_joint = joint.split("|")[-1]
        if parent:
            joint = cmds.parent(joint, world=True)[0]
        cmds.joint(joint, e=True, oj="none", zso=True)
        if parent:
            joint = cmds.parent(joint, parent)[0]
            joint = cmds.rename(joint, orig_joint)
        _reparent_children(joint, children)

    if joints:
        cmds.select(joints)


def offset_orient(joints, amount, axis):
    """Offsets the orient by the given amount

    @param joints: Joints to orient.
    @param amount: Amount to offset by.
    @param axis: Which axis X, Y or Z
    """
    for joint in joints:
        children = _unparent_children(joint)
        attribute = "{0}.jointOrient{1}".format(joint, axis)
        orient = cmds.getAttr(attribute)
        orient += amount
        cmds.setAttr(attribute, orient)
        _reparent_children(joint, children)

    if joints:
        cmds.select(joints)


def _unparent_children(joint):
    """Helper function to unparent any children of the given joint.

    @param joint: Joint whose children to unparent.
    @return: A list of the unparented children.
    """
    children = cmds.listRelatives(joint, children=True, path=True) or []
    return [cmds.parent(child, world=True)[0] for child in children]


def _reparent_children(joint, children):
    """Helper function to reparent any children of the given joint.
    @param joint: Joint whose children to reparent.
    @param children: List of transforms to reparent
    """
    for child in children:
        cmds.parent(child, joint)


def template_joints(joints=None, reorient_children=True, reset_orientation=True):
    if joints is None:
        joints = cmds.ls(sl=True, type="joint")
    if not joints:
        raise RuntimeError("No joint selected to orient.")

    if reorient_children:
        children = cmds.listRelatives(fullPath=True, allDescendents=True, type="joint")
        joints.extend(children)

    red, green, blue = create_shaders()

    orient_group = cmds.createNode("transform", name=ORIENT_GROUP)
    manips = []
    for joint in joints:
        if reset_orientation:
            cmds.makeIdentity(joint, apply=True)
            cmds.joint(
                joint,
                edit=True,
                orientJoint="xyz",
                secondaryAxisOrient="yup",
                children=False,
                zeroScaleOrient=True,
            )
        if not cmds.listRelatives(joint, children=True):
            zero_orient([joint])
            continue
        group, manip = create_orient_manipulator(joint, blue)
        manips.append(manip)
        cmds.parent(group, orient_group)
        cmds.parentConstraint(joint, group)
        cmds.setAttr(joint + ".template", 1)
    cmds.select(manips)


def create_shaders():
    """
    Creates the red/green/blue shaders.
    @return: (Red, green, blue material nodes)
    """
    red = cmds.shadingNode("lambert", asShader=True)
    cmds.setAttr("{0}.color".format(red), 1, 0, 0, type="double3")
    cmds.setAttr("{0}.ambientColor".format(red), 1, 0, 0, type="double3")
    green = cmds.shadingNode("lambert", asShader=True)
    cmds.setAttr("{0}.color".format(green), 0, 1, 0, type="double3")
    cmds.setAttr("{0}.ambientColor".format(green), 0, 1, 0, type="double3")
    blue = cmds.shadingNode("lambert", asShader=True)
    cmds.setAttr("{0}.color".format(blue), 0, 0, 1, type="double3")
    cmds.setAttr("{0}.ambientColor".format(blue), 0, 0, 1, type="double3")

    t = 0.9
    for node in [red, green, blue]:
        cmds.setAttr("{0}.transparency".format(node), t, t, t, type="double3")

    return red, green, blue


def create_orient_manipulator(joint, material):
    joint_scale = cmds.jointDisplayScale(query=True)
    joint_radius = cmds.getAttr("{0}.radius".format(joint))
    radius = joint_scale * joint_radius
    children = cmds.listRelatives(joint, children=True, path=True)
    if children:
        p1 = cmds.xform(joint, q=True, ws=True, t=True)
        p1 = OpenMaya.MPoint(*p1)
        p2 = cmds.xform(children[0], q=True, ws=True, t=True)
        p2 = OpenMaya.MPoint(*p2)
        radius = p1.distanceTo(p2)
    arrow_cvs = [
        [-1, 0, 0],
        [-1, 2, 0],
        [-2, 2, 0],
        [0, 4, 0],
        [2, 2, 0],
        [1, 2, 0],
        [1, 0, 0],
        [-1, 0, 0],
    ]
    arrow_cvs = [[x[0] * radius, x[1] * radius, x[2] * radius] for x in arrow_cvs]
    shape = cmds.curve(name="{0}_zForward".format(joint), degree=1, point=arrow_cvs)
    # shape = cmds.sphere(n='{0}_zForward'.format(joint), p=(0, 0, 0), ax=(0, 0, -1), ssw=0, esw=180, r=radius, d=3, ut=0, tol=0.01, s=8, nsp=4, ch=0)[0]
    # cmds.setAttr('{0}.sz'.format(shape), 0)
    # cmds.select(shape)
    # cmds.hyperShade(assign=material)
    group = cmds.createNode("transform", name="{0}_grp".format(shape))
    cmds.parent(shape, group)
    cmds.makeIdentity(shape, apply=True)
    cmds.addAttr(shape, longName=MESSAGE_ATTRIBUTE, attributeType="message")
    cmds.connectAttr(
        "{0}.message".format(joint), "{0}.{1}".format(shape, MESSAGE_ATTRIBUTE)
    )
    for attr in ["tx", "ty", "tz", "ry", "rz", "v"]:
        cmds.setAttr("{0}.{1}".format(shape, attr), lock=True, keyable=False)
    return group, shape


def get_position(node):
    p = cmds.xform(node, q=True, ws=True, t=True)
    return OpenMaya.MPoint(p)


def create_arrow(jointName):
    curve = cmds.curve(
        name="%s_ForwardDirection" % jointName,
        degree=1,
        point=[
            (-1, 0, 0),
            (-1, 2, 0),
            (-2, 2, 0),
            (0, 4, 0),
            (2, 2, 0),
            (1, 2, 0),
            (1, 0, 0),
            (-1, 0, 0),
        ],
    )
    group = cmds.group()
    cmds.xform(objectSpace=True, pivots=(0, 0, 0))
    jointScale = cmds.jointDisplayScale(query=True)
    jointRadius = cmds.getAttr("%s.radius" % jointName)
    jointScale *= jointRadius
    cmds.xform(scale=(jointScale, jointScale, jointScale))

    return group


def rebuild_joints(*args):
    if not cmds.objExists(ORIENT_GROUP):
        return
    nodes = cmds.listRelatives(ORIENT_GROUP, ad=True, path=True) or []

    joints = []
    for node in nodes:
        attrs = cmds.listAttr(node, ud=True) or []
        if MESSAGE_ATTRIBUTE not in attrs:
            continue
        joint = cmds.listConnections(
            "{0}.{1}".format(node, MESSAGE_ATTRIBUTE), d=False
        )[0]
        joints.append(joint)
        rotation = cmds.getAttr("{0}.rx".format(node))

        children = cmds.listRelatives(joint, children=True, shapes=False, path=True)
        if children:
            # First unparent children so change in joint orient does not affect children
            children = [cmds.parent(child, world=True)[0] for child in children]

            # Add rotation offset to joint orient
            orient_x = cmds.getAttr("{0}.jointOrientX".format(joint))
            orient_x += rotation
            while orient_x > 180.0:
                orient_x -= 360.0
            while orient_x < -180.0:
                orient_x += 360.0
            cmds.setAttr("{0}.jointOrientX".format(joint), orient_x)

            # Reparent child
            for child in children:
                cmds.parent(child, joint)

        else:
            # tip joint, just zero out joint orient
            cmds.setAttr("%s.jointOrientX" % joint, 0)
            cmds.setAttr("%s.jointOrientY" % joint, 0)
            cmds.setAttr("%s.jointOrientZ" % joint, 0)

        # Untemplate
        cmds.setAttr("{0}.template".format(joint), 0)

    # Delete arrow group
    cmds.delete(ORIENT_GROUP)
    cmds.select(joints)
