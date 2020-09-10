"""Space switching without constraints or extra DAG nodes.

Contains functions to create a space switching network as well as seamlessly switching
between spaces.

Example Usage
=============

::

    import cmt.rig.spaceswitch as spaceswitch

    # Create the space switch
    spaceswitch.create_space_switch(
        pole_vector_control,
        [(ik_control, "foot"), (root_control, "root"), (world_control, "world")],
        switch_attribute="space",
        use_rotate=False,
    )

    # Seamless switch
    spaceswitch.switch_space(pole_vector_control, "space", 1, create_keys=False)

"""
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
from cmt.dge import dge
import cmt.rig.common as common
import cmt.shortcuts as shortcuts


def create_space_switch(
    node, drivers, switch_attribute=None, use_translate=True, use_rotate=True
):
    """Creates a space switch network.

    The network uses the offsetParentMatrix attribute and does not create any
    constraints or new dag nodes.

    :param node: Transform to drive
    :param drivers: List of tuples: [(driver1, "spaceName1"), (driver2, "spaceName2")]
    :param switch_attribute: Name of the switch attribute to create on the target node.
    """
    if switch_attribute is None:
        switch_attribute = "space"

    if cmds.objExists("{}.{}".format(node, switch_attribute)):
        cmds.deleteAttr(node, at=switch_attribute)
    names = [d[1] for d in drivers]
    cmds.addAttr(node, ln=switch_attribute, at="enum", en=":".join(names), keyable=True)

    # Create attribute to toggle translation in the matrices
    enable_translate_attr = _create_bool_attribute(
        node, "{}UseTranslate".format(switch_attribute), use_translate
    )

    # Create attribute to toggle rotation in the matrices
    enable_rotate_attr = _create_bool_attribute(
        node, "{}UseRotate".format(switch_attribute), use_rotate
    )

    blend = cmds.createNode("blendMatrix", name="{}_spaceswitch".format(node))

    # Get the current offset parent matrix.  This is used as the starting blend point
    m = OpenMaya.MMatrix(cmds.getAttr("{}.offsetParentMatrix".format(node)))
    cmds.setAttr("{}.inputMatrix".format(blend), list(m), type="matrix")

    parent = cmds.listRelatives(node, parent=True, path=True)
    to_parent_local = "{}.worldInverseMatrix[0]".format(parent[0]) if parent else None

    for i, driver in enumerate(drivers):
        driver = driver[0]

        _connect_driver_matrix_network(blend, node, driver, i, to_parent_local)

        target_attr = "{}.target[{}]".format(blend, i)

        # Hook up the weight toggle when switching spaces
        dge(
            "x = switch == {} ? 1 : 0".format(i),
            x="{}.weight".format(target_attr),
            switch="{}.{}".format(node, switch_attribute),
        )

        # Connect the translation, rotation toggles
        cmds.connectAttr(enable_translate_attr, "{}.useTranslate".format(target_attr))
        cmds.connectAttr(enable_rotate_attr, "{}.useRotate".format(target_attr, i))

    cmds.connectAttr(
        "{}.outputMatrix".format(blend), "{}.offsetParentMatrix".format(node)
    )


def _create_bool_attribute(node, attribute, default_value):
    cmds.addAttr(
        node, ln=attribute, at="bool", defaultValue=default_value, keyable=True
    )
    return "{}.{}".format(node, attribute)


def _connect_driver_matrix_network(blend, node, driver, index, to_parent_local):
    # The multMatrix node will calculate the transformation to blend to when driven
    # by this driver transform
    mult = cmds.createNode(
        "multMatrix", name="spaceswitch_{}_to_{}".format(node, driver)
    )

    offset = (
         shortcuts.get_dag_path2(node).exclusiveMatrix()
         * OpenMaya.MMatrix(cmds.getAttr("{}.worldInverseMatrix[0]".format(driver)))
    )
    cmds.setAttr("{}.matrixIn[0]".format(mult), list(offset), type="matrix")

    cmds.connectAttr("{}.worldMatrix[0]".format(driver), "{}.matrixIn[1]".format(mult))

    if to_parent_local:
        cmds.connectAttr(to_parent_local, "{}.matrixIn[2]".format(mult))

    cmds.connectAttr(
        "{}.matrixSum".format(mult), "{}.target[{}].targetMatrix".format(blend, index)
    )


def switch_space(node, attribute, space, create_keys=False):
    """Seamlessly switch between spaces

    :param node: Node to switch
    :param attribute: Space switching attribute on node
    :param space: Space index in the space attribute
    :param create_keys: True to create switching keys
    """
    m = cmds.xform(node, q=True, ws=True, m=True)
    cmds.setAttr("{}.{}".format(node, attribute), space)
    cmds.xform(node, ws=True, m=m)
