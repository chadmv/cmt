import maya.cmds as cmds
import cmt.shortcuts as shortcuts


class Parts(object):
    hips = 0
    chest = 1
    neck = 2
    head = 3
    left_clavicle = 4
    left_shoulder = 5
    left_elbow = 6
    left_hand = 7
    left_up_leg = 8
    left_lo_leg = 9
    left_foot = 10
    right_clavicle = 11
    right_shoulder = 12
    right_elbow = 13
    right_hand = 14
    right_up_leg = 15
    right_lo_leg = 16
    right_foot = 17


def create():
    node = cmds.createNode("ikRig")
    joints = ['Hips', 'Spine3', 'Neck', 'Head', 'Clavicle_L', 'UpperArm_L', 'Forearm_L', 'Hand_L', 'Thigh_L',
              'Knee_L', 'Foot_L', 'Clavicle_R', 'UpperArm_R', 'Forearm_R', 'Hand_R', 'Thigh_R', 'Knee_R', 'Foot_R']

    out_joints = ['pelvis', 'spine_03', 'neck_01', 'head', 'clavicle_l', 'upperarm_l', 'lowerarm_l', 'hand_l',
                  'thigh_l', 'calf_l', 'foot_l', 'clavicle_r', 'upperarm_r', 'lowerarm_r', 'hand_r', 'thigh_r',
                  'calf_r', 'foot_r']

    locs = []
    for i, j in enumerate(joints):
        cmds.connectAttr("{}.worldMatrix[0]".format(j), "{}.inMatrix[{}]".format(node, i))
        path = shortcuts.get_dag_path2(j)
        pre_matrix = list(path.inclusiveMatrixInverse())
        cmds.setAttr("{}.inBindPreMatrix[{}]".format(node, i), *pre_matrix, type="matrix")

        path = shortcuts.get_dag_path2(out_joints[i])
        matrix = list(path.inclusiveMatrix())
        cmds.setAttr("{}.targetRestMatrix[{}]".format(node, i), *matrix, type="matrix")

        loc = cmds.spaceLocator(name="ikrig_{}".format(j))[0]
        cmds.connectAttr("{}.outputTranslate[{}]".format(node, i), "{}.t".format(loc))
        cmds.connectAttr("{}.outputRotate[{}]".format(node, i), "{}.r".format(loc))

        cmds.setAttr("{}Shape.localScale".format(loc), 5, 5, 5)
        locs.append(loc)

    for loc, joint in zip(locs, out_joints):
        cmds.parentConstraint(loc, joint)
    loc = cmds.spaceLocator(name="rootMotion")[0]
    cmds.connectAttr("{}.rootMotion".format(node), "{}.opm".format(loc))
    return node

"""
import maya.api.OpenMaya as OpenMaya
import cmt.shortcuts as shortcuts
import math


def clamp(v, minv, maxv):
    return max(min(v, maxv), minv)


def two_bone_ik(a, b, c, d, t, pv, a_gr, b_gr):
    eps = 0.001
    lab = (b - a).length()
    lcb = (b - c).length()
    lat = clamp((t - a).length(), eps, lab + lcb - eps)

    # Get current interior angles of start and mid
    ac_ab_0 = math.acos(clamp((c - a).normal() * (b - a).normal(), -1.0, 1.0))
    ba_bc_0 = math.acos(clamp((a - b).normal() * (c - b).normal(), -1.0, 1.0))
    ac_at_0 = math.acos(clamp((c - a).normal() * (t - a).normal(), -1.0, 1.0))

    # Get desired interior angles
    ac_ab_1 = math.acos(clamp((lcb * lcb - lab * lab - lat * lat) / (-2.0 * lab * lat), -1.0, 1.0))
    ba_bc_1 = math.acos(clamp((lat * lat - lab * lab - lcb * lcb) / (-2.0 * lab * lcb), -1.0, 1.0))

    # axis0 = ((c - a) ^ (b - a)).normal()
    axis0 = ((c - a) ^ d).normal()
    axis1 = ((c - a) ^ (t - a)).normal()

    r0 = OpenMaya.MQuaternion(ac_ab_1 - ac_ab_0, axis0)
    r1 = OpenMaya.MQuaternion(ba_bc_1 - ba_bc_0, axis0)
    r2 = OpenMaya.MQuaternion(ac_at_0, axis1)

    # pole vector
    n1 = ((c - a) ^ (b - a)).normal().rotateBy(r0).rotateBy(r2)
    n2 = ((t - a) ^ (pv - a)).normal()
    r3 = n1.rotateTo(n2)

    a_gr *= r0 * r2 * r3
    b_gr *= r1
    b_gr *= r0 * r2 * r3
    return a_gr, b_gr


path_hip = shortcuts.get_dag_path2("hip")
path_knee = shortcuts.get_dag_path2("knee")
hip = OpenMaya.MFnTransform(path_hip)
knee = OpenMaya.MFnTransform(path_knee)
foot = OpenMaya.MFnTransform(shortcuts.get_dag_path2("foot"))
pole = OpenMaya.MFnTransform(shortcuts.get_dag_path2("pv"))
target = OpenMaya.MFnTransform(shortcuts.get_dag_path2("target"))

local_knee = path_knee.inclusiveMatrix() * path_hip.inclusiveMatrixInverse()

space = OpenMaya.MSpace.kWorld
a = hip.translation(space)
b = knee.translation(space)
c = foot.translation(space)
t = target.translation(space)
pv = pole.translation(space)
# d = pv - ((a + t) * 0.5)
d = OpenMaya.MVector(0.0, 0.0, 1.0).normal()
a_gr = hip.rotation(space, asQuaternion=True)
b_gr = knee.rotation(space, asQuaternion=True)
a_gr, b_gr = two_bone_ik(a, b, c, d, t, pv, a_gr, b_gr)

hip.setRotation(a_gr, space)
knee.setRotation(b_gr, space)
knee_pos = local_knee * path_hip.inclusiveMatrix()
knee_pos = OpenMaya.MVector(knee_pos.getElement(3, 0), knee_pos.getElement(3, 1), knee_pos.getElement(3, 2))
knee.setTranslation(knee_pos, space)
"""
