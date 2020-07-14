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

#include <array>

#include "common.h"

MTypeId IKRigNode::id(0x0011581B);
MObject IKRigNode::aOutTranslate;
MObject IKRigNode::aOutRotate;
MObject IKRigNode::aOutRotateX;
MObject IKRigNode::aOutRotateY;
MObject IKRigNode::aOutRotateZ;
MObject IKRigNode::aOutRootMotion;
MObject IKRigNode::aInMatrix;
MObject IKRigNode::aInBindPreMatrix;
MObject IKRigNode::aTargetRestMatrix;
MObject IKRigNode::aLeftLegTwistOffset;
MObject IKRigNode::aRightLegTwistOffset;
MObject IKRigNode::aStrideScale;
MObject IKRigNode::aRootMotionScale;

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

  aOutRootMotion = mAttr.create("rootMotion", "rootMotion");
  mAttr.setWritable(false);
  mAttr.setStorable(false);
  addAttribute(aOutRootMotion);

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

  aStrideScale = nAttr.create("strideScale", "strideScale", MFnNumericData::kFloat, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aStrideScale);
  affects(aStrideScale);

  aRootMotionScale =
      nAttr.create("rootMotionScale", "rootMotionScale", MFnNumericData::kFloat, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRootMotionScale);
  affects(aRootMotionScale);

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
  attributeAffects(attribute, aOutRootMotion);
}

void* IKRigNode::creator() { return new IKRigNode(); }

IKRigNode::IKRigNode() : strideScale_(1.0), spineScale_(1.0), hipScale_(1.0) {
  inputMatrix_.setLength(IKRig_Count);
  inputBindPreMatrix_.setLength(IKRig_Count);
  targetRestMatrix_.setLength(IKRig_Count);
  outputDelta_.setLength(IKRig_Count);
  prevForward_.push(MVector::zAxis);
  prevForward_.push(MVector::zAxis);
}

IKRigNode::~IKRigNode() {}

MStatus IKRigNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutTranslate && plug != aOutRotate && plug != aOutRootMotion) {
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

  rootMotionScale_ = data.inputValue(aRootMotionScale).asFloat();
  strideScale_ = data.inputValue(aStrideScale).asFloat();

  // Calculate outputs
  for (unsigned int i = 0; i < IKRig_Count; ++i) {
    outputDelta_[i] = inputBindPreMatrix_[i] * inputMatrix_[i];
  }

  // Calculate Root Motion
  rootMotion_ = calculateRootMotion();
  scaledRootMotion_ = rootMotion_;
  scaledRootMotion_[3][0] *= rootMotionScale_;
  scaledRootMotion_[3][2] *= rootMotionScale_;
  toScaledRootMotion_ = rootMotion_.inverse() * scaledRootMotion_;
  MDataHandle hRootMotion = data.outputValue(aOutRootMotion);
  hRootMotion.setMMatrix(scaledRootMotion_);
  hRootMotion.setClean();

  // Set outputs
  MArrayDataHandle hOutputTranslate = data.outputArrayValue(aOutTranslate);
  MArrayDataHandle hOutputRotate = data.outputArrayValue(aOutRotate);

  // Hips
  hipScale_ = position(targetRestMatrix_[IKRig_Hips]).y /
              position(inputBindPreMatrix_[IKRig_Hips].inverse()).y;
  outputDelta_[IKRig_Hips][3][1] *= hipScale_;
  MMatrix hips = targetRestMatrix_[IKRig_Hips] * outputDelta_[IKRig_Hips];
  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_Hips, hips * toScaledRootMotion_);
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

  // Chest
  float targetSpineLength =
      position(targetRestMatrix_[IKRig_Chest]).y - position(targetRestMatrix_[IKRig_Hips]).y;
  float inputSpineLength = position(inputBindPreMatrix_[IKRig_Chest].inverse()).y -
                           position(inputBindPreMatrix_[IKRig_Hips].inverse()).y;
  // Scale the local xform translation delta of the of the chest based on the spine length ratio
  spineScale_ = targetSpineLength / inputSpineLength;
  MMatrix inputRestLocalChest =
      inputBindPreMatrix_[IKRig_Chest].inverse() * inputBindPreMatrix_[IKRig_Hips];
  MMatrix inputCurrentLocalChest = inputMatrix_[IKRig_Chest] * inputMatrix_[IKRig_Hips].inverse();
  MMatrix localDelta = inputRestLocalChest.inverse() * inputCurrentLocalChest;
  localDelta[3][0] *= spineScale_;
  localDelta[3][1] *= spineScale_;
  localDelta[3][2] *= spineScale_;
  outputDelta_[IKRig_Chest] = inputBindPreMatrix_[IKRig_Chest] * inputRestLocalChest * localDelta *
                              inputMatrix_[IKRig_Hips];

  MMatrix chest = targetRestMatrix_[IKRig_Chest] * outputDelta_[IKRig_Chest];
  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_Chest, chest * toScaledRootMotion_);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Left arm
  status = calculateArmIk(IKRig_LeftClavicle, IKRig_LeftShoulder, IKRig_LeftElbow, IKRig_LeftHand,
                          chest, 0.0f, hOutputTranslate, hOutputRotate);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Right arm
  status = calculateArmIk(IKRig_RightClavicle, IKRig_RightShoulder, IKRig_RightElbow,
                          IKRig_RightHand, chest, 0.0f, hOutputTranslate, hOutputRotate);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  hOutputTranslate.setAllClean();
  hOutputRotate.setAllClean();

  return MS::kSuccess;
}

