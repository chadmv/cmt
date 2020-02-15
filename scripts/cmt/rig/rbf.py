import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import math


class RBF(object):
    swing = 0
    twist = 1
    swing_twist = 2

    @classmethod
    def create(
        cls,
        name=None,
        inputs=None,
        outputs=None,
        input_transforms=None,
        output_transforms=None,
        add_neutral_sample=True,
    ):
        cmds.loadPlugin("cmt", qt=True)
        name = name or "rbf#"
        node = cmds.createNode("rbf", name=name)
        node = RBF(node)
        if add_neutral_sample:
            # Store the current output values because they may be different once
            # connected
            output_values = [cmds.getAttr(x) for x in outputs] if outputs else None
            output_rotations = (
                [cmds.getAttr("{}.r".format(x))[0] for x in output_transforms]
                if output_transforms
                else None
            )

        node.set_inputs(inputs)
        node.set_outputs(outputs)
        node.set_input_transforms(input_transforms)
        node.set_output_transforms(output_transforms)

        if add_neutral_sample:
            for i in range(3):
                node.add_sample(
                    output_values=output_values,
                    output_rotations=output_rotations,
                    rotation_type=i,
                )

        return node

    def __init__(self, name):
        self.name = name

    def set_inputs(self, inputs):
        """Set the rbf inputs to the given list of attributes.

        :param inputs: List of attributes
        """
        current_inputs = self.inputs()
        # Disconnect existing inputs
        for i, attribute in enumerate(current_inputs):
            cmds.disconnectAttr(attribute, "{}.inputValue[{}]".format(self.name, i))

        if not inputs:
            cmds.setAttr("{}.inputValueCount".format(self.name), 0)
            return
        for i, attribute in enumerate(inputs):
            cmds.connectAttr(attribute, "{}.inputValue[{}]".format(self.name, i))
        cmds.setAttr("{}.inputValueCount".format(self.name), len(inputs))
        # TODO: Reshuffle samples if inputs are being re-used

    def inputs(self):
        """Get a list of the inputs to the rbf node"""
        indices = cmds.getAttr("{}.inputValue".format(self.name), mi=True) or []
        return [self.input(i) for i in indices]

    def input(self, i):
        """Get the input at index

        :param i: Index
        :return: The attribute connected to the input at index i
        """
        input_count = cmds.getAttr("{}.inputValueCount".format(self.name))
        if i >= input_count:
            raise RuntimeError("Invalid input index")
        connection = cmds.listConnections(
            "{}.inputValue[{}]".format(self.name, i), d=False, plugs=True
        )
        return connection[0] if connection else None

    def set_input_transforms(self, input_transforms):
        current_input_transforms = self.input_transforms()
        # Disconnect existing input transforms
        for i, attribute in enumerate(current_input_transforms):
            cmds.disconnectAttr(attribute, "{}.inputQuat[{}]".format(self.name, i))

        if not input_transforms:
            cmds.setAttr("{}.inputQuatCount".format(self.name), 0)
            return
        for i, transform in enumerate(input_transforms):
            rotation = cmds.createNode(
                "decomposeMatrix", name="{}_rotation".format(transform)
            )
            cmds.connectAttr(
                "{}.matrix".format(transform), "{}.inputMatrix".format(rotation)
            )
            cmds.connectAttr(
                "{}.outputQuat".format(rotation),
                "{}.inputQuat[{}]".format(self.name, i),
            )
            q = cmds.getAttr("{}.outputQuat".format(rotation))[0]
            cmds.setAttr(
                "{}.inputRestQuat[{}]".format(self.name, i), *q, type="double4"
            )
        cmds.setAttr("{}.inputQuatCount".format(self.name), len(input_transforms))
        # TODO: Reshuffle samples if inputs are being re-used

    def set_output_transforms(self, output_transforms):
        current_output_transforms = self.output_transforms()
        # Disconnect existing transforms
        for i, node in enumerate(current_output_transforms):
            cmds.disconnectAttr(
                "{}.outputRotate[{}]".format(self.name, i), "{}.r".format(node)
            )

        if not output_transforms:
            cmds.setAttr("{}.outputQuatCount".format(self.name), 0)
            return
        for i, node in enumerate(output_transforms):
            cmds.connectAttr(
                "{}.outputRotate[{}]".format(self.name, i), "{}.r".format(node)
            )
        cmds.setAttr("{}.outputQuatCount".format(self.name), len(output_transforms))

    def input_transforms(self):
        """Get a list of the input transforms to the rbf node"""
        indices = cmds.getAttr("{}.inputQuat".format(self.name), mi=True) or []
        return [self.input_transform(i) for i in indices]

    def input_transform(self, i):
        """Get the input transform at index

        :param i: Index
        :return: The transform driving the input at index i
        """
        input_count = cmds.getAttr("{}.inputQuatCount".format(self.name))
        if i >= input_count:
            raise RuntimeError("Invalid input index")
        # Traverse connections to the transform
        # inputQuat <- decomposeMatrix <- transform
        connection = cmds.listConnections(
            "{}.inputQuat[{}]".format(self.name, i), d=False
        )

        if not connection or cmds.nodeType(connection[0]) != "decomposeMatrix":
            return None
        connection = cmds.listConnections(
            "{}.inputMatrix".format(connection[0]), d=False
        )
        return connection[0] if connection else None

    def output_transforms(self):
        """Get a list of the input transforms to the rbf node"""
        indices = cmds.getAttr("{}.outputRotate".format(self.name), mi=True) or []
        return [self.output_transform(i) for i in indices]

    def output_transform(self, i):
        """Get the output transform at index

        :param i: Index
        :return: The transform driven by the output at index i
        """
        output_count = cmds.getAttr("{}.outputQuatCount".format(self.name))
        if i >= output_count:
            raise RuntimeError("Invalid output index")
        connection = cmds.listConnections(
            "{}.outputRotate[{}]".format(self.name, i), s=False
        )
        return connection[0] if connection else None

    def set_outputs(self, outputs):
        current_outputs = self.outputs()
        # Disconnect existing outputs
        for i, attribute in enumerate(current_outputs):
            cmds.disconnectAttr("{}.outputValue[{}]".format(self.name, i), attribute)

        if not outputs:
            cmds.setAttr("{}.outputValueCount".format(self.name), 0)
            return
        for i, attribute in enumerate(outputs):
            cmds.connectAttr(
                "{}.outputValue[{}]".format(self.name, i), attribute, f=True
            )
        cmds.setAttr("{}.outputValueCount".format(self.name), len(outputs))
        # TODO: Reshuffle samples if outputs are being re-used

    def outputs(self):
        """Get a list of the outputs to the rbf node"""
        indices = cmds.getAttr("{}.outputValue".format(self.name), mi=True) or []
        return [self.output(i) for i in indices]

    def output(self, i):
        """Get the output at index

        :param i: Index
        :return: The attribute connected to the output at index i
        """
        output_count = cmds.getAttr("{}.outputValueCount".format(self.name))
        if i >= output_count:
            raise RuntimeError("Invalid output index")
        connection = cmds.listConnections(
            "{}.outputValue[{}]".format(self.name, i), s=False, plugs=True
        )
        return connection[0] if connection else None

    def add_sample(
        self,
        input_values=None,
        output_values=None,
        input_rotations=None,
        output_rotations=None,
        rotation_type=swing,
    ):
        """Add a new sample with the given values

        :param input_values: Optional list of input values
        :param output_values: Optional list of output values
        :param input_rotations: Optional list of input rotations:
            [[rx, ry, rz], [rx, ry, rz]]
        :param output_rotations: Optional list of output rotations:
            [[rx, ry, rz], [rx, ry, rz]]
        :return: The sample index
        """
        if input_values is None:
            # Use existing values
            input_values = [cmds.getAttr(x) for x in self.inputs()]

        input_transforms = self.input_transforms()
        if input_rotations is None:
            input_rotations = [
                cmds.getAttr("{}.r".format(x))[0] for x in input_transforms
            ]

        # Convert euler to quat
        input_rotations = euler_to_quat(input_rotations, input_transforms)

        # See if a sample with these inputs already exists
        if self._sample_already_exists(input_values, input_rotations, rotation_type):
            print("Existing sample already exists. Skipping.")
            return None

        if output_values is None:
            # Use existing values
            output_values = [cmds.getAttr(x) for x in self.outputs()]

        output_transforms = self.output_transforms()
        if output_rotations is None:
            # Use existing values
            output_rotations = [
                cmds.getAttr("{}.r".format(x))[0] for x in output_transforms
            ]
        output_rotations = euler_to_quat(output_rotations, output_transforms)

        indices = cmds.getAttr("{}.sample".format(self.name), mi=True) or []
        idx = indices[-1] + 1 if indices else 0
        cmds.setAttr("{}.sample[{}].rotationType".format(self.name, idx), rotation_type)
        for i, v in enumerate(input_values):
            cmds.setAttr(
                "{}.sample[{}].sampleInputValue[{}]".format(self.name, idx, i), v
            )
        for i, v in enumerate(output_values):
            cmds.setAttr(
                "{}.sample[{}].sampleOutputValue[{}]".format(self.name, idx, i), v
            )
        for i, v in enumerate(input_rotations):
            cmds.setAttr(
                "{}.sample[{}].sampleInputQuat[{}]".format(self.name, idx, i),
                *v,
                type="double4"
            )
        for i, v in enumerate(output_rotations):
            cmds.setAttr(
                "{}.sample[{}].sampleOutputQuat[{}]".format(self.name, idx, i),
                *v,
                type="double4"
            )

        return idx

    def _sample_already_exists(self, input_values, input_rotations, rotation_type):
        """Check if a sample with the given inputs already exists.

        :param input_values: List of float values.
        :param input_rotations: List of 4-tuples representing quaternions
        :param rotation_type:
        :return: True if the sample already exists.
        """
        indices = cmds.getAttr("{}.sample".format(self.name), mi=True) or []
        if not indices:
            return False
        threshold = 0.0001
        for idx in indices:
            rt = cmds.getAttr("{}.sample[{}].rotationType".format(self.name, idx))
            if rotation_type != rt:
                continue
            sample_is_same = True
            for i, v1 in enumerate(input_values):
                v2 = cmds.getAttr(
                    "{}.sample[{}].sampleInputValue[{}]".format(self.name, idx, i)
                )
                if math.fabs(v1 - v2) > threshold:
                    sample_is_same = False
                    break

            for i, v1 in enumerate(input_rotations):
                v2 = cmds.getAttr(
                    "{}.sample[{}].sampleInputQuat[{}]".format(self.name, idx, i)
                )[0]
                q1 = OpenMaya.MQuaternion(*v1)
                q2 = OpenMaya.MQuaternion(*v2)
                d = quaternion_distance(q1, q2)

                if d > threshold:
                    sample_is_same = False
                    break
            if sample_is_same:
                return True
        return False

    def remove_sample(self, i):
        """Remove the sample at index i

        :param i: Index
        """
        indices = cmds.getAttr("{}.sample".format(self.name), mi=True) or []
        if i not in indices:
            raise RuntimeError("Sample {} does not exist.".format(i))
        cmds.removeMultiInstance("{}.sample[{}]".format(self.name, i), all=True, b=True)


