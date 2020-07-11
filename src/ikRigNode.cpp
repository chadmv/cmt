#include "ikRigNode.h"

#include <maya/MAngle.h>
#include <maya/MEulerRotation.h>
#include <maya/MFloatVector.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MMatrix.h>
#include <maya/MMatrixArray.h>
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

IKRigNode::IKRigNode() {}

IKRigNode::~IKRigNode() {}

MStatus IKRigNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutTranslate && plug != aOutRotate) {
    return MS::kUnknownParameter;
  }

  // Get the input skeleton
  MMatrixArray inputMatrix(IKRig_Count);
  MMatrixArray inputBindPreMatrix(IKRig_Count);
  MMatrixArray targetRestMatrix(IKRig_Count);
  MArrayDataHandle hInputMatrices = data.inputArrayValue(aInMatrix);
  MArrayDataHandle hInputBindPreMatrices = data.inputArrayValue(aInBindPreMatrix);
  MArrayDataHandle hOutputBindPreMatrices = data.inputArrayValue(aTargetRestMatrix);
  for (unsigned int i = 0; i < IKRig_Count; ++i) {
    status = JumpToElement(hInputMatrices, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    inputMatrix[i] = hInputMatrices.inputValue().asMatrix();

    status = JumpToElement(hInputBindPreMatrices, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    inputBindPreMatrix[i] = hInputBindPreMatrices.inputValue().asMatrix();

    status = JumpToElement(hOutputBindPreMatrices, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    targetRestMatrix[i] = hOutputBindPreMatrices.inputValue().asMatrix();
  }

  // Calculate outputs
  MMatrixArray outputDelta(IKRig_Count);
  for (unsigned int i = 0; i < IKRig_Count; ++i) {
    outputDelta[i] = inputBindPreMatrix[i] * inputMatrix[i];
  }

  // Set outputs
  MArrayDataHandle hOutputTranslate = data.outputArrayValue(aOutTranslate);
  MArrayDataHandle hOutputRotate = data.outputArrayValue(aOutRotate);

  // Hips
  float hipScale = position(targetRestMatrix[IKRig_Hips]).y /
                   position(inputBindPreMatrix[IKRig_Hips].inverse()).y;
  outputDelta[IKRig_Hips][3][0] *= hipScale;
  outputDelta[IKRig_Hips][3][1] *= hipScale;
  outputDelta[IKRig_Hips][3][2] *= hipScale;
  MMatrix hips = targetRestMatrix[IKRig_Hips] * outputDelta[IKRig_Hips];
  hips[3][0] = inputMatrix[IKRig_Hips][3][0];
  hips[3][1] = inputMatrix[IKRig_Hips][3][1] * hipScale;
  hips[3][2] = inputMatrix[IKRig_Hips][3][2];
  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_Hips, hips);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Left leg
  MMatrix leftUpLeg =
      targetRestMatrix[IKRig_LeftUpLeg] * targetRestMatrix[IKRig_Hips].inverse() * hips;
  MMatrix leftLoLeg =
      targetRestMatrix[IKRig_LeftLoLeg] * targetRestMatrix[IKRig_LeftUpLeg].inverse() * leftUpLeg;
  MMatrix leftFoot =
      targetRestMatrix[IKRig_LeftFoot] * targetRestMatrix[IKRig_LeftLoLeg].inverse() * leftLoLeg;

  // Left foot target
  float leftAnkleHeightDelta = position(targetRestMatrix[IKRig_LeftFoot]).y -
                               position(inputBindPreMatrix[IKRig_LeftFoot].inverse()).y;
  MMatrix leftFootTarget;
  leftFootTarget[3][1] = leftAnkleHeightDelta;
  leftFootTarget = inputBindPreMatrix[IKRig_LeftFoot].inverse() * leftFootTarget * outputDelta[IKRig_LeftFoot];
  /*MVector leftFootOffset =
      (position(leftUpLeg) - position(leftFoot)).normal() * leftAnkleHeightDelta;
  leftFootTarget[3][0] = inputMatrix[IKRig_LeftFoot][3][0] + leftFootOffset.x;
  leftFootTarget[3][1] = inputMatrix[IKRig_LeftFoot][3][1] + leftFootOffset.y;
  leftFootTarget[3][2] = inputMatrix[IKRig_LeftFoot][3][2] + leftFootOffset.z;*/

  // Calculate left leg ik
  MVector a = position(leftUpLeg);
  MVector b = position(leftLoLeg);
  MVector c = position(leftFoot);
  MVector t = position(leftFootTarget);
  MQuaternion a_gr = MTransformationMatrix(leftUpLeg).rotation();
  MQuaternion b_gr = MTransformationMatrix(leftLoLeg).rotation();
  MVector ac = c - a;
  MVector d = b - (a + ((b - a) * ac) / (ac * ac) * ac);
  twoBoneIk(a, b, c, d, t, a_gr, b_gr);

  leftUpLeg = a_gr.asMatrix();
  leftUpLeg[3][0] = a.x;
  leftUpLeg[3][1] = a.y;
  leftUpLeg[3][2] = a.z;
  MMatrix leftKnee = b_gr.asMatrix();
  MMatrix leftkneePos =
      targetRestMatrix[IKRig_LeftLoLeg] * targetRestMatrix[IKRig_LeftUpLeg].inverse() * leftUpLeg;
  leftKnee[3][0] = leftkneePos[3][0];
  leftKnee[3][1] = leftkneePos[3][1];
  leftKnee[3][2] = leftkneePos[3][2];

  leftFoot =
      targetRestMatrix[IKRig_LeftFoot] * targetRestMatrix[IKRig_LeftLoLeg].inverse() * leftKnee;

  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_LeftUpLeg, leftUpLeg);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_LeftLoLeg, leftKnee);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = setOutput(hOutputTranslate, hOutputRotate, IKRig_LeftFoot, leftFoot);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  hOutputTranslate.setAllClean();
  hOutputRotate.setAllClean();

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

// http://theorangeduck.com/page/simple-two-joint
void IKRigNode::twoBoneIk(const MVector& a, const MVector& b, const MVector& c, const MVector& d,
                          const MVector& t, MQuaternion& a_gr, MQuaternion& b_gr) {
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
  std::cerr << "ba_bc_0 = " << ba_bc_0 * 57.2958f << " ba_bc_1 = " << ba_bc_1 * 57.2958f
            << std::endl;
  MVector axis0 = ((c - a) ^ (b - a)).normal();
  //MVector axis0 = ((c - a) ^ d).normal();
  MVector axis1 = ((c - a) ^ (t - a)).normal();

  MQuaternion r0(ac_ab_1 - ac_ab_0, axis0);
  MQuaternion r1(ba_bc_1 - ba_bc_0, axis0);
  MQuaternion r2(ac_at_0, axis1);

  a_gr *= r0 * r2;
  b_gr *= r1;
  b_gr *= r0 * r2;
}
