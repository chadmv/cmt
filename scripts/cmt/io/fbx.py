import os
import maya.cmds as cmds
import maya.mel as mel
import cmt.shortcuts as shortcuts


def import_fbx(file_path):
    file_path = file_path.replace("\\", "/")
    mel.eval("FBXImportMode -v Merge;")
    mel.eval('FBXImport -file "{}"'.format(file_path))


def export_fbx(nodes, file_path):
    file_path = file_path.replace("\\", "/")
    cmds.select(nodes)
    mel.eval("FBXExportCameras -v false;")
    mel.eval("FBXExportConstraints -v false;")
    mel.eval("FBXExportInAscii -v false;")
    mel.eval("FBXExportInputConnections -v true;")
    mel.eval("FBXExportShapes -v true;")
    mel.eval("FBXExportSkins -v true;")
    mel.eval("FBXExportSmoothingGroups -v true;")
    mel.eval("FBXExportSmoothMesh -v false;")
    mel.eval('FBXExport -f "{}" -s'.format(file_path))


def export_animation_fbx(root=None, file_path=None, start_frame=None, end_frame=None):
    if root is None:
        root = cmds.ls(sl=True)
        if not root:
            raise RuntimeError("Select the root joint to export")
        root = root[0]

    if file_path is None:
        file_path = shortcuts.get_save_file_name("*.fbx", "cmt.fbx.export")
        if not file_path:
            return

    if start_frame is None:
        start_frame = int(cmds.playbackOptions(q=True, min=True))
    if end_frame is None:
        end_frame = int(cmds.playbackOptions(q=True, max=True))

    file_path = file_path.replace("\\", "/")

    with ExportSkeleton(root) as skeleton:
        cmds.select(skeleton)
        mel.eval("FBXExportApplyConstantKeyReducer -v true;")
        mel.eval("FBXExportBakeComplexAnimation -v true;")
        mel.eval("FBXExportBakeComplexStart -v {};".format(start_frame))
        mel.eval("FBXExportBakeComplexEnd -v {};".format(end_frame))
        mel.eval("FBXExportBakeComplexStep -v 1;")
        mel.eval("FBXExportCameras -v false;")
        mel.eval("FBXExportConstraints -v false;")
        mel.eval("FBXExportInAscii -v false;")
        mel.eval("FBXExportInputConnections -v false;")
        mel.eval("FBXExportReferencedAssetsContent -v false;")
        mel.eval("FBXExportShapes -v true;")
        mel.eval("FBXExportSkins -v true;")
        mel.eval("FBXExportSmoothingGroups -v true;")
        mel.eval("FBXExportSmoothMesh -v false;")
        mel.eval('FBXExport -f "{}" -s'.format(file_path))


class ExportSkeleton(object):
    temp_namespace = "TEMP_EXPORT_NAMESPACE"

    def __init__(self, root):
        self.orig_root = root
        self.namespace = None
        self.joints = None

    def __enter__(self):
        namespace = shortcuts.get_namespace_from_name(self.orig_root)
        if not namespace:
            # Temporarily put the input skeleton in a namespace so we can create a duplicate
            # skeleton using the same names
            if not cmds.namespace(exists=":{}".format(ExportSkeleton.temp_namespace)):
                cmds.namespace(add=ExportSkeleton.temp_namespace)
            self.orig_root = cmds.rename(self.orig_root, "{}:{}".format(ExportSkeleton.temp_namespace, self.orig_root))

        self.joints = create_export_skeleton(self.orig_root)
        return self.joints

    def __exit__(self, type, value, traceback):
        cmds.delete(self.joints)
        if cmds.namespace(exists=":{}".format(ExportSkeleton.temp_namespace)):
            cmds.namespace(removeNamespace=":{}".format(ExportSkeleton.temp_namespace), mergeNamespaceWithRoot=True)


def create_export_skeleton(root):
    """Create a skeleton driven by the given list of joints ready to be exported
    to fbx.

    :param joints:
    :return:
    """
    namespace = shortcuts.get_namespace_from_name(root)
    export_root = cmds.duplicate(root)[0]
    if cmds.listRelatives(export_root, parent=True):
        export_root = cmds.parent(export_root, world=True)[0]
    joints = [export_root] + cmds.listRelatives(export_root, ad=True, path=True)
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for j in joints:
        if cmds.nodeType(j) != "joint":
            cmds.delete(j)
            continue
        if cmds.about(api=True) >= 20200000:
            # Remove any offset parent matrix
            cmds.setAttr("{}.opm".format(j), identity, type="matrix")
        source = "{}:{}".format(namespace, j)
        cmds.parentConstraint(source, j)
        cmds.scaleConstraint(source, j)
        attributes = cmds.listAttr(source, ud=True) or []
        for attr in attributes:
            cmds.connectAttr("{}.{}".format(source, attr), "{}.{}".format(j, attr))
    joints = [j for j in joints if cmds.objExists(j) and cmds.nodeType(j) == "joint"]
    # start = int(cmds.playbackOptions(q=True, min=True))
    # end = int(cmds.playbackOptions(q=True, max=True))
    # mel.eval("paneLayout -e -manage false $gMainPane")
    # cmds.bakeResults(joints, t=(start, end), simulation=True)
    # mel.eval("paneLayout -e -manage true $gMainPane")
    # cmds.delete(joints, constraints=True)
    cmds.select(joints)
    return joints
