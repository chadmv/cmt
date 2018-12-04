"""SwingTwist is a dependency graph node that decomposes the local rotation of a transform to drive the rotation of
another transform allowing the user to scale the swing and twist components of the local rotation.

To create the node, select the driver, then the driven and run cmds.swingTwist(name='swingTwistNodeName')

node = cmds.swingTwist(driver, driven, name='nodeName')
"""

import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
import math


def slerp(qa, qb, t):
    """Calculates the quaternion slerp between two quaternions.

    From: http://www.euclideanspace.com/maths/algebra/realNormedAlgebra/quaternions/slerp/index.htm

    :param qa: Start MQuaternion.
    :param qb: End MQuaternion.
    :param t: Parameter between 0.0 and 1.0
    :return: An MQuaternion interpolated between qa and qb.
    """
    qm = OpenMaya.MQuaternion()

    # Calculate angle between them.
    cos_half_theta = qa.w * qb.w + qa.x * qb.x + qa.y * qb.y + qa.z * qb.z
    # if qa == qb or qa == -qb then theta = 0 and we can return qa
    if abs(cos_half_theta) >= 1.0:
        qm.w = qa.w
        qm.x = qa.x
        qm.y = qa.y
        qm.z = qa.z
        return qa

    # Calculate temporary values
    half_theta = math.acos(cos_half_theta)
    sin_half_theta = math.sqrt(1.0 - cos_half_theta * cos_half_theta)
    # if theta = 180 degrees then result is not fully defined
    # we could rotate around any axis normal to qa or qb
    if math.fabs(sin_half_theta) < 0.001:
        qm.w = qa.w * 0.5 + qb.w * 0.5
        qm.x = qa.x * 0.5 + qb.x * 0.5
        qm.y = qa.y * 0.5 + qb.y * 0.5
        qm.z = qa.z * 0.5 + qb.z * 0.5
        return qm

    ratio_a = math.sin((1 - t) * half_theta) / sin_half_theta
    ratio_b = math.sin(t * half_theta) / sin_half_theta
    # Calculate quaternion
    qm.w = qa.w * ratio_a + qb.w * ratio_b
    qm.x = qa.x * ratio_a + qb.x * ratio_b
    qm.y = qa.y * ratio_a + qb.y * ratio_b
    qm.z = qa.z * ratio_a + qb.z * ratio_b
    return qm


