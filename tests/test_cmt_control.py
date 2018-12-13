import json
import os
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import cmt.rig.control as control
import cmt.shortcuts as shortcuts
from cmt.test import TestCase


class ControlTests(TestCase):
    def setUp(self):
        self.knots = [0, 0, 0, 1, 2, 3, 3, 3]
        self.cvs = [
            (-69.090977, 0.0, -42.485142),
            (-12.141088, 0.0, -22.456294),
            (4.930275, 0.0, 2.926625),
            (0.242549, 0.0, 14.701021),
            (-22.959533, 0.0, 2.415859),
            (-40.740289, 0.0, -10.943939),
        ]
        self.curve = cmds.curve(d=3, p=self.cvs, k=self.knots)

    def cvs_are_equal(self, cvs1, cvs2):
        for cv1, cv2 in zip(cvs1, cvs2):
            self.assertListAlmostEqual(cv1, cv2)

    def test_get_curve_object(self):
        obj = control.CurveShape(self.curve)
        self.assertEqual(obj.degree, 3)
        self.assertEqual(obj.form, 0)
        self.assertListEqual(obj.knots, self.knots)
        self.cvs_are_equal(obj.cvs, self.cvs)
        self.assertIsNone(obj.color)

    def test_get_curve_object_with_history(self):
        curve = cmds.circle()[0]
        obj = control.CurveShape(curve)
        self.assertEqual(obj.degree, 3)
        self.assertEqual(obj.form, 2)
        self.assertListEqual(obj.knots, range(-2, 11))
        expected_cvs = [
            (0.7836116248912245, 0.7836116248912246, 0.0),
            (6.785732323110912e-17, 1.1081941875543877, 0.0),
            (-0.7836116248912245, 0.7836116248912244, 0.0),
            (-1.1081941875543881, 5.74489823752483e-17, 0.0),
            (-0.7836116248912245, -0.7836116248912245, 0.0),
            (-1.1100856969603225e-16, -1.1081941875543884, 0.0),
            (0.7836116248912245, -0.7836116248912244, 0.0),
            (1.1081941875543881, -1.511240500779959e-16, 0.0),
        ]
        self.cvs_are_equal(obj.cvs, expected_cvs)
        self.assertIsNone(obj.color)

    def test_create_on_nonexisting_transform(self):
        obj = control.CurveShape(self.curve)
        transform = obj.create("node1")
        self.assertTrue(cmds.objExists(transform))
        obj = control.CurveShape(transform)
        self.assertEqual(obj.degree, 3)
        self.assertEqual(obj.form, 0)
        self.assertListEqual(obj.knots, self.knots)
        self.cvs_are_equal(obj.cvs, self.cvs)
        self.assertIsNone(obj.color)

    def test_create_on_existing_transform(self):
        transform = cmds.createNode("transform", name="my_new_transform")
        obj = control.CurveShape(self.curve)
        transform2 = obj.create(transform)
        self.assertEqual(transform, transform2)
        self.assertTrue(cmds.objExists(transform))
        obj = control.CurveShape(transform)
        self.assertEqual(obj.degree, 3)
        self.assertEqual(obj.form, 0)
        self.assertListEqual(obj.knots, self.knots)
        self.cvs_are_equal(obj.cvs, self.cvs)
        self.assertIsNone(obj.color)

    def test_translate(self):
        obj = control.CurveShape(self.curve)
        offset = (0.2, 0.3, 0.4)
        obj.translate_by(*offset)
        transform = obj.create("node1")
        expected_cvs = [
            (offset[0] + x[0], offset[1] + x[1], offset[2] + x[2]) for x in self.cvs
        ]
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

        obj.translate_by(*offset)
        transform = obj.create("node2")
        expected_cvs = [
            (2 * offset[0] + x[0], 2 * offset[1] + x[1], 2 * offset[2] + x[2])
            for x in self.cvs
        ]
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

        obj.set_translation(0, 0, 0)
        transform = obj.create("node3")
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, self.cvs)

    def test_scale(self):
        obj = control.CurveShape(self.curve)
        offset = (3.0, 3.0, 3.0)
        obj.scale_by(*offset)
        transform = obj.create("node1")
        expected_cvs = [
            (offset[0] * x[0], offset[1] * x[1], offset[2] * x[2]) for x in self.cvs
        ]
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

        obj.scale_by(*offset)
        transform = obj.create("node2")
        expected_cvs = [
            (
                offset[0] * offset[0] * x[0],
                offset[1] * offset[1] * x[1],
                offset[2] * offset[2] * x[2],
            )
            for x in self.cvs
        ]
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

        obj.set_scale(1, 1, 1)
        transform = obj.create("node3")
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, self.cvs)

    def test_rotate(self):
        obj = control.CurveShape(self.curve)
        offset = (90.0, 0.0, 0.0)
        obj.rotate_by(*offset)
        transform = obj.create("node1")

        expected_cvs = [
            (-69.090977, 42.48514199999038, 2.860121442424159e-05),
            (-12.141088, 22.456293999994912, 1.5117691730153798e-05),
            (4.930275, -2.926624999999337, -1.970218886507336e-06),
            (0.242549, -14.701020999996672, -9.896802366254971e-06),
            (-22.959533, -2.415858999999453, -1.6263686085298683e-06),
            (-40.740289, 10.943938999997522, 7.3675155889750836e-06),
        ]
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

        obj.rotate_by(*offset)
        transform = obj.create("node2")
        expected_cvs = [
            (-69.090977, -5.720242882439578e-05, 42.48514199996149),
            (-12.141088, -3.0235383447575762e-05, 22.456293999979646),
            (4.930275, 3.94043777135539e-06, -2.9266249999973475),
            (0.242549, 1.9793604724175044e-05, -14.701020999986676),
            (-22.959533, 3.2527372156900394e-06, -2.4158589999978104),
            (-40.740289, -1.4735031171745385e-05, 10.943938999990081),
        ]
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

        obj.set_rotation(0, 0, 0)
        transform = obj.create("node3")
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, self.cvs)

        obj.set_rotation(180, 0, 0)
        transform = obj.create("node4")
        cvs = cmds.getAttr("{}.cv[*]".format(transform))
        self.cvs_are_equal(cvs, expected_cvs)

    def test_get_control_data(self):
        controls = control.get_curve_data([self.curve])
        expected = [
            {
                "transform": self.curve,
                "cvs": self.cvs,
                "degree": 3,
                "form": 0,
                "knots": self.knots,
                "color": None,
            }
        ]
        expected = json.dumps(expected, sort_keys=True)
        actual = json.dumps(controls, sort_keys=True, cls=control.CurveShapeEncoder)
        self.assertEqual(expected, actual)

    def test_save_and_load_curves(self):
        file_path = self.get_temp_filename("test_curve.json")
        control.export_curves([self.curve], file_path)
        self.assertTrue(os.path.exists(file_path))
        cmds.delete(self.curve)
        controls = control.import_curves(file_path)
        self.assertTrue(cmds.objExists(self.curve))
        self.assertEqual(controls[0], self.curve)
        self.test_get_curve_object()

    def test_save_and_load_curve_on_other_transform(self):
        file_path = self.get_temp_filename("test_curve.json")
        control.export_curves([self.curve], file_path)
        other = cmds.createNode("transform", name="other")
        cmds.setAttr("{}.tx".format(other), 2)
        control.import_curves_on_selected(file_path)
        self.assertTrue(cmds.objExists("otherShape"))
        obj = control.CurveShape(other)
        self.assertEqual(obj.degree, 3)
        self.assertEqual(obj.form, 0)
        self.assertListEqual(obj.knots, self.knots)
        self.cvs_are_equal(obj.cvs, self.cvs)
        self.assertIsNone(obj.color)

    def test_mirror_curve(self):
        cmds.setAttr("{}.t".format(self.curve), 62, 3, 52)
        cmds.setAttr("{}.r".format(self.curve), 162, -231, -10)
        other = cmds.createNode("transform")
        cmds.setAttr("{}.t".format(other), 1, 2, 3)
        cmds.setAttr("{}.r".format(other), 45, 23, 10)
        mirrored_curve = control.mirror_curve(self.curve, other)

        path_curve = shortcuts.get_dag_path(self.curve)
        matrix = path_curve.inclusiveMatrix()

        path_other = shortcuts.get_dag_path(other)
        inverse_matrix = path_other.inclusiveMatrixInverse()

        world_cvs = [OpenMaya.MPoint(x[0], x[1], x[2]) * matrix for x in self.cvs]
        for cv in world_cvs:
            cv.x *= -1
        expected_local_cvs = [p * inverse_matrix for p in world_cvs]
        expected_local_cvs = [(p.x, p.y, p.z) for p in expected_local_cvs]
        self.cvs_are_equal(mirrored_curve.cvs, expected_local_cvs)