MMatrix IKRigNode::calculateRootMotion() {
  std::array<int, 4> rootInfluenceIndex = {IKRig_Hips, IKRig_Chest, IKRig_LeftUpLeg,
                                           IKRig_RightUpLeg};
  double weights[] = {0.5, 0.3, 0.1, 0.1};
  MVector rootMotionTranslate;
  int col = 0;
  MVector forward;
  for (const auto& i : rootInfluenceIndex) {
    MQuaternion q = MTransformationMatrix(outputDelta_[i]).rotation();
    forward += MVector::zAxis.rotateBy(q) * weights[col];

    rootMotionTranslate +=
        MTransformationMatrix(inputMatrix_[i]).translation(MSpace::kWorld) * weights[col];
    ++col;
  }
  forward.y = 0.0;
  forward.normalize();

  // Average with previous two forward vectors
  forward += prevForward_.front();
  prevForward_.pop();
  forward += prevForward_.front();
  forward.normalize();
  prevForward_.push(forward);

  MVector x = forward ^ MVector::yAxis;
  MMatrix m;
  m[0][0] = x.x;
  m[0][1] = x.y;
  m[0][2] = x.z;
  m[1][0] = 0.0;
  m[1][1] = 1.0;
  m[1][2] = 0.0;
  m[2][0] = forward.x;
  m[2][1] = forward.y;
  m[2][2] = forward.z;
  m[3][0] = rootMotionTranslate.x;
  m[3][1] = 0.0;
  m[3][2] = rootMotionTranslate.z;
  return m;
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
  footTarget *= rootMotion_.inverse();
  footTarget[3][0] *= hipScale_ * strideScale_;
  footTarget[3][1] *= hipScale_;
  footTarget[3][2] *= hipScale_ * strideScale_;
  footTarget *= rootMotion_;

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
  MMatrix ikUpLeg, ikLoLeg;
  calculateTwoBoneIk(upLeg, loLeg, foot, footTarget, pv, ikUpLeg, ikLoLeg);

  MQuaternion footRotOffset =
      MTransformationMatrix(targetRestMatrix_[footIdx] * inputBindPreMatrix_[footIdx]).rotation();
  MQuaternion footInputRot = MTransformationMatrix(inputMatrix_[footIdx]).rotation();
  footRotOffset *= footInputRot;
  MMatrix ikFootPos = targetRestMatrix_[footIdx] * targetRestMatrix_[loLegIdx].inverse() * ikLoLeg;
  MTransformationMatrix tIkFoot(ikFootPos);
  tIkFoot.setRotationQuaternion(footRotOffset.x, footRotOffset.y, footRotOffset.z, footRotOffset.w);
  MMatrix ikFoot = tIkFoot.asMatrix();

  ikUpLeg *= toScaledRootMotion_;
  ikLoLeg *= toScaledRootMotion_;
  ikFoot *= toScaledRootMotion_;

  status = setOutput(hOutputTranslate, hOutputRotate, upLegIdx, ikUpLeg);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, loLegIdx, ikLoLeg);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, footIdx, ikFoot);
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

