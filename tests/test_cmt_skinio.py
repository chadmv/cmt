import unittest
import os
import maya.cmds as cmds
import cmt.deform.skinio as skinio

from cmt.test import TestCase


class SkinIOTests(TestCase):
    def setUp(self):
        self.joint1 = cmds.joint(p=(-0.5, -0.5, 0))
        self.joint2 = cmds.joint(p=(0, 0.0, 0))
        self.joint3 = cmds.joint(p=(0.5, 0.5, 0))
        self.shape = cmds.polyCube()[0]
        cmds.delete(self.shape, ch=True)
        self.skin = cmds.skinCluster(self.joint1, self.joint2, self.joint3, self.shape)[
            0
        ]
        self.expected = {
            "bindMethod": 1,
            "blendWeights": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "dropoffRate": 4.0,
            "heatmapFalloff": 0.0,
            "maintainMaxInfluences": False,
            "maxInfluences": 2,
            "name": u"skinCluster1",
            "normalizeWeights": 1,
            "shape": u"pCube1",
            "skinningMethod": 0,
            "useComponents": False,
            "weightDistribution": 0,
            "weights": {
                "joint1": [0.9, 0.5, 0.5, 0.0, 0.5, 0.0, 0.9, 0.5],
                "joint2": [
                    0.10000000000000002,
                    0.5,
                    0.5,
                    0.5,
                    0.5,
                    0.5,
                    0.10000000000000002,
                    0.5,
                ],
                "joint3": [0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0],
            },
        }

    def test_skincluster_data_is_correct(self):
        skin = skinio.SkinCluster(self.skin)
        data = skin.gather_data()
        attributes = [
            "skinningMethod",
            "normalizeWeights",
            "dropoffRate",
            "maintainMaxInfluences",
            "maxInfluences",
            "bindMethod",
            "useComponents",
            "normalizeWeights",
            "weightDistribution",
            "heatmapFalloff",
            "name",
            "shape",
        ]
        for attribute in attributes:
            self.assertEqual(self.expected[attribute], data[attribute])
        self.assertListAlmostEqual(self.expected["blendWeights"], data["blendWeights"])
        self.assertListAlmostEqual(
            self.expected["weights"]["joint1"], data["weights"]["joint1"]
        )
        self.assertListAlmostEqual(
            self.expected["weights"]["joint2"], data["weights"]["joint2"]
        )
        self.assertListAlmostEqual(
            self.expected["weights"]["joint3"], data["weights"]["joint3"]
        )

    def test_export_skin(self):
        file_path = self.get_temp_filename("temp.skin")
        skinio.export_skin(file_path, self.shape)
        self.assertTrue(os.path.exists(file_path))
        self.assertGreater(os.path.getsize(file_path), 0)

    def test_import_skin(self):
        file_path = self.get_temp_filename("temp.skin")
        skinio.export_skin(file_path, self.shape)
        cmds.delete(self.skin)
        skinio.import_skin(file_path)
        self.assertTrue(cmds.objExists(self.skin))

    def test_import_skin_sets_correct_data(self):
        file_path = self.get_temp_filename("temp.skin")
        skinio.export_skin(file_path, self.shape)
        cmds.skinPercent(
            self.skin,
            "{0}.vtx[0]".format(self.shape),
            transformValue=[(self.joint1, 0.1), (self.joint2, 0.2), (self.joint3, 0.7)],
        )
        skinio.import_skin(file_path)
        self.test_skincluster_data_is_correct()

    def test_import_skin_on_selected_subset(self):
        file_path = self.get_temp_filename("temp.skin")
        skinio.export_skin(file_path, self.shape)
        cmds.skinPercent(
            self.skin,
            "{0}.vtx[0]".format(self.shape),
            transformValue=[(self.joint1, 0.1), (self.joint2, 0.2), (self.joint3, 0.7)],
        )
        cmds.skinPercent(
            self.skin,
            "{0}.vtx[1]".format(self.shape),
            transformValue=[(self.joint1, 0.1), (self.joint2, 0.2), (self.joint3, 0.7)],
        )
        cmds.select("{}.vtx[1]".format(self.shape))
        skinio.import_skin(file_path, to_selected_shapes=True)

        skin = skinio.SkinCluster(self.skin)
        data = skin.gather_data()

        w1 = [0.1, 0.5, 0.5, 0.0, 0.5, 0.0, 0.9, 0.5]
        w2 = [0.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.1, 0.5]
        w3 = [0.7, 0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0]
        self.assertListAlmostEqual(w1, data["weights"]["joint1"])
        self.assertListAlmostEqual(w2, data["weights"]["joint2"])
        self.assertListAlmostEqual(w3, data["weights"]["joint3"])
