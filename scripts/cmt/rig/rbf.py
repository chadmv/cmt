import maya.cmds as cmds


class RBF(object):
    @classmethod
    def create(cls, name=None, inputs=None, outputs=None, input_transforms=None, add_neutral_sample=True):
        cmds.loadPlugin("cmt", qt=True)
        name = name or "rbf#"
        node = cmds.createNode("rbf", name=name)
        node = RBF(node)
        if add_neutral_sample:
            # Store the current output values because they may be different once
            # connected
            output_values = [cmds.getAttr(x) for x in outputs] if outputs else None

        node.set_inputs(inputs)
        node.set_outputs(outputs)
        node.set_input_transforms(input_transforms)

        if add_neutral_sample:
            node.add_sample(output_values=output_values)

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
            # Connect the local rotation quaternion into the rbf
            # Since we want to be able import the rbf data outside of Maya,
            # We want the local rotation to take into account joint orient or
            # offsetParentMatrix
            mult = cmds.createNode(
                "multMatrix", name="{}_local_matrix".format(transform)
            )
            world_matrix = "{}.worldMatrix[0]".format(transform)
            cmds.connectAttr(world_matrix, "{}.matrixIn[0]".format(mult))
            parent = cmds.listRelatives(transform, parent=True, path=True)
            if parent:
                parent_inverse = "{}.worldInverseMatrix[0]".format(parent[0])
                cmds.connectAttr(parent_inverse, "{}.matrixIn[1]".format(mult))

            rotation = cmds.createNode(
                "decomposeMatrix", name="{}_rotation".format(transform)
            )
            cmds.connectAttr(
                "{}.matrixSum".format(mult), "{}.inputMatrix".format(rotation)
            )
            cmds.connectAttr(
                "{}.outputQuat".format(rotation),
                "{}.inputQuat[{}]".format(self.name, i),
            )
        cmds.setAttr("{}.inputQuatCount".format(self.name), len(input_transforms))
        # TODO: Reshuffle samples if inputs are being re-used

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
        # inputQuat <- decomposeMatrix <- multMatrix <- transform
        connection = cmds.listConnections(
            "{}.inputQuat[{}]".format(self.name, i), d=False
        )

        if not connection or cmds.nodeType(connection[0]) != "decomposeMatrix":
            return None
        connection = cmds.listConnections(
            "{}.inputMatrix".format(connection[0]), d=False
        )
        if not connection or cmds.nodeType(connection[0]) != "multMatrix":
            return None
        connection = cmds.listConnections(
            "{}.matrixIn[0]".format(connection[0]), d=False
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
            cmds.connectAttr("{}.outputValue[{}]".format(self.name, i), attribute)
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

    def add_sample(self, input_values=None, output_values=None, input_quats=None):
        """Add a new sample with the given values

        :param input_values: Optional list of input values
        :param output_values: Optional list of output values
        :param input_quats: Optional list of quaternion values:
            [[x, y, z, w], [x, y, z, w]]
        :return: The sample index
        """
        if input_values is None:
            # Use existing values
            input_values = [cmds.getAttr(x) for x in self.inputs()]

        if output_values is None:
            # Use existing values
            output_values = [cmds.getAttr(x) for x in self.outputs()]

        if input_quats is None:
            # Use existing values
            input_quat_count = cmds.getAttr("{}.inputQuatCount".format(self.name))
            input_quats = [
                cmds.getAttr("{}.inputQuat[{}]".format(self.name, i))[0]
                for i in range(input_quat_count)
            ]

        if input_values:
            print("Input values: {}".format(input_values))
        if output_values:
            print("Output values: {}".format(output_values))
        if input_quats:
            print("Input quats: {}".format(input_quats))

        indices = cmds.getAttr("{}.sample".format(self.name), mi=True)
        idx = indices[-1] + 1 if indices else 0
        for i, v in enumerate(input_values):
            cmds.setAttr(
                "{}.sample[{}].sampleInputValue[{}]".format(self.name, idx, i), v
            )
        for i, v in enumerate(output_values):
            cmds.setAttr(
                "{}.sample[{}].sampleOutputValue[{}]".format(self.name, idx, i), v
            )
        for i, v in enumerate(input_quats):
            cmds.setAttr(
                "{}.sample[{}].sampleInputQuat[{}]".format(self.name, idx, i),
                *v,
                type="double4"
            )

        return idx

    def remove_sample(self, i):
        """Remove the sample at index i

        :param i: Index
        """
        indices = cmds.getAttr("{}.sample".format(self.name), mi=True) or []
        if i not in indices:
            raise RuntimeError("Sample {} does not exist.".format(i))
        cmds.removeMultiInstance("{}.sample[{}]".format(self.name, i), all=True, b=True)
