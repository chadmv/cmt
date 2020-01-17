import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import cmt.shortcuts as shortcuts
from six import string_types

HIERARCHY = {
    "top": {"anim": None, "skeleton": None, "rig": {"orients": None}, "geo": None}
}


class RigHierarchy(object):
    def __init__(self, hierarchy=None, prefix=None, suffix=None, lock_and_hide=None):
        if hierarchy is None:
            hierarchy = HIERARCHY
        self.hierarchy = hierarchy
        self.prefix = prefix or ""
        self.suffix = "_grp" if suffix is None else suffix
        self.lock_and_hide = lock_and_hide or ["t", "r", "s", "v"]

    def create(self, hierarchy=None, parent=None):
        if hierarchy is None:
            hierarchy = self.hierarchy
        for name, children in hierarchy.items():
            node = "{}{}{}".format(self.prefix, name, self.suffix)
            setattr(self, name, node)
            func = _create_parent_method(node)
            setattr(self, "parent_to_{}".format(name), func)
            if not cmds.objExists(node):
                node = cmds.createNode("transform", name=node)
            if parent:
                current_parent = cmds.listRelatives(node, parent=True, path=True)
                if current_parent:
                    current_parent = current_parent[0]
                if current_parent != parent:
                    cmds.parent(node, parent)
            lock_and_hide(node, attributes=self.lock_and_hide)
            if children:
                self.create(children, node)

    def delete(self, name):
        """Delete the node from the hierarchy

        :param name: Hierarchy node name (Could be different from the Maya node name)
        """
        cmds.delete(getattr(self, name))
        delattr(self, name)


def _create_parent_method(node):
    def func(nodes_to_parent):
        cmds.parent(nodes_to_parent, node)

    return func


def lock_and_hide(node, attributes):
    """

    :param node:
    :param attributes:
    :return:
    """
    for attr in attributes:
        if attr in ["translate", "rotate", "scale"]:
            for x in "XYZ":
                cmds.setAttr("%s.%s%s" % (node, attr, x), lock=True, keyable=False)
        elif attr in ["t", "r", "s"]:
            for x in "xyz":
                cmds.setAttr("%s.%s%s" % (node, attr, x), lock=True, keyable=False)
        else:
            cmds.setAttr("%s.%s" % (node, attr), lock=True, keyable=False)


def duplicate_chain(start, end, prefix="", suffix="", search_for="", replace_with=""):
    """Duplicates the transform chain starting at start and ending at end.

    :param start: The start transform.
    :param end: The end transform.
    :param prefix: Prefix to add to the new chain.
    :param suffix: Suffix to add to the new chain.
    :param search_for: Search for token
    :param replace_with: Replace token
    :return: A list of the duplicated joints, a list of the original joints that were
    duplicated.
    """
    joint = end
    joints = []
    original_joints = []
    while joint:
        name = "{0}{1}{2}".format(prefix, joint, suffix)
        if search_for or replace_with:
            name = name.replace(search_for, replace_with)
        original_joints.append(joint)
        duplicate_joint = cmds.duplicate(joint, name=name, parentOnly=True)[0]
        if joints:
            cmds.parent(joints[-1], duplicate_joint)
        joints.append(duplicate_joint)
        if joint == start:
            break
        joint = cmds.listRelatives(joint, parent=True, path=True)
        if joint:
            joint = joint[0]
        else:
            raise RuntimeError("{0} is not a descendant of {1}".format(end, start))
    joints.reverse()
    original_joints.reverse()
    return joints, original_joints


def connect_attribute(
    source,
    destination,
    offset=0,
    multiplier=None,
    negate=False,
    clamp=False,
    inverse=False,
):
    output = source
    name = source.split(".")[-1]
    if negate:
        mdl = cmds.createNode("multDoubleLinear", name="{}_negate".format(name))
        cmds.setAttr("{}.input1".format(mdl), -1)
        cmds.connectAttr(output, "{}.input2".format(mdl))
        output = "{}.output".format(mdl)

    if clamp:
        clamp_node = cmds.createNode("clamp", name="{}_clamp".format(name))
        cmds.setAttr("{}.minR".format(clamp_node), clamp[0])
        cmds.setAttr("{}.maxR".format(clamp_node), clamp[1])
        cmds.connectAttr(output, "{}.inputR".format(clamp_node))
        output = "{}.outputR".format(clamp_node)

    if multiplier is not None:
        mdl = cmds.createNode("multDoubleLinear", name="{}_multiplier".format(name))
        cmds.setAttr("{}.input1".format(mdl), multiplier)
        cmds.connectAttr(output, "{}.input2".format(mdl))
        output = "{}.output".format(mdl)

    if offset:
        adl = cmds.createNode("addDoubleLinear", name="{}_offset".format(name))
        cmds.setAttr("{}.input1".format(adl), offset)
        cmds.connectAttr(output, "{}.input2".format(adl))
        output = "{}.output".format(adl)

    if inverse:
        pma = cmds.createNode("plusMinusAverage", name="{}_inverse".format(name))
        cmds.setAttr("{}.operation".format(pma), 2)  # subtract
        cmds.setAttr("{}.input1D[0]".format(pma), 1)
        cmds.connectAttr(output, "{}.input1D[1]".format(pma))
        output = "{}.output1D".format(pma)

    cmds.connectAttr(output, destination)


def freeze_to_parent_offset(node=None):
    """Transfer the local matrix of the specified node into the offsetParentMatrix

    :param node: Node name or list of node names
    """
    if node is None:
        node = cmds.ls(sl=True)
    if node is None:
        return

    if not isinstance(node, string_types):
        for n in node:
            freeze_to_parent_offset(n)
        return

    if cmds.about(api=True) < 20200000:
        raise RuntimeError("offsetParentMatrix is only available starting in Maya 2020")

    m = OpenMaya.MMatrix(cmds.getAttr("{}.worldMatrix[0]".format(node)))
    pinv = OpenMaya.MMatrix(cmds.getAttr("{}.parentInverseMatrix[0]".format(node)))
    offset = m * pinv
    cmds.setAttr("{}.offsetParentMatrix".format(node), list(offset), type="matrix")
    for attr in ["jo", "ra"]:
        if cmds.objExists("{}.{}".format(node, attr)):
            cmds.setAttr("{}.{}".format(node, attr), 0, 0, 0)

    for attr in ["{}{}".format(x, y) for x in "trs" for y in "xyz"]:
        is_locked = cmds.getAttr("{}.{}".format(node, attr), lock=True)
        if is_locked:
            cmds.setAttr("{}.{}".format(node, attr), lock=False)
        value = 1.0 if attr.startswith("s") else 0.0
        cmds.setAttr("{}.{}".format(node, attr), value)
        if is_locked:
            cmds.setAttr("{}.{}".format(node, attr), lock=True)


def snap_to_position(node, snap_to):
    pos = cmds.xform(snap_to, q=True, ws=True, t=True)
    cmds.xform(node, ws=True, t=pos)

def snap_to_orientation(node, snap_to):
    r = cmds.xform(snap_to, q=True, ws=True, ro=True)
    cmds.xform(node, ws=True, ro=r)

def snap_to(node, snap_to):
    snap_to_position(node, snap_to)
    snap_to_orientation(node, snap_to)
