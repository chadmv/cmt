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

    return node
