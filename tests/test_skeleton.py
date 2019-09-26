import maya.cmds as cmds
import cmt.rig.skeleton as skeleton
from cmt.test import TestCase


class SkeletonTests(TestCase):
    def setUp(self):
        self.group = cmds.createNode("transform", name="skeleton_grp")
        cmds.select(cl=True)
        j1 = cmds.joint(p=(0, 10, 0))
        cmds.joint(p=(1, 9, 0))
        cmds.joint(p=(2, 8, 0))
        j = cmds.joint(p=(3, 9, 0))
        cmds.joint(p=(4, 6, 0))
        cmds.joint(p=(5, 5, 0))
        cmds.joint(p=(6, 3, 0))
        self.cube = cmds.polyCube()[0]
        cmds.parent(self.cube, j)
        cmds.parent(j1, self.group)

        cmds.joint(j1, e=True, oj="xyz", secondaryAxisOrient="yup", ch=True, zso=True)
        self.translates = [
            cmds.getAttr("{0}.t".format(x))[0] for x in cmds.ls(type="joint")
        ]
        self.rotates = [
            cmds.getAttr("{0}.r".format(x))[0] for x in cmds.ls(type="joint")
        ]
        self.orients = [
            cmds.getAttr("{0}.jo".format(x))[0] for x in cmds.ls(type="joint")
        ]

    def test_get_and_rebuild_data(self):
        data = skeleton.dumps(self.group)
        cmds.file(new=True, f=True)
        skeleton.create(data)
        self.assert_hierarachies_match()

    def test_export_and_import_data(self):
        json_file = self.get_temp_filename("skeleton.json")
        skeleton.dump(self.group, json_file)
        cmds.file(new=True, f=True)
        skeleton.load(json_file)
        self.assert_hierarachies_match()

    def assert_hierarachies_match(self):
        self.assertEqual(7, len(cmds.ls(type="joint")))
        # Make sure the joint orients are the same
        translates = [cmds.getAttr("{0}.t".format(x))[0] for x in cmds.ls(type="joint")]
        rotates = [cmds.getAttr("{0}.r".format(x))[0] for x in cmds.ls(type="joint")]
        orients = [cmds.getAttr("{0}.jo".format(x))[0] for x in cmds.ls(type="joint")]
        for orient, new_orient in zip(self.orients, orients):
            self.assertListAlmostEqual(orient, new_orient)
        for translate, new_translate in zip(self.translates, translates):
            self.assertListAlmostEqual(translate, new_translate)
        for rotate, new_rotate in zip(self.rotates, rotates):
            self.assertListAlmostEqual(rotate, new_rotate)
        # The geometry should not have been exported
        self.assertFalse(cmds.objExists(self.cube))
        self.assertTrue(cmds.objExists(self.group))
        self.assertEqual("joint1", cmds.listRelatives(self.group, children=True)[0])
