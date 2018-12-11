from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import maya.cmds as cmds
import cmt.rig.transformstack as ts
from cmt.test import TestCase


class TransformStackTests(TestCase):
    def setUp(self):
        self.leaf = cmds.createNode("transform", name="leaf")
        self.suffixes = ["_zero", "_offset", "_sdk"]

    def test_create_stack(self):
        stack = ts.create_transform_stack(self.leaf, self.suffixes)
        expected = ["leaf{}".format(x) for x in self.suffixes]
        expected.append(self.leaf)
        self.assertListEqual(stack, expected)
        for node in expected:
            self.assertTrue(cmds.objExists(node))

    def test_delete_stack(self):
        stack = ts.create_transform_stack(self.leaf, self.suffixes)
        ts.delete_stack(self.leaf)
        stack = stack[:-1]
        for node in stack:
            self.assertFalse(cmds.objExists(node))
        self.assertTrue(cmds.objExists(self.leaf))

    def test_get_stack(self):
        ts.create_transform_stack(self.leaf, self.suffixes)
        stack = ts.get_stack(self.leaf)
        expected = ["leaf{}".format(x) for x in self.suffixes]
        expected.append(self.leaf)
        self.assertListEqual(stack, expected)

    def test_get_stack_count(self):
        ts.create_transform_stack(self.leaf, self.suffixes)
        count = ts.get_stack_count(self.leaf)
        self.assertEqual(count, 4)

    def test_get_stack_parent(self):
        original_parent = cmds.createNode("transform", name="root")
        cmds.parent(self.leaf, original_parent)
        ts.create_transform_stack(self.leaf, self.suffixes)
        parent = ts.get_stack_parent(self.leaf)
        self.assertEqual(parent, original_parent)

    def test_get_stack_parent_world(self):
        ts.create_transform_stack(self.leaf, self.suffixes)
        parent = ts.get_stack_parent(self.leaf)
        self.assertIsNone(parent)
