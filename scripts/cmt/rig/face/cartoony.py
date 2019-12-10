import maya.cmds as cmds
from itertools import product


class Side(object):
    left = "l"
    middle = "m"
    right = "r"
    top = "t"
    bottom = "b"
    left_right = [left, right]
    left_middle_right = [left, middle, right]


class Section(object):
    inner = "inn"
    middle = "mid"
    outer = "out"
    inner_middle_outer = [inner, middle, outer]


class Direction(object):
    in_out = "inOut"
    up_down = "upDown"
    left_right = "leftRight"
    twist = "twist"


def get_name_combinations(name, tokens=None):
    result = list(product(*tokens)) if tokens else []
    result = ["{}_{}".format(name, "_".join(v)) for v in result]
    return result


ATTRIBUTES = [
    {
        "name": "brow",
        "tokens": [
            Side.left_right,
            Section.inner_middle_outer,
            [Direction.in_out, Direction.up_down],
        ],
    },
    {
        "name": "brow",
        "tokens": [Side.left_right, [Direction.in_out, Direction.up_down]],
    },
    {"name": "browTwist", "tokens": [Side.left_right]},
    {"name": "cheek", "tokens": [Side.left_right, [Direction.in_out]]},
    {"name": "cheekRaiser", "tokens": [Side.left_right]},
    {"name": "dimpler", "tokens": [Side.left_right]},
    {"name": "funneler", "tokens": [Side.left_right]},
    {
        "name": "jaw",
        "tokens": [
            [Direction.in_out, Direction.left_right, Direction.twist, Direction.up_down]
        ],
    },
    {
        "name": "lipCorner",
        "tokens": [Side.left_right, [Direction.in_out, Direction.up_down]],
    },
    {"name": "lipPressor", "tokens": [Side.left_right]},
    {"name": "lipUpperRoll", "tokens": [Side.left_right]},
    {"name": "lipLowerRoll", "tokens": [Side.left_right]},
    {
        "name": "eyeLidLower",
        "tokens": [
            Side.left_right,
            Section.inner_middle_outer,
            [Direction.in_out, Direction.up_down],
        ],
    },
    {
        "name": "eyeLidLower",
        "tokens": [Side.left_right, [Direction.in_out, Direction.up_down]],
    },
    {
        "name": "eyeLidUpper",
        "tokens": [
            Side.left_right,
            Section.inner_middle_outer,
            [Direction.in_out, Direction.up_down],
        ],
    },
    {
        "name": "eyeLidUpper",
        "tokens": [Side.left_right, [Direction.in_out, Direction.up_down]],
    },
    {
        "name": "mouth",
        "tokens": [
            [Direction.in_out, Direction.left_right, Direction.twist, Direction.up_down]
        ],
    },
    {
        "name": "nose",
        "tokens": [
            [Direction.in_out, Direction.left_right, Direction.twist, Direction.up_down]
        ],
    },
    {"name": "noseRotate", "tokens": [[Direction.up_down]]},
    {"name": "noseTip", "tokens": [[Direction.left_right, Direction.up_down]]},
    {"name": "noseWrinkler", "tokens": [Side.left_right]},
    {"name": "pucker", "tokens": [Side.left_right]},
    {
        "name": "lipLower",
        "tokens": [
            [Side.left, Side.middle, Side.right],
            [Direction.in_out, Direction.left_right, Direction.up_down],
        ],
    },
    {"name": "lipLowerPinch", "tokens": [Side.left_right]},
    {
        "name": "lipUpper",
        "tokens": [
            [Side.left, Side.middle, Side.right],
            [Direction.in_out, Direction.left_right, Direction.up_down],
        ],
    },
    {"name": "lipUpperPinch", "tokens": [Side.left_right]},
]


class DrivenAnimationNode(object):
    """Encapsulates layered animation attributes.

    There are two layers of attributes.  The attributes on the first layer
    are meant to be controller directly.  This first layer drives the attributes on the
    second layer through any combination of node networks.

    +-----+                 +-----+
    |     |                 |     |
    |  a  +---------+------>+  a  | = a
    |     |         |       |     |
    |  b  +---------v------>+  b  | = b+a
    |     |                 |     |
    |  c  +---------------->+  c  | = c
    |     |                 |     |
    +-----+                 +-----+

    """

    def __init__(self, name):
        self.name = name
        self.blend_weighted = {}

    def create(self):
        self.anim_node = cmds.createNode("transform", name=self.name)
        self.driven_node = cmds.createNode(
            "transform", name="{}_driven".format(self.name)
        )
        for attr in ["{}{}".format(x, y) for x in "trs" for y in "xyz"] + ["v"]:
            cmds.setAttr("{}.{}".format(self.anim_node, attr), lock=True, keyable=False)
            cmds.setAttr(
                "{}.{}".format(self.driven_node, attr), lock=True, keyable=False
            )

        for attr in ATTRIBUTES:
            names = get_name_combinations(attr["name"], attr.get("tokens", []))
            for name in names:
                cmds.addAttr(self.anim_node, ln=name, keyable=True, at="float")
                cmds.addAttr(self.driven_node, ln=name, keyable=True, at="float")
                blend = cmds.createNode(
                    "blendWeighted", name="{}_blendWeighted".format(name)
                )
                cmds.connectAttr(
                    "{}.{}".format(self.anim_node, name), "{}.input[0]".format(blend)
                )
                cmds.setAttr("{}.weight[0]".format(blend), 1.0)
                cmds.connectAttr(
                    "{}.output".format(blend), "{}.{}".format(self.driven_node, name)
                )
                self.blend_weighted[name] = blend

    def get_blend_weighted(self, name):
        return self.blend_weighted[name]

    def add_secondary_driver(
        self,
        target,
        driver,
        weight,
        offset=0,
        multiplier=None,
        negate=False,
        clamp=False,
        inverse=False,
    ):
        """Add a new driver to the attribute in second layer.

        :param target: Attribute to drive
        :param driver: Attribute on the first layer to add as a driver
        :param weight: Weight multiplier to use with the driver
        :param clamp: True to clamp the min driver weight to 0
        """
        blend = self.get_blend_weighted(target)
        index = cmds.getAttr("{}.input".format(blend), mi=True)[-1] + 1
        source = (
            driver
            if cmds.objExists(driver)
            else "{}.{}".format(self.driven_node, driver)
        )
        connect_attribute(
            source,
            "{}.input[{}]".format(blend, index),
            offset,
            multiplier,
            negate,
            clamp,
            inverse,
        )
        if isinstance(weight, float):
            cmds.setAttr("{}.w[{}]".format(blend, index), weight)
        else:
            cmds.connectAttr(weight, "{}.w[{}]".format(blend, index))
        return blend


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
        clamp = cmds.createNode("clamp", name="{}_clamp".format(name))
        cmds.setAttr("{}.minR".format(clamp), 0.0)
        cmds.setAttr("{}.maxR".format(clamp), 10.0)
        cmds.connectAttr(output, "{}.inputR".format(clamp))
        output = "{}.outputR".format(clamp)

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


def create_attribute_node(name="face_animation"):
    node = DrivenAnimationNode(name)
    node.create()
    return node