def quaternion_distance(q1, q2):
    dot = quaternion_dot(q1, q2)
    return math.acos(2.0 * dot * dot - 1.0) / math.pi


def quaternion_dot(q1, q2):
    value = (q1.x * q2.x) + (q1.y * q2.y) + (q1.z * q2.z) + (q1.w * q2.w)
    # Clamp any floating point error
    if value < -1.0:
        value = -1.0
    elif value > 1.0:
        value = 1.0
    return value


def euler_to_quat(eulers, transforms):
    """Convert a list of eulers to quaternions

    :param eulers: List of tuples or lists of length 3
    :param transforms: List of transforms per rotation
    :return: List of quaternions
    """
    quats = []
    for i, v in enumerate(eulers):
        rotate_order = cmds.getAttr("{}.ro".format(transforms[i]))
        r = [math.radians(x) for x in v]
        euler = OpenMaya.MEulerRotation(r[0], r[1], r[2], rotate_order)
        q = euler.asQuaternion()
        if cmds.nodeType(transforms[i]) == "joint":
            jo = cmds.getAttr("{}.jo".format(transforms[i]))[0]
            jo = [math.radians(x) for x in jo]
            jo = OpenMaya.MEulerRotation(jo[0], jo[1], jo[2])
            q *= jo.asQuaternion()
        quats.append([q.x, q.y, q.z, q.w])
    return quats
