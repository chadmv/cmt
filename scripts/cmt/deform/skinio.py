"""Exports and imports skin weights.

Usage:
    Select a mesh and run

    # To export
    import skinio
    skinio.export_skin(file_path='/path/to/data.skin')

    # To import
    skinio.import_skin(file_path='/path/to/data.skin')
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
import re
from six import string_types
from functools import partial

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

import cmt.shortcuts as shortcuts

logger = logging.getLogger(__name__)
EXTENSION = ".skin"

# Key value for QSettings to save file browser directory
KEY_STORE = "skinio.start_directory"


def import_skin(file_path=None, shape=None, to_selected_shapes=False, enable_remap=True):
    """Creates a skinCluster on the specified shape if one does not already exist
    and then import the weight data.
    """

    if file_path is None:
        file_path = shortcuts.get_open_file_name(
            "Skin Files (*{})".format(EXTENSION), key=KEY_STORE
        )
    if not file_path:
        return

    # Read in the file
    with open(file_path, "r") as fh:
        data = json.load(fh)

    # Some cases the skinningMethod may have been set to -1
    if data.get("skinningMethod", 0) < 0:
        data["skinningMethod"] = 0

    selected_components = []
    if to_selected_shapes:
        shape = cmds.ls(sl=True)
        if shape:
            components = cmds.filterExpand(sm=31) or []
            selected_components = [
                int(re.search("(?<=\[)\d+", x).group(0)) for x in components
            ]
            shape = shape[0].split(".")[0]
    if shape is None:
        shape = data["shape"]
    if not cmds.objExists(shape):
        logging.warning("Cannot import skin, {} does not exist".format(shape))
        return

    # Make sure the vertex count is the same
    mesh_vertex_count = cmds.polyEvaluate(shape, vertex=True)
    imported_vertex_count = len(data["blendWeights"])
    if mesh_vertex_count != imported_vertex_count:
        raise RuntimeError(
            "Vertex counts do not match. Mesh {} != File {}".format(
                mesh_vertex_count, imported_vertex_count
            )
        )

    # Check if the shape has a skinCluster
    skins = get_skin_clusters(shape)
    if skins:
        skin_cluster = SkinCluster(skins[0])
    else:
        # Create a new skinCluster
        joints = data["weights"].keys()

        unused_imports, no_match = get_joints_that_need_remapping(joints)

        # If there were unmapped influences ask the user to map them
        if unused_imports and no_match and enable_remap:
            mapping_dialog = WeightRemapDialog(file_path)
            mapping_dialog.set_influences(unused_imports, no_match)
            result = mapping_dialog.exec_()
            remap_weights(mapping_dialog.mapping, data["weights"])

        # Create the skinCluster with post normalization so setting the weights does not
        # normalize all the weights
        joints = [x for x in data["weights"].keys() if cmds.objExists(x)]
        kwargs = {}
        if data["maintainMaxInfluences"]:
            kwargs["obeyMaxInfluences"] = True
            kwargs["maximumInfluences"] = data["maxInfluences"]
        skin = cmds.skinCluster(
            joints, shape, tsb=True, nw=2, n=data["name"], **kwargs
        )[0]
        skin_cluster = SkinCluster(skin)

    skin_cluster.set_data(data, selected_components)
    logging.info("Imported %s", file_path)


def get_skin_clusters(nodes):
    """Get the skinClusters attached to the specified node and all nodes in descendents.

    :param nodes: List of dag nodes.
    @return A list of the skinClusters in the hierarchy of the specified root node.
    """
    if isinstance(nodes, string_types):
        nodes = [nodes]
    all_skins = []
    for node in nodes:
        relatives = cmds.listRelatives(node, ad=True, path=True) or []
        relatives.insert(0, node)
        relatives = [shortcuts.get_shape(node) for node in relatives]
        for relative in relatives:
            history = cmds.listHistory(relative, pruneDagObjects=True, il=2) or []
            skins = [x for x in history if cmds.nodeType(x) == "skinCluster"]
            if skins:
                all_skins.append(skins[0])
    return list(set(all_skins))


def get_joints_that_need_remapping(joints_in_file):
    # Make sure all the joints exist
    unused_joints_from_file = []
    joints_that_get_no_weights = set(
        [shortcuts.remove_namespace_from_name(x) for x in cmds.ls(type="joint")]
    )
    for j in joints_in_file:
        j = j.split("|")[-1]
        if j in joints_that_get_no_weights:
            joints_that_get_no_weights.remove(j)
        else:
            unused_joints_from_file.append(j)
    return unused_joints_from_file, joints_that_get_no_weights


def remap_weights(remapping, weight_dict):
    for src, dst in remapping.items():
        weight_dict[dst] = weight_dict[src]
        del weight_dict[src]
    return weight_dict


def export_skin(file_path=None, shapes=None):
    """Exports the skinClusters of the given shapes to disk.

    :param file_path: Path to export the data.
    :param shapes: Optional list of dag nodes to export skins from.  All descendent nodes will be
        searched for skinClusters also.
    """
    if shapes is None:
        shapes = cmds.ls(sl=True) or []

    # If no shapes were selected, export all skins
    skins = get_skin_clusters(shapes) if shapes else cmds.ls(type="skinCluster")
    if not skins:
        raise RuntimeError("No skins to export.")

    if file_path is None:
        if len(skins) == 1:
            file_path = shortcuts.get_save_file_name(
                "Skin Files (*{})".format(EXTENSION), KEY_STORE
            )
        else:
            file_path = shortcuts.get_directory_name(KEY_STORE)
        if not file_path:
            return

    directory = file_path if len(skins) > 1 else os.path.dirname(file_path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    for skin in skins:
        skin = SkinCluster(skin)
        data = skin.gather_data()
        if len(skins) > 1:
            # With multiple skinClusters, the user just chooses an export directory.  Set the
            # name to the transform name.
            file_path = os.path.join(
                directory, "{}{}".format(skin.shape.replace("|", "!"), EXTENSION)
            )
        logger.info(
            "Exporting skinCluster %s on %s (%d influences, %d vertices) : %s",
            skin.node,
            skin.shape,
            len(data["weights"].keys()),
            len(data["blendWeights"]),
            file_path
        )
        with open(file_path, "w") as fh:
            json.dump(data, fh)


class SkinCluster(object):
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
    ]

    def __init__(self, skin_cluster):
        """Constructor"""
        self.node = skin_cluster
        self.shape = cmds.listRelatives(
            cmds.deformer(skin_cluster, q=True, g=True)[0], parent=True, path=True
        )[0]

        # Get the skinCluster MObject
        self.mobject = shortcuts.get_mobject(self.node)
        self.fn = OpenMayaAnim.MFnSkinCluster(self.mobject)
        self.data = {
            "weights": {},
            "blendWeights": [],
            "name": self.node,
            "shape": self.shape,
        }

    def gather_data(self):
        """Gather all the skinCluster data into a dictionary so it can be serialized.

        :return: The data dictionary containing all the skinCluster data.
        """
        dag_path, components = self.__get_geometry_components()
        self.gather_influence_weights(dag_path, components)
        self.gather_blend_weights(dag_path, components)

        for attr in SkinCluster.attributes:
            self.data[attr] = cmds.getAttr("%s.%s" % (self.node, attr))
        return self.data

    def __get_geometry_components(self):
        """Get the MDagPath and component MObject of the deformed geometry.

        :return: (MDagPath, MObject)
        """
        # Get dagPath and member components of skinned shape
        fnset = OpenMaya.MFnSet(self.fn.deformerSet())
        members = OpenMaya.MSelectionList()
        fnset.getMembers(members, False)
        dag_path = OpenMaya.MDagPath()
        components = OpenMaya.MObject()
        members.getDagPath(0, dag_path, components)
        return dag_path, components

    def gather_influence_weights(self, dag_path, components):
        """Gathers all the influence weights

        :param dag_path: MDagPath of the deformed geometry.
        :param components: Component MObject of the deformed components.
        """
        weights = self.__get_current_weights(dag_path, components)

        influence_paths = OpenMaya.MDagPathArray()
        influence_count = self.fn.influenceObjects(influence_paths)
        components_per_influence = weights.length() // influence_count
        for ii in range(influence_paths.length()):
            influence_name = influence_paths[ii].partialPathName()
            # We want to store the weights by influence without the namespace so it is easier
            # to import if the namespace is different
            influence_without_namespace = shortcuts.remove_namespace_from_name(
                influence_name
            )
            self.data["weights"][influence_without_namespace] = [
                weights[jj * influence_count + ii]
                for jj in range(components_per_influence)
            ]

    def gather_blend_weights(self, dag_path, components):
        """Gathers the blendWeights

        :param dag_path: MDagPath of the deformed geometry.
        :param components: Component MObject of the deformed components.
        """
        weights = OpenMaya.MDoubleArray()
        self.fn.getBlendWeights(dag_path, components, weights)
        self.data["blendWeights"] = [weights[i] for i in range(weights.length())]

    def __get_current_weights(self, dag_path, components):
        """Get the current skin weight array.

        :param dag_path: MDagPath of the deformed geometry.
        :param components: Component MObject of the deformed components.
        :return: An MDoubleArray of the weights.
        """
        weights = OpenMaya.MDoubleArray()
        util = OpenMaya.MScriptUtil()
        util.createFromInt(0)
        ptr = util.asUintPtr()
        self.fn.getWeights(dag_path, components, weights, ptr)
        return weights

    def set_data(self, data, selected_components=None):
        """Sets the data and stores it in the Maya skinCluster node.

        :param data: Data dictionary.
        """

        self.data = data
        dag_path, components = self.__get_geometry_components()
        if selected_components:
            fncomp = OpenMaya.MFnSingleIndexedComponent()
            components = fncomp.create(OpenMaya.MFn.kMeshVertComponent)
            for i in selected_components:
                fncomp.addElement(i)
        self.set_influence_weights(dag_path, components)
        self.set_blend_weights(dag_path, components)

        for attr in SkinCluster.attributes:
            cmds.setAttr("{0}.{1}".format(self.node, attr), self.data[attr])

    def set_influence_weights(self, dag_path, components):
        """Sets all the influence weights.

        :param dag_path: MDagPath of the deformed geometry.
        :param components: Component MObject of the deformed components.
        """
        influence_paths = OpenMaya.MDagPathArray()
        influence_count = self.fn.influenceObjects(influence_paths)

        elements = OpenMaya.MIntArray()
        fncomp = OpenMaya.MFnSingleIndexedComponent(components)
        fncomp.getElements(elements)
        weights = OpenMaya.MDoubleArray(elements.length() * influence_count)

        components_per_influence = elements.length()

        for imported_influence, imported_weights in self.data["weights"].items():
            imported_influence = imported_influence.split("|")[-1]
            for ii in range(influence_paths.length()):
                influence_name = influence_paths[ii].partialPathName()
                influence_without_namespace = shortcuts.remove_namespace_from_name(
                    influence_name
                )
                if influence_without_namespace == imported_influence:
                    # Store the imported weights into the MDoubleArray
                    for jj in range(components_per_influence):
                        weights.set(imported_weights[elements[jj]], jj * influence_count + ii)
                    break

        influence_indices = OpenMaya.MIntArray(influence_count)
        for ii in range(influence_count):
            influence_indices.set(ii, ii)
        self.fn.setWeights(dag_path, components, influence_indices, weights, False)

    def set_blend_weights(self, dag_path, components):
        """Set the blendWeights.

        :param dag_path: MDagPath of the deformed geometry.
        :param components: Component MObject of the deformed components.
        """
        elements = OpenMaya.MIntArray()
        fncomp = OpenMaya.MFnSingleIndexedComponent(components)
        fncomp.getElements(elements)
        blend_weights = OpenMaya.MDoubleArray(elements.length())
        for i in range(elements.length()):
            blend_weights.set(self.data["blendWeights"][elements[i]], i)
        self.fn.setBlendWeights(dag_path, components, blend_weights)


class WeightRemapDialog(MayaQWidgetBaseMixin, QDialog):
    def __init__(self, file_path=None, parent=None):
        super(WeightRemapDialog, self).__init__(parent)
        self.setWindowTitle("Remap Weights")
        self.setObjectName("remapWeightsUI")
        self.setModal(True)
        self.resize(600, 400)
        self.mapping = {}

        mainvbox = QVBoxLayout(self)
        if file_path is None:
            file_path = ""

        label = QLabel(
            "{} The following influences have no corresponding influence from the "
            "imported file.  You can either remap the influences or skip them.".format(
                file_path
            )
        )
        label.setWordWrap(True)
        mainvbox.addWidget(label)

        hbox = QHBoxLayout()
        mainvbox.addLayout(hbox)

        # The existing influences that didn't have weight imported
        vbox = QVBoxLayout()
        hbox.addLayout(vbox)
        vbox.addWidget(QLabel("Unmapped influences"))
        self.existing_influences = QListWidget()
        vbox.addWidget(self.existing_influences)

        vbox = QVBoxLayout()
        hbox.addLayout(vbox)
        vbox.addWidget(QLabel("Available imported influences"))
        widget = QScrollArea()
        self.imported_influence_layout = QVBoxLayout(widget)
        vbox.addWidget(widget)

        hbox = QHBoxLayout()
        mainvbox.addLayout(hbox)
        hbox.addStretch()

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        hbox.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def set_influences(self, imported_influences, existing_influences):
        infs = list(existing_influences)
        infs.sort()
        self.existing_influences.addItems(infs)
        width = 200
        for inf in imported_influences:
            row = QHBoxLayout()
            self.imported_influence_layout.addLayout(row)
            label = QLabel(inf)
            row.addWidget(label)
            toggle_btn = QPushButton(">")
            toggle_btn.setMaximumWidth(30)
            row.addWidget(toggle_btn)
            label = QLabel("")
            label.setMaximumWidth(width)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            row.addWidget(label)
            toggle_btn.released.connect(
                partial(self.set_influence_mapping, src=inf, label=label)
            )
        self.imported_influence_layout.addStretch()

    def set_influence_mapping(self, src, label):
        selected_influence = self.existing_influences.selectedItems()
        if not selected_influence:
            return
        dst = selected_influence[0].text()
        label.setText(dst)
        self.mapping[src] = dst
        # Remove the item from the list
        index = self.existing_influences.indexFromItem(selected_influence[0])
        item = self.existing_influences.takeItem(index.row())
        del item
