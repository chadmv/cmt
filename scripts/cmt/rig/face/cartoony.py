import maya.cmds as cmds
from itertools import product


class Side(object):
    left = "L"
    middle = "M"
    right = "R"
    top = "T"
    bottom = "B"
    left_right = [left, right]


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
        "tokens": [Side.left_right, [Direction.left_right, Direction.up_down]],
    },
    {"name": "lipPressor", "tokens": [Side.left_right]},
    {
        "name": "lipRoll",
        "tokens": [
            [
                "{}{}".format(Side.left, Side.bottom),
                "{}{}".format(Side.right, Side.bottom),
                "{}{}".format(Side.left, Side.top),
                "{}{}".format(Side.right, Side.top),
            ]
        ],
    },
    {
        "name": "eyeLidLower",
        "tokens": [
            Side.left_right,
            Section.inner_middle_outer,
            [Direction.left_right, Direction.up_down],
        ],
    },
    {
        "name": "eyeLidUpper",
        "tokens": [
            Side.left_right,
            Section.inner_middle_outer,
            [Direction.left_right, Direction.up_down],
        ],
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
    {"name": "noseWrinkler", "tokens": [Side.left_right]},
    {"name": "pucker", "tokens": [Side.left_right]},
    {
        "name": "lipLower",
        "tokens": [
            [Side.left, Side.middle, Side.right],
            [Direction.in_out, Direction.left_right, Direction.up_down],
        ],
    },
    {
        "name": "lipUpper",
        "tokens": [
            [Side.left, Side.middle, Side.right],
            [Direction.in_out, Direction.left_right, Direction.up_down],
        ],
    },
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

    def add_secondary_driver(self, target, driver, weight):
        """Add a new driver to the attribute in second layer.

        :param target: Attribute to drive
        :param driver: Attribute on the first layer to add as a driver
        :param weight: Weight multiplier to use with the driver
        """
        blend = self.get_blend_weighted(target)
        index = cmds.getAttr("{}.input".format(blend), mi=True)[-1] + 1
        cmds.connectAttr(
            "{}.{}".format(self.anim_node, driver), "{}.input[{}]".format(blend, index)
        )
        cmds.setAttr("{}.w[{}]".format(blend, index), weight)


def create_attribute_node(name="face_animation"):
    node = DrivenAnimationNode(name)
    node.create()
    return node
