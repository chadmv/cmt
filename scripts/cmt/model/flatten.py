from __future__ import absolute_import

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

import cmt.shortcuts as shortcuts


def flatten(mesh=None, uvset=None):
    """Creates a mesh from the UV layout of another mesh.

    I use this to generate flattened versions of meshes from Marvelous Designer to easily use Quad
    Draw to create clean meshes and then Transfer Attributes vertex positions through UVs.

    :param mesh: Mesh to sample.
    :param uvset: UV set name
    """
    if mesh is None:
        mesh = cmds.ls(sl=True)
        if not mesh:
            raise RuntimeError('No mesh selected.')
        mesh = mesh[0]
    o_mesh = shortcuts.get_mobject(shortcuts.get_shape(mesh))
    fn_mesh = OpenMaya.MFnMesh(o_mesh)
    if uvset is None:
        uvset = fn_mesh.currentUVSetName()

    vertex_count = fn_mesh.numUVs(uvset)
    polygon_count = fn_mesh.numPolygons()
    u_array = OpenMaya.MFloatArray()
    v_array = OpenMaya.MFloatArray()
    fn_mesh.getUVs(u_array, v_array, uvset)
    vertex_array = OpenMaya.MPointArray(u_array.length())
    for i in range(u_array.length()):
        vertex_array.set(i, u_array[i], 0, -v_array[i])
    polygon_counts = OpenMaya.MIntArray(polygon_count)

    it_poly = OpenMaya.MItMeshPolygon(o_mesh)
    polygon_connects = OpenMaya.MIntArray(fn_mesh.numFaceVertices())
    face_vertex_index = 0
    while not it_poly.isDone():
        face_index = it_poly.index()
        polygon_counts[face_index] = it_poly.polygonVertexCount()

        for i in range(polygon_counts[face_index]):
            int_ptr = shortcuts.get_int_ptr()
            it_poly.getUVIndex(i, int_ptr)
            uv_index = shortcuts.ptr_to_int(int_ptr)
            polygon_connects[face_vertex_index] = uv_index
            face_vertex_index += 1
        it_poly.next()

    new_mesh = OpenMaya.MFnMesh()
    new_mesh.create(vertex_count, polygon_count, vertex_array, polygon_counts, polygon_connects,
                    u_array, v_array)
    new_mesh.assignUVs(polygon_counts, polygon_connects)
