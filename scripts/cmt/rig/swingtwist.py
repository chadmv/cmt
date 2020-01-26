"""Creates a node network to extract twist rotation of a transform to drive another
transform.

The network calculates the local rotation twist offset around a specified twist axis
relative to the local rest orientation.  This allows users to specify how much
twist they want to propagate to another transform.  Uses include driving an upper arm
twist joint from the shoulder and driving forearm twist joints from the wrist.

Since the network uses quaternions, partial twist values between 0.0 and 1.0 will see a
flip when the driver transform rotates past 180 degrees.

Example Usage
=============
The twist decomposition network can be accessed in the cmt menu::

    CMT > Rigging > Connect Twist Joint

Twist child of shoulder::

    shoulder
      |- twist_joint1
      |- twist_joint2
      |- elbow

    create_twist_decomposition(shoulder, twist_joint1, invert=True)
    create_twist_decomposition(shoulder, twist_joint2, invert=True, twist_weight=0.5)

Twist forearm from wrist::

    elbow
      |- twist_joint1
      |- twist_joint2
      |- wrist

    create_twist_decomposition(wrist, twist_joint1, invert=False, twist_weight=0.5)
    create_twist_decomposition(wrist, twist_joint2, invert=False)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as OpenMaya

from cmt.ui.optionbox import OptionBox
from cmt.settings import DOCUMENTATION_ROOT
from cmt.dge import dge
import cmt.shortcuts as shortcuts
import math

logger = logging.getLogger(__name__)

# User defined attribute names used in the network
TWIST_WEIGHT = "twist"
SWING_WEIGHT = "swing"
TWIST_OUTPUT = "twistOutput"
INV_TWIST_OUTPUT = "invertedTwistOutput"
SWING_OUTPUT = "swingOutput"
INV_SWING_OUTPUT = "invertedSwingOutput"

HELP_URL = "{}/rig/twistdecomposition.html".format(DOCUMENTATION_ROOT)


def create_swing_twist(
    driver, driven, twist_weight=1.0, swing_weight=1.0, twist_axis=0
):
    """Create a node network to drive a transforms rotation from the decomposed twist of
    another transform.

    :param driver: Driver transform
    :param driven: Driven transform
    :param twist_weight: -1 to 1 twist scalar
    :param swing_weight: -1 to 1 swing scalar
    :param twist_axis: Local twist axis on driver such as (1.0, 0.0, 0.0).  If not
        specified, the twist axis will be calculated as the vector to the first child.
        If the driver has no children, the twist axis will be (1.0, 0.0, 0.0).
    """
    for attr in [TWIST_OUTPUT, INV_TWIST_OUTPUT, SWING_OUTPUT, INV_SWING_OUTPUT]:
        if not cmds.objExists("{}.{}".format(driver, attr)):
            cmds.addAttr(driver, ln=attr, at="message")

    if not _twist_network_exists(driver):
        _create_twist_decomposition_network(driver, twist_axis)
    for attr in [TWIST_WEIGHT, SWING_WEIGHT]:
        if not cmds.objExists("{}.{}".format(driven, attr)):
            cmds.addAttr(
                driven,
                ln=attr,
                keyable=True,
                minValue=0,
                maxValue=1,
                defaultValue=math.fabs(twist_weight),
            )

    twist, inv_twist, swing, inv_swing = _get_swing_twist_attributes(driver)

    twist_slerp = _create_slerp(driven, twist_weight, twist, inv_twist, TWIST_WEIGHT)
    swing_slerp = _create_slerp(driven, swing_weight, swing, inv_swing, SWING_WEIGHT)

    rotation = cmds.createNode("quatProd", name="{}_rotation".format(driver))
    cmds.connectAttr(
        "{}.outputQuat".format(twist_slerp), "{}.input1Quat".format(rotation)
    )
    cmds.connectAttr(
        "{}.outputQuat".format(swing_slerp), "{}.input2Quat".format(rotation)
    )

    rotation_matrix = cmds.createNode(
        "composeMatrix", name="{}_rotation_matrix".format(driver)
    )
    cmds.setAttr("{}.useEulerRotation".format(rotation_matrix), 0)
    cmds.connectAttr(
        "{}.outputQuat".format(rotation), "{}.inputQuat".format(rotation_matrix)
    )

    mult = cmds.createNode("multMatrix", name="{}_offset_parent_matrix".format(driven))
    cmds.connectAttr(
        "{}.outputMatrix".format(rotation_matrix), "{}.matrixIn[0]".format(mult)
    )

    pinv = OpenMaya.MMatrix(cmds.getAttr("{}.parentInverseMatrix[0]".format(driven)))
    m = OpenMaya.MMatrix(cmds.getAttr("{}.worldMatrix[0]".format(driven)))
    local_rest_matrix = m * pinv
    cmds.setAttr("{}.matrixIn[1]".format(mult), list(local_rest_matrix), type="matrix")

    cmds.connectAttr(
        "{}.matrixSum".format(mult), "{}.offsetParentMatrix".format(driven)
    )

    # Zero out local xforms to prevent double xform
    for attr in ["{}{}".format(x, y) for x in ["t", "r", "jo"] for y in "xyz"]:
        is_locked = cmds.getAttr("{}.{}".format(driven, attr), lock=True)
        if is_locked:
            cmds.setAttr("{}.{}".format(driven, attr), lock=False)
        cmds.setAttr("{}.{}".format(driven, attr), 0.0)
        if is_locked:
            cmds.setAttr("{}.{}".format(driven, attr), lock=True)

    logger.info(
        "Created swing twist network to drive {} from {}".format(driven, driver)
    )


def _twist_network_exists(driver):
    """Test whether the twist decomposition network already exists on driver.

    :param driver: Driver transform
    :return: True or False
    """
    has_twist_attribute = cmds.objExists("{}.{}".format(driver, TWIST_OUTPUT))
    if not has_twist_attribute:
        return False
    twist_node = cmds.listConnections("{}.{}".format(driver, TWIST_OUTPUT), d=False)
    return True if twist_node else False


def _create_twist_decomposition_network(driver, twist_axis):
    """Create the twist decomposition network for driver.

    :param driver: Driver transform
    :param twist_axis: Local twist axis on driver
    """
    # Connect message attributes to the decomposed twist nodes so we can reuse them
    # if the network is driving multiple nodes

    mult = cmds.createNode("multMatrix", name="{}_local_matrix".format(driver))
    parent_inverse = "{}.parentInverseMatrix[0]".format(driver)
    world_matrix = "{}.worldMatrix[0]".format(driver)
    cmds.connectAttr(world_matrix, "{}.matrixIn[0]".format(mult))
    cmds.connectAttr(parent_inverse, "{}.matrixIn[1]".format(mult))
    pinv = OpenMaya.MMatrix(cmds.getAttr(parent_inverse))
    m = OpenMaya.MMatrix(cmds.getAttr(world_matrix))
    inv_local_rest_matrix = (m * pinv).inverse()
    cmds.setAttr(
        "{}.matrixIn[2]".format(mult), list(inv_local_rest_matrix), type="matrix"
    )

    rotation = cmds.createNode("decomposeMatrix", name="{}_rotation".format(driver))
    cmds.connectAttr("{}.matrixSum".format(mult), "{}.inputMatrix".format(rotation))

    twist = cmds.createNode("quatNormalize", name="{}_twist".format(driver))
    cmds.connectAttr(
        "{}.outputQuat.outputQuatW".format(rotation),
        "{}.inputQuat.inputQuatW".format(twist),
    )
    axis = "XYZ"[twist_axis]
    cmds.connectAttr(
        "{}.outputQuat.outputQuat{}".format(rotation, axis),
        "{}.inputQuat.inputQuat{}".format(twist, axis),
    )

    # swing = twist.inverse() * rotation
    inv_twist = cmds.createNode("quatInvert", name="{}_inverse_twist".format(driver))
    cmds.connectAttr("{}.outputQuat".format(twist), "{}.inputQuat".format(inv_twist))
    swing = cmds.createNode("quatProd", name="{}_swing".format(driver))
    cmds.connectAttr("{}.outputQuat".format(inv_twist), "{}.input1Quat".format(swing))
    cmds.connectAttr("{}.outputQuat".format(rotation), "{}.input2Quat".format(swing))

    inv_swing = cmds.createNode("quatInvert", name="{}_inverse_swing".format(driver))
    cmds.connectAttr("{}.outputQuat".format(swing), "{}.inputQuat".format(inv_swing))

    # Connect the nodes to the driver so we can find and reuse them for multiple setups
    for node, attr in [
        (twist, TWIST_OUTPUT),
        (inv_twist, INV_TWIST_OUTPUT),
        (swing, SWING_OUTPUT),
        (inv_swing, INV_SWING_OUTPUT),
    ]:
        cmds.connectAttr("{}.message".format(node), "{}.{}".format(driver, attr))


def _get_swing_twist_attributes(driver):
    """Get the quaternion output attribute of the twist decomposition network.

    :param driver: Driver transform
    :param invert: True to get the inverted twist attribute
    :param twist_axis: Local twist axis of driver
    :return: The quaternion output attribute
    """
    nodes = []
    for attr in [TWIST_OUTPUT, INV_TWIST_OUTPUT, SWING_OUTPUT, INV_SWING_OUTPUT]:
        node = cmds.listConnections("{}.{}".format(driver, attr), d=False)
        if not node:
            # The network isn't connected so create it
            _create_twist_decomposition_network(driver, twist_axis)
            return _get_swing_twist_attributes(driver)
        nodes.append(node[0])

    return ["{}.outputQuat".format(node) for node in nodes]


def _create_slerp(driven, weight, rotation, inv_rotation, attribute):
    slerp = cmds.createNode("quatSlerp", name="{}_{}_slerp".format(driven, attribute))
    cmds.setAttr("{}.{}".format(driven, attribute), math.fabs(weight))
    cmds.connectAttr("{}.{}".format(driven, attribute), "{}.inputT".format(slerp))
    cmds.setAttr("{}.input1QuatW".format(slerp), 1)
    if weight >= 0.0:
        cmds.connectAttr(rotation, "{}.input2Quat".format(slerp))
    else:
        cmds.connectAttr(inv_rotation, "{}.input2Quat".format(slerp))
    return slerp


def create_from_menu(*args, **kwargs):
    sel = cmds.ls(sl=True)
    if len(sel) != 2:
        raise RuntimeError("Select driver transform then driven transform.")
    driver, driven = sel
    kwargs = Options.get_kwargs()
    create_twist_decomposition(driver, driven, **kwargs)


def display_menu_options(*args, **kwargs):
    options = Options("Twist Decomposition Options", HELP_URL)
    options.show()


class Options(OptionBox):
    INVERT_WIDGET = "cmt_twist_invert"
    TWIST_WEIGHT_WIDGET = "cmt_twist_weight"
    TWIST_AXIS_ENABLE_WIDGET = "cmt_twist_auto_axis"
    TWIST_AXIS_WIDGET = "cmt_twist_axis"

    @classmethod
    def get_kwargs(cls):
        """Gets the function arguments either from the option box widgets or the saved
        option vars.  If the widgets exist, their values will be saved to the option
        vars.

        :return: A dictionary of the arguments to the create_twist_decomposition
        function."""
        kwargs = {}
        if cmds.floatSliderGrp(Options.TWIST_WEIGHT_WIDGET, exists=True):
            kwargs["twist_weight"] = cmds.floatSliderGrp(
                Options.TWIST_WEIGHT_WIDGET, q=True, value=True
            )
            cmds.optionVar(fv=(Options.TWIST_WEIGHT_WIDGET, kwargs["twist_weight"]))
        else:
            kwargs["twist_weight"] = cmds.optionVar(q=Options.TWIST_WEIGHT_WIDGET)

        if cmds.checkBoxGrp(Options.INVERT_WIDGET, exists=True):
            value = cmds.checkBoxGrp(Options.INVERT_WIDGET, q=True, v1=True)
            kwargs["invert"] = value
            cmds.optionVar(iv=(Options.INVERT_WIDGET, value))
        else:
            value = cmds.optionVar(q=Options.INVERT_WIDGET)
            kwargs["invert"] = value

        if cmds.checkBoxGrp(Options.TWIST_AXIS_ENABLE_WIDGET, exists=True):
            value = cmds.checkBoxGrp(Options.TWIST_AXIS_ENABLE_WIDGET, q=True, v1=True)
            if value:
                x = cmds.floatFieldGrp(Options.TWIST_AXIS_WIDGET, q=True, v1=True)
                y = cmds.floatFieldGrp(Options.TWIST_AXIS_WIDGET, q=True, v2=True)
                z = cmds.floatFieldGrp(Options.TWIST_AXIS_WIDGET, q=True, v3=True)
                kwargs["twist_axis"] = (x, y, z)
            else:
                kwargs["twist_axis"] = None
            cmds.optionVar(clearArray=Options.TWIST_AXIS_WIDGET)
            if kwargs["twist_axis"]:
                for v in kwargs["twist_axis"]:
                    cmds.optionVar(floatValueAppend=[Options.TWIST_AXIS_WIDGET, v])
        else:
            kwargs["twist_axis"] = cmds.optionVar(q=Options.TWIST_AXIS_WIDGET)

        return kwargs

    def create_ui(self):
        cmds.columnLayout(adj=True)

        for widget in [
            Options.INVERT_WIDGET,
            Options.TWIST_WEIGHT_WIDGET,
            Options.TWIST_AXIS_ENABLE_WIDGET,
            Options.TWIST_AXIS_WIDGET,
        ]:
            # Delete the widgets so we don't create multiple controls with the same name
            try:
                cmds.deleteUI(widget, control=True)
            except RuntimeError:
                pass
        invert_twist = cmds.optionVar(q=Options.INVERT_WIDGET)
        cmds.checkBoxGrp(
            Options.INVERT_WIDGET,
            numberOfCheckBoxes=1,
            label="Invert twist",
            v1=invert_twist,
        )

        twist_weight = cmds.optionVar(q=Options.TWIST_WEIGHT_WIDGET)
        cmds.floatSliderGrp(
            Options.TWIST_WEIGHT_WIDGET,
            label="Twist weight",
            field=True,
            minValue=0.0,
            maxValue=1.0,
            fieldMinValue=0.0,
            fieldMaxValue=1.0,
            value=twist_weight,
            step=0.1,
            precision=2,
        )

        specify_twist_axis = cmds.optionVar(q=Options.TWIST_AXIS_ENABLE_WIDGET)
        cmds.checkBoxGrp(
            Options.TWIST_AXIS_ENABLE_WIDGET,
            numberOfCheckBoxes=1,
            label="Specify twist axis ",
            v1=specify_twist_axis,
            cc=self.on_axis_enable_changed,
        )

        twist_axis = cmds.optionVar(q=Options.TWIST_AXIS_WIDGET)
        twist_axis = twist_axis if twist_axis else (1, 0, 0)
        cmds.floatFieldGrp(
            Options.TWIST_AXIS_WIDGET,
            numberOfFields=3,
            label="Twist axis ",
            v1=twist_axis[0],
            v2=twist_axis[1],
            v3=twist_axis[2],
            enable=specify_twist_axis,
            precision=3,
        )

    def on_axis_enable_changed(self, value):
        cmds.floatFieldGrp(Options.TWIST_AXIS_WIDGET, e=True, enable=value)

    def on_apply(self):
        create_from_menu()

    def on_reset(self):
        cmds.floatSliderGrp(Options.TWIST_WEIGHT_WIDGET, e=True, value=1)
        cmds.checkBoxGrp(Options.INVERT_WIDGET, e=True, v1=True)
        cmds.checkBoxGrp(Options.TWIST_AXIS_ENABLE_WIDGET, e=True, v1=False)
        cmds.floatFieldGrp(Options.TWIST_AXIS_WIDGET, e=True, v1=1.0, v2=0.0, v3=0.0)

    def on_save(self):
        Options.get_kwargs()
