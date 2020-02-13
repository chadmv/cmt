#include "swingTwistNode.h"

#include <maya/MFloatVector.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MMatrix.h>
#include <maya/MQuaternion.h>
#include <maya/MTransformationMatrix.h>


MTypeId SwingTwistNode::id(0x00115819);
MObject SwingTwistNode::aOutMatrix;
MObject SwingTwistNode::aInMatrix;
MObject SwingTwistNode::aTargetRestMatrix;
MObject SwingTwistNode::aRestMatrix;
MObject SwingTwistNode::aTwistWeight;
MObject SwingTwistNode::aSwingWeight;
MObject SwingTwistNode::aTwistAxis;


const MString SwingTwistNode::kName("swingTwist");

MStatus SwingTwistNode::initialize() {
  MStatus status;

  MFnEnumAttribute eAttr;
  MFnMatrixAttribute mAttr;
  MFnNumericAttribute nAttr;

  aOutMatrix = mAttr.create("outMatrix", "outMatrix");
  mAttr.setWritable(false);
  mAttr.setStorable(false);
  addAttribute(aOutMatrix);

  aInMatrix = mAttr.create("driverMatrix", "driverMatrix");
  addAttribute(aInMatrix);
  attributeAffects(aInMatrix, aOutMatrix);

  aRestMatrix = mAttr.create("driverRestMatrix", "driverRestMatrix");
  addAttribute(aRestMatrix);
  attributeAffects(aRestMatrix, aOutMatrix);

  aTargetRestMatrix = mAttr.create("targetRestMatrix", "targetRestMatrix");
  addAttribute(aTargetRestMatrix);
  attributeAffects(aTargetRestMatrix, aOutMatrix);

  aTwistWeight = nAttr.create("twist", "twist", MFnNumericData::kFloat, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(-1.0);
  nAttr.setMax(1.0);
  addAttribute(aTwistWeight);
  attributeAffects(aTwistWeight, aOutMatrix);

  aSwingWeight = nAttr.create("swing", "swing", MFnNumericData::kFloat, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(-1.0);
  nAttr.setMax(1.0);
  addAttribute(aSwingWeight);
  attributeAffects(aSwingWeight, aOutMatrix);

  aTwistAxis = eAttr.create("twistAxis", "twistAxis");
  eAttr.setKeyable(true);
  eAttr.addField("X", 0);
  eAttr.addField("Y", 1);
  eAttr.addField("Z", 2);
  addAttribute(aTwistAxis);
  attributeAffects(aTwistAxis, aOutMatrix);

  return MS::kSuccess;
}


void* SwingTwistNode::creator() {
  return new SwingTwistNode(); 
}


SwingTwistNode::SwingTwistNode() {
}


SwingTwistNode::~SwingTwistNode() {
}


MStatus SwingTwistNode::compute(const MPlug &plug, MDataBlock &data) {
  MStatus status;

  if (plug != aOutMatrix) {
    return MS::kUnknownParameter;
  }

  // Get the input data
  MMatrix inMatrix = data.inputValue(aInMatrix).asMatrix();
  MMatrix targetRestMatrix = data.inputValue(aTargetRestMatrix).asMatrix();
  MMatrix restMatrix = data.inputValue(aRestMatrix).asMatrix();
  float twistWeight = data.inputValue(aTwistWeight).asFloat();
  float swingWeight = data.inputValue(aSwingWeight).asFloat();
  short twistAxis = data.inputValue(aTwistAxis).asShort();

  // By calculating the local matrix with the world and parent inverse, we automatically
  // take in to account whether the joint uses joint orient or not.
  MMatrix localMatrix = inMatrix * restMatrix.inverse();

  // Get the input rotation quaternion
  MQuaternion rotation = MTransformationMatrix(localMatrix).rotation();
  MQuaternion twist(rotation);

  // Get the reference twist vector
  switch (twistAxis) {
    case 0:
      twist.y = 0.0;
      twist.z = 0.0;
      break;
    case 1:
      twist.x = 0.0;
      twist.z = 0.0;
      break;
    case 2:
      twist.x = 0.0;
      twist.y = 0.0;
      break;
  }
  twist.normalizeIt();

  MQuaternion swing = twist.inverse() * rotation;

  if (twistWeight < 0.0f) {
    twist.invertIt();
    twistWeight = -twistWeight;
  }
  if (swingWeight < 0.0f) {
    swing.invertIt();
    swingWeight = -swingWeight;
  }

  // Scale by the input weights
  MQuaternion rest;
  swing = slerp(rest, swing, swingWeight);
  twist = slerp(rest, twist, twistWeight);
  
  MQuaternion outRotation = twist * swing;

  // Since this is meant to drive offsetParentMatrix, we need to put the rotation
  // in the space of the driven transform. If we don't multiply by the target's rest
  // matrix, the rotation would occur in the target's parent space
  MMatrix outMatrix = outRotation.asMatrix() * targetRestMatrix;

  MDataHandle hOut = data.outputValue(aOutMatrix);
  hOut.setMMatrix(outMatrix);
  hOut.setClean();

  return MS::kSuccess;
}
