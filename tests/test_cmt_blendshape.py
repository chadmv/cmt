import unittest
import os
import maya.cmds as cmds
import cmt.deform.blendshape as bs

from cmt.test import TestCase


class BlendShapeTests(TestCase):
    def test_get_blendshape_on_new_shape(self):
        shape = cmds.polyCube()[0]
        blendshape = bs.get_or_create_blendshape_node(shape)
        self.assertTrue(cmds.objExists(blendshape))
        blendshapes = cmds.ls(type="blendShape")
        self.assertEqual(len(blendshapes), 1)
        self.assertEqual(blendshapes[0], blendshape)

        blendshape = bs.get_or_create_blendshape_node(shape)
        blendshapes = cmds.ls(type="blendShape")
        self.assertEqual(len(blendshapes), 1)
        self.assertEqual(blendshapes[0], blendshape)

    def test_get_blendshape_on_existing_blendshape(self):
        shape = cmds.polyCube()[0]
        blendshape = cmds.blendShape(shape)[0]
        existing_blendshape = bs.get_or_create_blendshape_node(shape)
        self.assertEqual(blendshape, existing_blendshape)
