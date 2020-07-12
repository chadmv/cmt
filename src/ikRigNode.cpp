#include "ikRigNode.h"

#include <maya/MAngle.h>
#include <maya/MEulerRotation.h>
#include <maya/MFloatVector.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MMatrix.h>
#include <maya/MQuaternion.h>
#include <maya/MTransformationMatrix.h>

#include "common.h"

MTypeId IKRigNode::id(0x0011581B);
MObject IKRigNode::aOutTranslate;
MObject IKRigNode::aOutRotate;
MObject IKRigNode::aOutRotateX;
MObject IKRigNode::aOutRotateY;
MObject IKRigNode::aOutRotateZ;
MObject IKRigNode::aInMatrix;
MObject IKRigNode::aInBindPreMatrix;
MObject IKRigNode::aTargetRestMatrix;
MObject IKRigNode::aLeftLegTwistOffset;
MObject IKRigNode::aRightLegTwistOffset;

const MString IKRigNode::kName("ikRig");

#define MATRIX_INPUT(obj, name)          \
  {                                      \
    obj = mAttr.create(name, name);      \
    addAttribute(obj);                   \
    mAttr.setArray(true);                \
    mAttr.setUsesArrayDataBuilder(true); \
    affects(obj);                        \
  }

MStatus IKRigNode::initialize() {
  MStatus status;

  MFnEnumAttribute eAttr;
  MFnMatrixAttribute mAttr;
  MFnNumericAttribute nAttr;
  MFnUnitAttribute uAttr;

  aOutTranslate = nAttr.createPoint("outputTranslate", "outputTranslate");
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  nAttr.setWritable(false);
  nAttr.setStorable(false);
  addAttribute(aOutTranslate);

  aOutRotateX = uAttr.create("outputRotateX", "outputRotateX", MFnUnitAttribute::kAngle);
  aOutRotateY = uAttr.create("outputRotateY", "outputRotateY", MFnUnitAttribute::kAngle);
  aOutRotateZ = uAttr.create("outputRotateZ", "outputRotateZ", MFnUnitAttribute::kAngle);
  aOutRotate = nAttr.create("outputRotate", "outputRotate", aOutRotateX, aOutRotateY, aOutRotateZ);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  nAttr.setWritable(false);
  nAttr.setStorable(false);
  addAttribute(aOutRotate);

  aLeftLegTwistOffset =
      nAttr.create("leftLegTwistOffset", "leftLegTwistOffset", MFnNumericData::kFloat, 0.0);
  nAttr.setKeyable(true);
  addAttribute(aLeftLegTwistOffset);
  affects(aLeftLegTwistOffset);

  aRightLegTwistOffset =
      nAttr.create("rightLegTwistOffset", "rightLegTwistOffset", MFnNumericData::kFloat, 0.0);
  nAttr.setKeyable(true);
  addAttribute(aRightLegTwistOffset);
  affects(aRightLegTwistOffset);

  MATRIX_INPUT(aInMatrix, "inMatrix");
  MATRIX_INPUT(aInBindPreMatrix, "inBindPreMatrix");
  MATRIX_INPUT(aTargetRestMatrix, "targetRestMatrix");

  return MS::kSuccess;
}

void IKRigNode::affects(const MObject& attribute) {
  attributeAffects(attribute, aOutTranslate);
  attributeAffects(attribute, aOutRotate);
  attributeAffects(attribute, aOutRotateX);
  attributeAffects(attribute, aOutRotateY);
  attributeAffects(attribute, aOutRotateZ);
}

void* IKRigNode::creator() { return new IKRigNode(); }

IKRigNode::IKRigNode() {
  inputMatrix_.setLength(IKRig_Count);
  inputBindPreMatrix_.setLength(IKRig_Count);
  targetRestMatrix_.setLength(IKRig_Count);
  outputDelta_.setLength(IKRig_Count);
}

IKRigNode::~IKRigNode() {}

