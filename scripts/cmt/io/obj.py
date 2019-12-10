import os
import maya.cmds as cmds


def import_obj(file_path):

    old_nodes = set(cmds.ls(assemblies=True))

    cmds.file(
        file_path,
        i=True,
        type="OBJ",
        ignoreVersion=True,
        mergeNamespacesOnClash=False,
        options="mo=0",
    )

    new_nodes = set(cmds.ls(assemblies=True))
    new_nodes = new_nodes.difference(old_nodes)
    new_mesh = list(new_nodes)[0]
    name = os.path.splitext(os.path.basename(file_path))[0]
    return cmds.rename(new_mesh, name)


def export_obj(mesh, file_path):
    cmds.select(mesh)
    cmds.file(
        file_path,
        force=True,
        options="groups=0;ptgroups=0;materials=0;smoothing=0;normals=1",
        typ="OBJexport",
        es=True,
    )