MStatus IKRigNode::calculateArmIk(unsigned int clavicleIdx, unsigned int upArmIdx,
                                  unsigned int loArmIdx, unsigned int handIdx, const MMatrix& chest,
                                  float twist, MArrayDataHandle& hOutputTranslate,
                                  MArrayDataHandle& hOutputRotate) {
  MStatus status;

  MQuaternion clavicleOffset = MTransformationMatrix(targetRestMatrix_[clavicleIdx]).rotation() *
                               MTransformationMatrix(inputBindPreMatrix_[clavicleIdx]).rotation();
  MQuaternion clavicleRotation =
      clavicleOffset * MTransformationMatrix(inputMatrix_[clavicleIdx]).rotation();
  MPoint claviclePosition =
      MTransformationMatrix(targetRestMatrix_[clavicleIdx]).translation(MSpace::kWorld);
  claviclePosition *= targetRestMatrix_[IKRig_Chest].inverse() * chest;
  MMatrix clavicle = clavicleRotation.asMatrix();
  clavicle[3][0] = claviclePosition.x;
  clavicle[3][1] = claviclePosition.y;
  clavicle[3][2] = claviclePosition.z;

  MMatrix upArm = targetRestMatrix_[upArmIdx] * targetRestMatrix_[clavicleIdx].inverse() * clavicle;
  MMatrix loArm = targetRestMatrix_[loArmIdx] * targetRestMatrix_[upArmIdx].inverse() * upArm;
  MMatrix hand = targetRestMatrix_[handIdx] * targetRestMatrix_[loArmIdx].inverse() * loArm;

  // Hand target
  // Account for differences in arm length
  float targetArmLength =
      (position(targetRestMatrix_[loArmIdx]) - position(targetRestMatrix_[upArmIdx])).length() +
      (position(targetRestMatrix_[handIdx]) - position(targetRestMatrix_[loArmIdx])).length();
  float inArmLength = (position(inputBindPreMatrix_[loArmIdx].inverse()) -
                       position(inputBindPreMatrix_[upArmIdx].inverse()))
                          .length() +
                      (position(inputBindPreMatrix_[handIdx].inverse()) -
                       position(inputBindPreMatrix_[loArmIdx].inverse()))
                          .length();

  float armScale = targetArmLength / inArmLength;
  MVector armOffset =
      (position(inputMatrix_[handIdx]) - position(inputMatrix_[upArmIdx])) * armScale;

  MMatrix handTarget = upArm;
  handTarget[3][0] += armOffset.x;
  handTarget[3][1] += armOffset.y;
  handTarget[3][2] += armOffset.z;

  // Calculate arm ik
  MVector ia = position(inputBindPreMatrix_[upArmIdx].inverse());
  MVector ib = position(inputBindPreMatrix_[loArmIdx].inverse());
  MVector ic = position(inputBindPreMatrix_[handIdx].inverse());
  MVector iac = (ic - ia).normal();
  MVector twistAxis = position(handTarget) - position(upArm);
  MVector pv = (ib - (ia + (iac * ((ib - ia) * iac)))).normal() * outputDelta_[upArmIdx];
  // Apply any twist offset
  MQuaternion tw(twist * 0.0174533, twistAxis);
  pv = pv.rotateBy(tw);
  pv += position(upArm);
  MMatrix ikUpArm, ikLoArm;
  calculateTwoBoneIk(upArm, loArm, hand, handTarget, pv, ikUpArm, ikLoArm);

  // Hand rotation
  MQuaternion handOffset = MTransformationMatrix(targetRestMatrix_[handIdx]).rotation() *
                           MTransformationMatrix(inputBindPreMatrix_[handIdx]).rotation();
  MQuaternion handRotation = handOffset * MTransformationMatrix(inputMatrix_[handIdx]).rotation();
  MMatrix ikHandPos = targetRestMatrix_[handIdx] * targetRestMatrix_[loArmIdx].inverse() * ikLoArm;
  MTransformationMatrix tIkHand(ikHandPos);
  tIkHand.setRotationQuaternion(handRotation.x, handRotation.y, handRotation.z, handRotation.w);
  MMatrix ikHand = tIkHand.asMatrix();

  clavicle *= toScaledRootMotion_;
  ikUpArm *= toScaledRootMotion_;
  ikLoArm *= toScaledRootMotion_;
  ikHand *= toScaledRootMotion_;

  status = setOutput(hOutputTranslate, hOutputRotate, clavicleIdx, clavicle);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, upArmIdx, ikUpArm);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, loArmIdx, ikLoArm);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, handIdx, ikHand);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  return MS::kSuccess;
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