MStatus IKRigNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutTranslate && plug != aOutRotate) {
    return MS::kUnknownParameter;
  }

  // Get the input skeleton
  MArrayDataHandle hInputMatrices = data.inputArrayValue(aInMatrix);
  MArrayDataHandle hInputBindPreMatrices = data.inputArrayValue(aInBindPreMatrix);
  MArrayDataHandle hOutputBindPreMatrices = data.inputArrayValue(aTargetRestMatrix);
  for (unsigned int i = 0; i < IKRig_Count; ++i) {
    status = JumpToElement(hInputMatrices, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    inputMatrix_[i] = hInputMatrices.inputValue().asMatrix();

    status = JumpToElement(hInputBindPreMatrices, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    inputBindPreMatrix_[i] = hInputBindPreMatrices.inputValue().asMatrix();

    status = JumpToElement(hOutputBindPreMatrices, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    targetRestMatrix_[i] = hOutputBindPreMatrices.inputValue().asMatrix();
  }

  // Calculate outputs
  for (unsigned int i = 0; i < IKRig_Count; ++i) {
    outputDelta_[i] = inputBindPreMatrix_[i] * inputMatrix_[i];
  }

  // Set outputs
  MArrayDataHandle hOutputTranslate = data.outputArrayValue(aOutTranslate);
  MArrayDataHandle hOutputRotate = data.outputArrayValue(aOutRotate);

  // Hips
  float hipScale = position(targetRestMatrix_[IKRig_Hips]).y /
                   position(inputBindPreMatrix_[IKRig_Hips].inverse()).y;
  outputDelta_[IKRig_Hips][3][0] *= hipScale;
  outputDelta_[IKRig_Hips][3][1] *= hipScale;
  outputDelta_[IKRig_Hips][3][2] *= hipScale;
  MMatrix hips = targetRestMatrix_[IKRig_Hips] * outputDelta_[IKRig_Hips];
  hips[3][0] = inputMatrix_[IKRig_Hips][3][0];
  hips[3][1] = inputMatrix_[IKRig_Hips][3][1] * hipScale;
  hips[3][2] = inputMatrix_[IKRig_Hips][3][2];
  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_Hips, hips);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Left leg
  float leftLegTwistOffset = data.inputValue(aLeftLegTwistOffset).asFloat();
  status = calculateLegIk(IKRig_LeftUpLeg, IKRig_LeftLoLeg, IKRig_LeftFoot, hips,
                          leftLegTwistOffset, hOutputTranslate, hOutputRotate);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Right leg
  float rightLegTwistOffset = data.inputValue(aRightLegTwistOffset).asFloat();
  status = calculateLegIk(IKRig_RightUpLeg, IKRig_RightLoLeg, IKRig_RightFoot, hips,
                          rightLegTwistOffset, hOutputTranslate, hOutputRotate);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  hOutputTranslate.setAllClean();
  hOutputRotate.setAllClean();

  return MS::kSuccess;
}

MStatus IKRigNode::calculateLegIk(unsigned int upLegIdx, unsigned int loLegIdx,
                                  unsigned int footIdx, const MMatrix& hips, float twist,
                                  MArrayDataHandle& hOutputTranslate,
                                  MArrayDataHandle& hOutputRotate) {
  MStatus status;

  MMatrix upLeg = targetRestMatrix_[upLegIdx] * targetRestMatrix_[IKRig_Hips].inverse() * hips;
  MMatrix loLeg = targetRestMatrix_[loLegIdx] * targetRestMatrix_[upLegIdx].inverse() * upLeg;
  MMatrix foot = targetRestMatrix_[footIdx] * targetRestMatrix_[loLegIdx].inverse() * loLeg;

  // Foot target
  // Account for differences in ankle height to help with ground contact
  float ankleHeightDelta =
      position(targetRestMatrix_[footIdx]).y - position(inputBindPreMatrix_[footIdx].inverse()).y;
  MMatrix footTarget;
  footTarget[3][1] = ankleHeightDelta;
  footTarget = inputBindPreMatrix_[footIdx].inverse() * footTarget * outputDelta_[footIdx];

  // Calculate leg ik
  MVector ia = position(inputBindPreMatrix_[upLegIdx].inverse());
  MVector ib = position(inputBindPreMatrix_[loLegIdx].inverse());
  MVector ic = position(inputBindPreMatrix_[footIdx].inverse());
  MVector iac = (ic - ia).normal();
  MVector twistAxis = position(footTarget) - position(upLeg);
  MVector pv = (ib - (ia + (iac * ((ib - ia) * iac)))).normal() * outputDelta_[upLegIdx];
  // Apply any twist offset
  MQuaternion tw(twist * 0.0174533, twistAxis);
  pv = pv.rotateBy(tw);
  pv += position(upLeg);
  MMatrix ikLeftUpLeg, ikLeftLoLeg;
  calculateTwoBoneIk(upLeg, loLeg, foot, footTarget, pv, ikLeftUpLeg, ikLeftLoLeg);

  MQuaternion leftFootRotOffset =
      MTransformationMatrix(targetRestMatrix_[footIdx] * inputBindPreMatrix_[footIdx]).rotation();
  MQuaternion leftFootInputRot = MTransformationMatrix(inputMatrix_[footIdx]).rotation();
  leftFootRotOffset *= leftFootInputRot;
  MMatrix ikLeftFootPos =
      targetRestMatrix_[footIdx] * targetRestMatrix_[loLegIdx].inverse() * ikLeftLoLeg;
  MTransformationMatrix tIkLeftFoot(ikLeftFootPos);
  tIkLeftFoot.setRotationQuaternion(leftFootRotOffset.x, leftFootRotOffset.y, leftFootRotOffset.z,
                                    leftFootRotOffset.w);
  MMatrix ikLeftFoot = tIkLeftFoot.asMatrix();

  status = setOutput(hOutputTranslate, hOutputRotate, upLegIdx, ikLeftUpLeg);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, loLegIdx, ikLeftLoLeg);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, footIdx, ikLeftFoot);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  return MS::kSuccess;
}

