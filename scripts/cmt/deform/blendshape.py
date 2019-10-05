import maya.cmds as cmds

import cmt.shortcuts as shortcuts


def get_or_create_blendshape_node(geometry):
    """Get the first blendshape node upstream from the given geometry or create one if
    one does not exist.

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
        return cmds.blendShape(geometry)[0]


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


def set_target_weights(blendshape, target, weights):

    index = get_target_index(blendshape, target)
    for i, w in enumerate(weights):
        cmds.setAttr(
            "{}.inputTarget[0].inputTargetGroup[{}].targetWeights[{}]".format(
                blendshape, index, i
            ),
            w,
        )
