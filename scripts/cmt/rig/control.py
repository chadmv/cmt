"""The control module provides functions and a graphical interface to create,
manipulate, import and export curve controls.

.. image:: control.png

The APIs provided allow curve shapes to be abstracted from transforms.  This allows the
creation of rigging constructs independent of actual curve shapes which can vary
greatly from asset to asset.  The general workflow would be to create rig controls
with transforms only without shapes.  After the rigs are created, add shapes to the
transforms with this tool/API.  The shapes can then be serialized to disk to load back
in an automated build.

Example Usage
=============

The Control Creator tool can be accessed in the cmt menu::

    CMT > Rigging > Control Creator

API
---
::

    import cmt.rig.control as control
    curve = cmds.circle()[0]

    # Save the curve to disk
    file_path = "{}/control.json".format(cmds.workspace(q=True, rd=True))
    control.export_curves([curve], file_path)

    # Load the curve back in
    cmds.file(n=True, f=True)
    control.import_curves(file_path)

    # Create another copy of the curve
    control.import_new_curves(file_path)

    # Create the curve on the selected transform
    node = cmds.createNode('transform', name='newNode')
    control.import_curves_on_selected(file_path)

    # Manipulate the curve before creating
    curve = control.load_curves(file_path)[0]
    curve.scale_by(2, 2, 2)
    curve.set_rotation(0, 60, 0)
    curve.set_translation(10, 5, 0)
    new_node = curve.create("anotherNode")

    # Mirror the curve
    mirrored = cmds.createNode("transform", name="mirroredNode")
    cmds.setAttr("{}.t".format(mirrored), -10, -5, 2)
    cmds.setAttr("{}.r".format(mirrored), -55, 10, 63)
    control.mirror_curve(new_node, mirrored)

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import logging
import webbrowser

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from cmt.settings import DOCUMENTATION_ROOT
import cmt.shortcuts as shortcuts

logger = logging.getLogger(__name__)
CONTROLS_DIRECTORY = os.path.join(os.path.dirname(__file__), "controls")
HELP_URL = "{}/rig/control.html".format(DOCUMENTATION_ROOT)


def export_curves(controls=None, file_path=None):
    """Serializes the given curves into the control library.

    :param controls: Optional list of controls to export. If no controls are specified,
        the selected curves will be exported.
    :param file_path: File path to export to
    :return: The exported list of ControlShapes.
    """
    if file_path is None:
        file_path = shortcuts.get_save_file_name("*.json", "cmt.control")
        if not file_path:
            return
    if controls is None:
        controls = cmds.ls(sl=True)
    data = get_curve_data(controls)
    with open(file_path, "w") as fh:
        json.dump(data, fh, indent=4, cls=CurveShapeEncoder)
        logger.info("Exported controls to {}".format(file_path))
    return data


def get_curve_data(controls=None):
    """Get the serializable data of the given controls.

    :param controls: Controls to serialize
    :return: List of ControlShape objects
    """
    if controls is None:
        controls = cmds.ls(sl=True)
    data = [CurveShape(transform=control) for control in controls]
    # Prune empty curves
    data = [x for x in data if x.cvs]
    return data


def import_new_curves(file_path=None, tag_as_controller=False):
    """Imports control shapes from disk onto new transforms.

    :param file_path: Path to the control file.
    :param tag_as_controller: True to tag the curve transform as a controller
    :return: The new curve transforms
    """
    controls = load_curves(file_path)
    transforms = []
    for curve in controls:
        transform = _get_new_transform_name(curve.transform)
        transforms.append(curve.create(transform, tag_as_controller))
    return transforms


def import_curves(file_path=None, tag_as_controller=False):
    """Imports control shapes from disk onto their saved named transforms.

    :param file_path: Path to the control file.
    :param tag_as_controller: True to tag the curve transform as a controller
    :return: The new curve transforms
    """
    controls = load_curves(file_path)

    transforms = [
        curve.create(curve.transform, tag_as_controller) for curve in controls
    ]
    return transforms


def import_curves_on_selected(file_path=None, tag_as_controller=False):
    """Imports a control shape from disk onto the selected transform.

    :param file_path: Path to the control file.
    :param tag_as_controller: True to tag the curve transform as a controller
    :return: The new curve transform
    """
    controls = load_curves(file_path)
    selected_transforms = cmds.ls(sl=True)
    if not selected_transforms:
        return

    for transform in selected_transforms:
        for curve in controls:
            curve.create(transform, tag_as_controller)
    return selected_transforms


def load_curves(file_path=None):
    """Load the CurveShape objects from disk.

    :param file_path:
    :return:
    """
    if file_path is None:
        file_path = shortcuts.get_open_file_name("*.json", "cmt.control")
        if not file_path:
            return

    with open(file_path, "r") as fh:
        data = json.load(fh)
    logger.info("Loaded controls {}".format(file_path))
    curves = [CurveShape(**control) for control in data]
    return curves


def _get_new_transform_name(base):
    """Get a new unique transform name

    :param base: Base name
    :return: A unique name of a non-existing transform
    """
    name = base
    i = 1
    while cmds.objExists(name):
        name = "{}{}".format(base, i)
        i += 1
    return name


class CurveShape(object):
    """Represents the data required to build a nurbs curve shape"""

    def __init__(
        self, transform=None, cvs=None, degree=3, form=0, knots=None, color=None
    ):
        self.cvs = cvs
        self.degree = degree
        self.form = form
        self.knots = knots
        self.color = color
        self.transform_matrix = OpenMaya.MTransformationMatrix()
        self.transform = transform
        if transform and cmds.objExists(transform) and not cvs:
            self._set_from_curve(transform)

    def _set_from_curve(self, transform):
        """Store the parameters from an existing curve in the CurveShape object.

        :param transform: Transform
        """
        shape = shortcuts.get_shape(transform)
        if shape and cmds.nodeType(shape) == "nurbsCurve":
            create_attr = "{}.create".format(shape)
            connection = cmds.listConnections(create_attr, plugs=True, d=False)
            if connection:
                cmds.disconnectAttr(connection[0], create_attr)
            self.transform = transform
            self.cvs = cmds.getAttr("{}.cv[*]".format(shape))
            self.degree = cmds.getAttr("{}.degree".format(shape))
            self.form = cmds.getAttr("{}.form".format(shape))
            self.knots = get_knots(shape)
            if cmds.getAttr("{}.overrideEnabled".format(shape)):
                if cmds.getAttr("{}.overrideRGBColors".format(shape)):
                    self.color = cmds.getAttr("{}.overrideColorRGB".format(shape))[0]
                else:
                    self.color = cmds.getAttr("{}.overrideColor".format(shape))
            else:
                self.color = None
            if connection:
                cmds.connectAttr(connection[0], create_attr)

    def create(self, transform=None, as_controller=True):
        """Create a curve.

        :param transform: Name of the transform to create the curve shape under.
            If the transform does not exist, it will be created.
        :param as_controller: True to mark the curve transform as a controller.
        :return: The transform of the new curve shapes.
        """
        transform = transform or self.transform
        if not cmds.objExists(transform):
            transform = cmds.createNode("transform", name=transform)
        periodic = self.form == 2
        points = self._get_transformed_points()
        points = points + points[: self.degree] if periodic else points
        curve = cmds.curve(degree=self.degree, p=points, per=periodic, k=self.knots)
        shape = shortcuts.get_shape(curve)
        if self.color is not None:
            cmds.setAttr("{}.overrideEnabled".format(shape), True)
            if isinstance(self.color, int):
                cmds.setAttr("{}.overrideColor".format(shape), self.color)
            else:
                cmds.setAttr("{}.overrideRGBColors".format(shape), True)
                cmds.setAttr("{}.overrideColorRGB".format(shape), *self.color)
        cmds.parent(shape, transform, r=True, s=True)
        shape = cmds.rename(shape, "{}Shape".format(transform))
        cmds.delete(curve)
        if as_controller:
            cmds.controller(transform)
        logger.info("Created curve {} for transform {}".format(shape, transform))
        return transform

    def _get_transformed_points(self):
        matrix = self.transform_matrix.asMatrix()
        points = [OpenMaya.MPoint(*x) * matrix for x in self.cvs]
        points = [(p.x, p.y, p.z) for p in points]
        return points

    def translate_by(self, x, y, z, local=True):
        """Translate the curve cvs by the given values

        :param x: Translate X
        :param y: Translate Y
        :param z: Translate Z
        :param local: True for local space, False for world
        """
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.translateBy(OpenMaya.MVector(x, y, z), space)

    def set_translation(self, x, y, z, local=True):
        """Set the absolute translation of the curve shape.

        :param x: Translate X
        :param y: Translate Y
        :param z: Translate Z
        :param local: True for local space, False for world
        """
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.setTranslation(OpenMaya.MVector(x, y, z), space)

    def rotate_by(self, x, y, z, local=True):
        """Rotate the curve cvs by the given euler rotation values

        :param x: Rotate X
        :param y: Rotate Y
        :param z: Rotate Z
        :param local: True for local space, False for world
        """
        x, y, z = [v * 0.0174533 for v in [x, y, z]]
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.rotateBy(OpenMaya.MEulerRotation(x, y, z), space)

    def set_rotation(self, x, y, z):
        """Set the absolute rotation of the curve shape in euler rotations.

        :param x: Rotate X
        :param y: Rotate Y
        :param z: Rotate Z
        """
        x, y, z = [v * 0.0174533 for v in [x, y, z]]
        self.transform_matrix.setRotation(OpenMaya.MEulerRotation(x, y, z))

    def scale_by(self, x, y, z, local=True):
        """Scale the curve cvs by the given amount.

        :param x: Scale X
        :param y: Scale Y
        :param z: Scale Z
        :param local: True for local space, False for world
        """
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.scaleBy([x, y, z], space)

    def set_scale(self, x, y, z, local=True):
        """Set the absolute scale of the curve shape.

        :param x: Scale X
        :param y: Scale Y
        :param z: Scale Z
        :param local: True for local space, False for world
        """
        space = OpenMaya.MSpace.kObject if local else OpenMaya.MSpace.kWorld
        self.transform_matrix.setScale([x, y, z], space)


class CurveShapeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CurveShape):
            return {
                "cvs": obj.cvs,
                "degree": obj.degree,
                "form": obj.form,
                "knots": obj.knots,
                "color": obj.color,
                "transform": obj.transform,
            }
        return json.JSONEncoder.default(self, obj)


def rotate_components(rx, ry, rz, nodes=None):
    """Rotate the given nodes' components the given number of degrees about each axis.

    :param rx: Degrees around x.
    :param ry: Degrees around y.
    :param rz: Degrees around z.
    :param nodes: Optional list of curves.
    """
    if nodes is None:
        nodes = cmds.ls(sl=True) or []
    for node in nodes:
        pivot = cmds.xform(node, q=True, rp=True, ws=True)
        cmds.rotate(
            rx, ry, rz, "{0}.cv[*]".format(node), r=True, p=pivot, os=True, fo=True
        )


def mirror_curve(source, destination):
    """Mirrors the curve on source across the YZ plane to destination.

    The cvs will be mirrored in world space no matter the transform of destination.

    :param source: Source transform
    :param destination: Destination transform
    :return: The mirrored CurveShape object
    """
    source_curve = CurveShape(source)

    path_source = shortcuts.get_dag_path2(source)
    matrix = path_source.inclusiveMatrix()

    path_destination = shortcuts.get_dag_path2(destination)
    inverse_matrix = path_destination.inclusiveMatrixInverse()

    world_cvs = [OpenMaya.MPoint(*x) * matrix for x in source_curve.cvs]
    for cv in world_cvs:
        cv.x *= -1
    local_cvs = [p * inverse_matrix for p in world_cvs]
    source_curve.cvs = [(p.x, p.y, p.z) for p in local_cvs]
    is_controller = cmds.controller(source, q=True, isController=True)
    source_curve.transform = destination
    source_curve.create(destination, as_controller=is_controller)
    return source_curve


def get_knots(curve):
    """Gets the list of knots of a curve so it can be recreated.

    :param curve: Curve to query.
    :return: A list of knot values that can be passed into the curve creation command.
    """
    curve = shortcuts.get_shape(curve)
    info = cmds.createNode("curveInfo")
    cmds.connectAttr("{0}.worldSpace".format(curve), "{0}.inputCurve".format(info))
    knots = cmds.getAttr("{0}.knots[*]".format(info))
    knots = [int(x) for x in knots]
    cmds.delete(info)
    return knots


def documentation():
    webbrowser.open(HELP_URL)


def get_control_paths_in_library():
    """Get the file paths of all controls in the library.

    :return: List of file paths
    """
    controls = [
        os.path.splitext(x)[0]
        for x in os.listdir(CONTROLS_DIRECTORY)
        if x.endswith(".json")
    ]
    controls.sort()
    return controls