void IKRigNode::calculateTwoBoneIk(const MMatrix& root, const MMatrix& mid, const MMatrix& effector,
                                   const MMatrix& target, const MVector& pv, MMatrix& ikA,
                                   MMatrix& ikB) {
  MVector a = position(root);
  MVector b = position(mid);
  MVector c = position(effector);
  MVector t = position(target);
  MQuaternion a_gr = MTransformationMatrix(root).rotation();
  MQuaternion b_gr = MTransformationMatrix(mid).rotation();
  MVector ac = (c - a).normal();
  MVector d = (b - (a + (ac * ((b - a) * ac)))).normal();

  twoBoneIk(a, b, c, d, t, pv, a_gr, b_gr);

  ikA = a_gr.asMatrix();
  ikA[3][0] = a.x;
  ikA[3][1] = a.y;
  ikA[3][2] = a.z;
  ikB = b_gr.asMatrix();
  MMatrix midPos = mid * root.inverse() * ikA;
  ikB[3][0] = midPos[3][0];
  ikB[3][1] = midPos[3][1];
  ikB[3][2] = midPos[3][2];
}

// http://theorangeduck.com/page/simple-two-joint
void IKRigNode::twoBoneIk(const MVector& a, const MVector& b, const MVector& c, const MVector& d,
                          const MVector& t, const MVector& pv, MQuaternion& a_gr,
                          MQuaternion& b_gr) {
  float eps = 0.001f;
  float lab = (b - a).length();
  float lcb = (b - c).length();
  float lat = clamp((t - a).length(), eps, lab + lcb - eps);

  // Get current interior angles of start and mid
  float ac_ab_0 = acos(clamp((c - a).normal() * (b - a).normal(), -1.0f, 1.0f));
  float ba_bc_0 = acos(clamp((a - b).normal() * (c - b).normal(), -1.0f, 1.0f));
  float ac_at_0 = acos(clamp((c - a).normal() * (t - a).normal(), -1.0f, 1.0f));

  // Get desired interior angles
  float ac_ab_1 =
      acos(clamp((lcb * lcb - lab * lab - lat * lat) / (-2.0f * lab * lat), -1.0f, 1.0f));
  float ba_bc_1 =
      acos(clamp((lat * lat - lab * lab - lcb * lcb) / (-2.0f * lab * lcb), -1.0f, 1.0f));
  MVector axis0 = ((c - a) ^ d).normal();
  MVector axis1 = ((c - a) ^ (t - a)).normal();

  MQuaternion r0(ac_ab_1 - ac_ab_0, axis0);
  MQuaternion r1(ba_bc_1 - ba_bc_0, axis0);
  MQuaternion r2(ac_at_0, axis1);

  // Pole vector rotation
  // Determine the rotation used to rotate the normal of the triangle formed by
  // a.b.c post r0*r2 rotation to the normal of the triangle formed by triangle a.pv.t
  MVector n1 = ((c - a) ^ (b - a)).normal().rotateBy(r0).rotateBy(r2);
  MVector n2 = ((t - a) ^ (pv - a)).normal();
  MQuaternion r3 = n1.rotateTo(n2);

  a_gr *= r0 * r2 * r3;
  b_gr *= r1;
  // Since we are calculating in world space, apply the start rotations to the mid
  b_gr *= r0 * r2 * r3;
}

MStatus IKRigNode::setOutput(MArrayDataHandle& hOutputTranslate, MArrayDataHandle& hOutputRotate,
                             unsigned int bodyPart, const MMatrix& matrix) {
  MStatus status;
  MFloatVector position(matrix[3][0], matrix[3][1], matrix[3][2]);
  status = JumpToElement(hOutputTranslate, bodyPart);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MDataHandle hOutput = hOutputTranslate.outputValue();
  hOutput.setMFloatVector(position);
  hOutput.setClean();

  MEulerRotation r = MEulerRotation::decompose(matrix, MEulerRotation::kXYZ);
  MAngle rx(r.x);
  MAngle ry(r.y);
  MAngle rz(r.z);
  status = JumpToElement(hOutputRotate, bodyPart);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  hOutput = hOutputRotate.outputValue();

  MDataHandle hX = hOutput.child(aOutRotateX);
  MDataHandle hY = hOutput.child(aOutRotateY);
  MDataHandle hZ = hOutput.child(aOutRotateZ);
  hX.setMAngle(rx);
  hY.setMAngle(ry);
  hZ.setMAngle(rz);
  hX.setClean();
  hY.setClean();
  hZ.setClean();

  return MStatus::kSuccess;
}
