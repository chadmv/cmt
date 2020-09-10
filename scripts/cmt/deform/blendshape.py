import os
from six import string_types
import maya.cmds as cmds

from cmt.io.obj import import_obj, export_obj
import cmt.shortcuts as shortcuts
import cmt.deform.np_mesh as np_mesh
import cmt.rig.common as common


def get_blendshape_node(geometry):
    """Get the first blendshape node upstream from the given geometry.

    :param geometry: Name of the geometry
    :return: The blendShape node name
    """
    geometry = shortcuts.get_shape(geometry)
    history = cmds.listHistory(geometry, il=2, pdo=False) or []
    blendshapes = [
        x
        for x in history
        if cmds.nodeType(x) == "blendShape"
        and cmds.blendShape(x, q=True, g=True)[0] == geometry
    ]
    if blendshapes:
        return blendshapes[0]
    else:
        return None


def get_or_create_blendshape_node(geometry):
    """Get the first blendshape node upstream from the given geometry or create one if
    one does not exist.

    :param geometry: Name of the geometry
    :return: The blendShape node name
    """
    geometry = shortcuts.get_shape(geometry)
    blendshape = get_blendshape_node(geometry)
    if blendshape:
        return blendshape
    else:
        return cmds.blendShape(geometry, foc=True)[0]


def get_target_index(blendshape, target):
    indices = cmds.getAttr("{}.w".format(blendshape), mi=True) or []
    for i in indices:
        alias = cmds.aliasAttr("{}.w[{}]".format(blendshape, i), q=True)
        if alias == target:
            return i
    raise RuntimeError(
        "Target {} does not exist on blendShape {}".format(target, blendshape)
    )


def add_target(blendshape, target):
    # Check if target already exists
    try:
        index = get_target_index(blendshape, target)
    except RuntimeError:
        index = cmds.getAttr("{}.w".format(blendshape), mi=True)
        index = index[-1] + 1 if index else 0

    base = cmds.blendShape(blendshape, q=True, g=True)[0]
    cmds.blendShape(blendshape, e=True, t=(base, index, target, 1.0))
    return index


def get_target_list(blendshape):
    indices = cmds.getAttr("{}.w".format(blendshape), mi=True) or []
    targets = [
        cmds.aliasAttr("{}.w[{}]".format(blendshape, i), q=True) for i in indices
    ]
    return targets


def set_target_weights(blendshape, target, weights):

    index = get_target_index(blendshape, target)
    for i, w in enumerate(weights):
        cmds.setAttr(
            "{}.inputTarget[0].inputTargetGroup[{}].targetWeights[{}]".format(
                blendshape, index, i
            ),
            w,
        )


def import_obj_directory(directory, base_mesh=None):
    if base_mesh:
        blendshape = get_or_create_blendshape_node(base_mesh)
    for f in os.listdir(directory):
        if not f.lower().endswith(".obj") or f.startswith("_"):
            continue
        full_path = os.path.join(directory, f)
        target = import_obj(full_path)
        if base_mesh:
            add_target(blendshape, target)
            cmds.delete(target)


def export_blendshape_targets(blendshape, directory):
    """Export all targets of a blendshape as objs.

    :param blendshape: Blendshape name
    :param directory: Directory path
    """
    connections = zero_weights(blendshape)
    targets = get_target_list(blendshape)
    base = cmds.blendShape(blendshape, q=True, g=True)[0]
    for t in targets:
        plug = "{}.{}".format(blendshape, t)
        cmds.setAttr(plug, 1)
        file_path = os.path.join(directory, "{}.obj".format(t))
        export_obj(base, file_path)
        cmds.setAttr(plug, 0)
    restore_weights(blendshape, connections)


def zero_weights(blendshape):
    """Disconnects all connections to blendshape target weights and zero's
     out the weights.

    :param blendshape: Blendshape node name
    :return: Dictionary of connections dict[target] = connection
    """
    connections = {}
    targets = get_target_list(blendshape)
    for t in targets:
        plug = "{}.{}".format(blendshape, t)
        connection = cmds.listConnections(plug, plugs=True, d=False)
        if connection:
            connections[t] = connection[0]
            cmds.disconnectAttr(connection[0], plug)
        cmds.setAttr(plug, 0)
    return connections


def restore_weights(blendshape, connections):
    """Restore the weight connections disconnected from zero_weights.

    :param blendshape: Blendshape name
    :param connections: Dictionary of connections returned from zero_weights.
    """
    for target, connection in connections.items():
        cmds.connectAttr(connection, "{}.{}".format(blendshape, target))


def transfer_shapes(source, destination, blendshape=None):
    """Transfers the shapes on the given blendshape to the destination mesh.

    It is assumed the blendshape indirectly deforms the destination mesh.

    :param source: Mesh to transfer shapes from.
    :param destination: Mesh to transfer shapes to.
    :param blendshape: Optional blendshape node name.  If no blendshape is given, the
        blendshape on the source mesh will be used.
    :return: The new blendshape node name.
    """
    if blendshape is None:
        blendshape = get_blendshape_node(source)
        if blendshape is None:
            return
    connections = zero_weights(blendshape)
    targets = get_target_list(blendshape)
    new_targets = []
    for t in targets:
        cmds.setAttr("{}.{}".format(blendshape, t), 1)
        new_targets.append(cmds.duplicate(destination, name=t)[0])
        cmds.setAttr("{}.{}".format(blendshape, t), 0)
    cmds.delete(destination, ch=True)
    new_blendshape = cmds.blendShape(new_targets, destination, foc=True)[0]
    cmds.delete(new_targets)
    for t in targets:
        cmds.connectAttr(
            "{}.{}".format(blendshape, t), "{}.{}".format(new_blendshape, t)
        )
    restore_weights(blendshape, connections)
    return new_blendshape


def propagate_neutral_update(old_neutral, new_neutral, shapes):
    """Propagate neutral update deltas to target shapes

    :param old_neutral: The old neutral mesh
    :param new_neutral: The new neutral mesh
    :param shapes: The list of shapes to update
    """
    _old = np_mesh.Mesh.from_maya_mesh(old_neutral)
    _new = np_mesh.Mesh.from_maya_mesh(new_neutral)
    delta = _new - _old
    for shape in shapes:
        _shape = np_mesh.Mesh.from_maya_mesh(shape)
        new_shape = _shape + delta
        new_shape.to_maya_mesh(shape)


def create_shapes_joint(blendshapes, parent, name="shapes"):
    """Create a joint with a weight attribute per each blendshape target.

    This is used to export blendshape animation with the skeleton.

    :param blendshapes: List of blendshape nodes.
    :param parent: Joint to parent the new joint under.
    :param name: Name of the new joint. "shapes" by default.
    :return: The new joint name
    """
    joint = cmds.createNode("joint", name=name)
    common.snap_to(joint, parent)
    cmds.parent(joint, parent)
    cmds.makeIdentity(joint, t=True, r=True, s=True, apply=True)
    if isinstance(blendshapes, string_types):
        blendshapes = [blendshapes]

    for blendshape in blendshapes:
        targets = get_target_list(blendshape)
        for t in targets:
            attr = "{}.{}".format(joint, t)
            if not cmds.objExists(attr):
                cmds.addAttr(joint, ln=t, keyable=True)
            if not cmds.listConnections(attr, d=False):
                cmds.connectAttr("{}.{}".format(blendshape, t), attr)
    return joint