class SwingTwistNode(OpenMayaMPx.MPxNode):
    id = OpenMaya.MTypeId(0x00115817)
    name = "swingTwist"

    output_rotation = OpenMaya.MObject()
    output_rotation_x = OpenMaya.MObject()
    output_rotation_y = OpenMaya.MObject()
    output_rotation_z = OpenMaya.MObject()
    matrix = OpenMaya.MObject()
    twist_weight = OpenMaya.MObject()
    swing_weight = OpenMaya.MObject()
    twist_axis = OpenMaya.MObject()
    rotate_axis = OpenMaya.MObject()
    rotate_axis_x = OpenMaya.MObject()
    rotate_axis_y = OpenMaya.MObject()
    rotate_axis_z = OpenMaya.MObject()
    joint_orient = OpenMaya.MObject()
    joint_orient_x = OpenMaya.MObject()
    joint_orient_y = OpenMaya.MObject()
    joint_orient_z = OpenMaya.MObject()
    rotate_order = OpenMaya.MObject()

    @classmethod
    def creator(cls):
        return OpenMayaMPx.asMPxPtr(cls())

    @classmethod
    def initialize(cls):
        e_attr = OpenMaya.MFnEnumAttribute()
        m_attr = OpenMaya.MFnMatrixAttribute()
        n_attr = OpenMaya.MFnNumericAttribute()
        u_attr = OpenMaya.MFnUnitAttribute()

        cls.output_rotation_x = u_attr.create(
            "outRotateX", "outRotateX", OpenMaya.MFnUnitAttribute.kAngle
        )
        u_attr.setWritable(False)
        u_attr.setStorable(False)

        cls.output_rotation_y = u_attr.create(
            "outRotateY", "outRotateY", OpenMaya.MFnUnitAttribute.kAngle
        )
        u_attr.setWritable(False)
        u_attr.setStorable(False)

        cls.output_rotation_z = u_attr.create(
            "outRotateZ", "outRotateZ", OpenMaya.MFnUnitAttribute.kAngle
        )
        u_attr.setWritable(False)
        u_attr.setStorable(False)

        cls.output_rotation = n_attr.create(
            "outRotate",
            "outRotate",
            cls.output_rotation_x,
            cls.output_rotation_y,
            cls.output_rotation_z,
        )
        n_attr.setWritable(False)
        n_attr.setStorable(False)
        cls.addAttribute(cls.output_rotation)

        cls.twist_weight = n_attr.create(
            "twist", "twist", OpenMaya.MFnNumericData.kFloat, 1.0
        )
        n_attr.setKeyable(True)
        n_attr.setMin(-1.0)
        n_attr.setMax(1.0)
        cls.addAttribute(cls.twist_weight)
        cls.attribute_affects(cls.twist_weight)

        cls.swing_weight = n_attr.create(
            "swing", "swing", OpenMaya.MFnNumericData.kFloat, 1.0
        )
        n_attr.setKeyable(True)
        n_attr.setMin(-1.0)
        n_attr.setMax(1.0)
        cls.addAttribute(cls.swing_weight)
        cls.attribute_affects(cls.swing_weight)

        cls.twist_axis = e_attr.create("twistAxis", "twistAxis")
        e_attr.setKeyable(True)
        e_attr.addField("X Axis", 0)
        e_attr.addField("Y Axis", 1)
        e_attr.addField("Z Axis", 2)
        cls.addAttribute(cls.twist_axis)
        cls.attribute_affects(cls.twist_axis)

        cls.matrix = m_attr.create("matrix", "matrix")
        cls.addAttribute(cls.matrix)
        cls.attribute_affects(cls.matrix)

        cls.joint_orient_x = u_attr.create(
            "jointOrientX", "jointOrientX", OpenMaya.MFnUnitAttribute.kAngle
        )
        cls.joint_orient_y = u_attr.create(
            "jointOrientY", "jointOrientY", OpenMaya.MFnUnitAttribute.kAngle
        )
        cls.joint_orient_z = u_attr.create(
            "jointOrientZ", "jointOrientZ", OpenMaya.MFnUnitAttribute.kAngle
        )
        cls.joint_orient = n_attr.create(
            "jointOrient",
            "jointOrient",
            cls.joint_orient_x,
            cls.joint_orient_y,
            cls.joint_orient_z,
        )
        cls.addAttribute(cls.joint_orient)
        cls.attribute_affects(cls.joint_orient)

        cls.rotate_axis_x = u_attr.create(
            "rotateAxisX", "rotateAxisX", OpenMaya.MFnUnitAttribute.kAngle
        )
        cls.rotate_axis_y = u_attr.create(
            "rotateAxisY", "rotateAxisY", OpenMaya.MFnUnitAttribute.kAngle
        )
        cls.rotate_axis_z = u_attr.create(
            "rotateAxisZ", "rotateAxisZ", OpenMaya.MFnUnitAttribute.kAngle
        )
        cls.rotate_axis = n_attr.create(
            "rotateAxis",
            "rotateAxis",
            cls.rotate_axis_x,
            cls.rotate_axis_y,
            cls.rotate_axis_z,
        )
        cls.addAttribute(cls.rotate_axis)
        cls.attribute_affects(cls.rotate_axis)

        cls.rotate_order = e_attr.create("rotateOrder", "rotateOrder")
        e_attr.addField("XYZ", 0)
        e_attr.addField("YZX", 1)
        e_attr.addField("ZXY", 2)
        e_attr.addField("XZY", 3)
        e_attr.addField("YXZ", 4)
        e_attr.addField("ZYX", 5)
        cls.addAttribute(cls.rotate_order)
        cls.attribute_affects(cls.rotate_order)

    @classmethod
    def attribute_affects(cls, attribute):
        cls.attributeAffects(attribute, cls.output_rotation_x)
        cls.attributeAffects(attribute, cls.output_rotation_y)
        cls.attributeAffects(attribute, cls.output_rotation_z)
        cls.attributeAffects(attribute, cls.output_rotation)

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, data):
        if plug != self.output_rotation and plug.parent() != self.output_rotation:
            return OpenMaya.kUnknownParameter

        # Get the input data
        matrix = data.inputValue(self.matrix).asMatrix()
        twist_weight = data.inputValue(self.twist_weight).asFloat()
        swing_weight = data.inputValue(self.swing_weight).asFloat()
        twist_axis = data.inputValue(self.twist_axis).asShort()
        rotate_order = data.inputValue(self.rotate_order).asShort()
        h_joint_orient = data.inputValue(self.joint_orient)
        h_rotate_axis = data.inputValue(self.rotate_axis)
        joint_orient = [
            h_joint_orient.child(x).asAngle().asDegrees()
            for x in [self.joint_orient_x, self.joint_orient_y, self.joint_orient_z]
        ]
        rotate_axis = [
            h_rotate_axis.child(x).asAngle().asDegrees()
            for x in [self.rotate_axis_x, self.rotate_axis_y, self.rotate_axis_z]
        ]

        # Get the input rotation quaternion
        rotation = OpenMaya.MTransformationMatrix(matrix).rotation()

        # Take out the joint orient and rotate axis from the rotation quaternion
        joint_orient = [math.radians(x) for x in joint_orient]
        joint_orient = OpenMaya.MEulerRotation(
            joint_orient[0], joint_orient[1], joint_orient[2]
        )
        joint_orient = joint_orient.asQuaternion()

        rotate_axis = [math.radians(x) for x in rotate_axis]
        rotate_axis = OpenMaya.MEulerRotation(
            rotate_axis[0], rotate_axis[1], rotate_axis[2]
        )
        rotate_axis = rotate_axis.asQuaternion()

        rotation = rotate_axis.inverse() * rotation * joint_orient.inverse()
        rotation_matrix = rotation.asMatrix()

        # Calculate swing
        target_vector = [
            OpenMaya.MVector(
                rotation_matrix(x, 0), rotation_matrix(x, 1), rotation_matrix(x, 2)
            )
            for x in range(3)
        ][twist_axis]
        reference_vector = [
            OpenMaya.MVector.xAxis,
            OpenMaya.MVector.yAxis,
            OpenMaya.MVector.zAxis,
        ][twist_axis]
        swing = reference_vector.rotateTo(target_vector)

        twist = rotation * swing.inverse()
        twist_matrix = twist.asMatrix()
        # Calculate twist
        target_vector = [
            OpenMaya.MVector(twist_matrix(x, 0), twist_matrix(x, 1), twist_matrix(x, 2))
            for x in [1, 2, 0]
        ][twist_axis]
        reference_vector = [
            OpenMaya.MVector.yAxis,
            OpenMaya.MVector.zAxis,
            OpenMaya.MVector.xAxis,
        ][twist_axis]
        twist = reference_vector.rotateTo(target_vector)

        # Scale by the input weights
        rest = OpenMaya.MQuaternion()
        swing = slerp(rest, swing, abs(swing_weight))
        twist = slerp(rest, twist, abs(twist_weight))

        # Process any inversion
        if twist_weight < 0.0:
            twist.invertIt()
        if swing_weight < 0.0:
            swing.invertIt()

        # Get the output rotation order
        rotation_order = [
            OpenMaya.MEulerRotation.kXYZ,
            OpenMaya.MEulerRotation.kYZX,
            OpenMaya.MEulerRotation.kZXY,
            OpenMaya.MEulerRotation.kXZY,
            OpenMaya.MEulerRotation.kYXZ,
            OpenMaya.MEulerRotation.kZYX,
        ][rotate_order]

        out_rotation = twist * swing
        # Convert the rotation to euler
        euler = out_rotation.asEulerRotation()
        euler.reorderIt(rotation_order)
        rx = math.degrees(euler.x)
        ry = math.degrees(euler.y)
        rz = math.degrees(euler.z)

        # Set the output
        h_out = data.outputValue(self.output_rotation)
        for rot, attr in zip(
            [rx, ry, rz],
            [self.output_rotation_x, self.output_rotation_y, self.output_rotation_z],
        ):
            angle = OpenMaya.MAngle(rot, OpenMaya.MAngle.kDegrees)
            handle = h_out.child(attr)
            handle.setMAngle(angle)
            handle.setClean()

        h_out.setClean()
        data.setClean(plug)


class SwingTwistCommand(OpenMayaMPx.MPxCommand):
    """The command used to create swingTwist nodes."""

    name_flag_short = "-n"
    name_flag_long = "-name"
    swing_flag_short = "-s"
    swing_flag_long = "-swing"
    twist_flag_short = "-t"
    twist_flag_long = "-twist"
    twistaxis_flag_short = "-ta"
    twistaxis_flag_long = "-twistAxis"
    name = "swingTwist"

    @classmethod
    def command_syntax(cls):
        syntax = OpenMaya.MSyntax()
        syntax.addFlag(
            cls.name_flag_short, cls.name_flag_long, OpenMaya.MSyntax.kString
        )
        syntax.addFlag(
            cls.swing_flag_short, cls.swing_flag_long, OpenMaya.MSyntax.kDouble
        )
        syntax.addFlag(
            cls.twist_flag_short, cls.twist_flag_long, OpenMaya.MSyntax.kDouble
        )
        syntax.addFlag(
            cls.twistaxis_flag_short, cls.twistaxis_flag_long, OpenMaya.MSyntax.kLong
        )
        syntax.setObjectType(OpenMaya.MSyntax.kSelectionList, 2, 2)
        syntax.useSelectionAsDefault(True)
        syntax.enableEdit(False)
        syntax.enableQuery(False)
        return syntax

    @classmethod
    def creator(cls):
        return OpenMayaMPx.asMPxPtr(SwingTwistCommand())

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
        self._name = ""
        self._node_mobject = OpenMaya.MObject()
        self._dgmod = OpenMaya.MDGModifier()

    def isUndoable(self):
        return True

    def doIt(self, arg_list):
        # Read all the flag arguments
        arg_data = OpenMaya.MArgDatabase(self.syntax(), arg_list)

        selection = OpenMaya.MSelectionList()
        arg_data.getObjects(selection)

        # Get the name
        if arg_data.isFlagSet(self.name_flag_short):
            self._name = arg_data.flagArgumentString(self.name_flag_short, 0)
        self._node_mobject = self._dgmod.createNode(SwingTwistNode.id)

        path_driver = OpenMaya.MDagPath()
        path_driven = OpenMaya.MDagPath()
        selection.getDagPath(0, path_driver)
        selection.getDagPath(1, path_driven)

        fn_node = OpenMaya.MFnDependencyNode(self._node_mobject)
        fn_driver = OpenMaya.MFnDagNode(path_driver)
        fn_driven = OpenMaya.MFnDagNode(path_driven)

        # Set the swing weight
        swing = (
            arg_data.flagArgumentDouble(self.swing_flag_short, 0)
            if arg_data.isFlagSet(self.swing_flag_short)
            else 1.0
        )
        plug_swing = fn_node.findPlug(SwingTwistNode.swing_weight, False)
        self._dgmod.newPlugValueFloat(plug_swing, swing)

        # Set the twist weight
        twist = (
            arg_data.flagArgumentDouble(self.twist_flag_short, 0)
            if arg_data.isFlagSet(self.twist_flag_short)
            else 1.0
        )
        plug_twist = fn_node.findPlug(SwingTwistNode.twist_weight, False)
        self._dgmod.newPlugValueFloat(plug_twist, twist)

        # Set the twist axis
        twist_axis = (
            arg_data.flagArgumentInt(self.twistaxis_flag_short, 0)
            if arg_data.isFlagSet(self.twistaxis_flag_short)
            else 0
        )
        plug_twist_axis = fn_node.findPlug(SwingTwistNode.twist_axis, False)
        self._dgmod.newPlugValueShort(plug_twist_axis, twist_axis)

        # Connect the matrix
        plug_in_matrix = fn_node.findPlug(SwingTwistNode.matrix, False)
        plug_matrix = fn_driver.findPlug("matrix", False)
        self._dgmod.connect(plug_matrix, plug_in_matrix)

        # Connect the rotateAxis
        plug_in_rotate_axis = fn_node.findPlug(SwingTwistNode.rotate_axis, False)
        plug_rotate_axis = fn_driver.findPlug("rotateAxis", False)
        self._dgmod.connect(plug_rotate_axis, plug_in_rotate_axis)

        # Connect the jointOrient
        if path_driver.hasFn(OpenMaya.MFn.kJoint):
            plug_in_joint_orient = fn_node.findPlug(SwingTwistNode.joint_orient, False)
            plug_joint_orient = fn_driver.findPlug("jointOrient", False)
            self._dgmod.connect(plug_joint_orient, plug_in_joint_orient)

        # Connect the rotate order
        plug_in_rotate_order = fn_node.findPlug(SwingTwistNode.rotate_order, False)
        plug_rotate_order = fn_driven.findPlug("rotateOrder", False)
        self._dgmod.connect(plug_rotate_order, plug_in_rotate_order)

        # Connect the output
        plug_output_rotate = fn_node.findPlug(SwingTwistNode.output_rotation, False)
        plug_rotate = fn_driven.findPlug("rotate", False)
        # Make sure the rotate isn't already connected
        connected_plugs = OpenMaya.MPlugArray()
        plug_rotate.connectedTo(connected_plugs, True, False)
        if connected_plugs.length():
            raise RuntimeError(
                "Cannot create swingTwist because {0} already has incoming connections.".format(
                    plug_rotate.name()
                )
            )
        self._dgmod.connect(plug_output_rotate, plug_rotate)
        return self.redoIt()

    def redoIt(self):
        self.clearResult()
        self._dgmod.doIt()
        fn_node = OpenMaya.MFnDependencyNode(self._node_mobject)
        if self._name and self._name != "swingTwist#":
            name = fn_node.setName(self._name)
        else:
            name = fn_node.name()
        self.setResult(name)

    def undoIt(self):
        self._dgmod.undoIt()
