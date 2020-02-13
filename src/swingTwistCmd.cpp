#include "swingTwistCmd.h"
#include "swingTwistNode.h"

#include <maya/MDagPath.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnMatrixData.h>
#include <maya/MMatrix.h>
#include <maya/MPlug.h>

const char* SwingTwistCmd::kNameShort = "-n";
const char* SwingTwistCmd::kNameLong = "-name";
const char* SwingTwistCmd::kTwistShort = "-t";
const char* SwingTwistCmd::kTwistLong = "-twist";
const char* SwingTwistCmd::kSwingShort = "-s";
const char* SwingTwistCmd::kSwingLong = "-swing";
const char* SwingTwistCmd::kTwistAxisShort = "-ta";
const char* SwingTwistCmd::kTwistAxisLong = "-twistAxis";
const MString SwingTwistCmd::kName("swingTwist");

void* SwingTwistCmd::creator() { return new SwingTwistCmd; }

bool SwingTwistCmd::isUndoable() const { return true; }

MSyntax SwingTwistCmd::newSyntax() {
  MSyntax syntax;

  syntax.addFlag(kNameShort, kNameLong, MSyntax::kString);
  syntax.addFlag(kTwistShort, kTwistLong, MSyntax::kDouble);
  syntax.addFlag(kSwingShort, kSwingLong, MSyntax::kDouble);
  syntax.addFlag(kTwistAxisShort, kTwistAxisLong, MSyntax::kLong);

  syntax.setObjectType(MSyntax::kSelectionList, 2, 2);
  syntax.useSelectionAsDefault(true);

  syntax.enableEdit(false);
  syntax.enableQuery(false);

  return syntax;
}

MStatus SwingTwistCmd::doIt(const MArgList& argList) {
  MStatus status;
  // Read all the flag arguments
  MArgDatabase argData(syntax(), argList, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MSelectionList selection;
  status = argData.getObjects(selection);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Get the name
  if (argData.isFlagSet(kNameShort)) {
    name_ = argData.flagArgumentString(kNameShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  oNode_ = dgMod_.createNode(SwingTwistNode::id, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MDagPath pathDriver, pathDriven;
  selection.getDagPath(0, pathDriver);
  selection.getDagPath(1, pathDriven);

  MFnDagNode fnDriver(pathDriver, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MFnDagNode fnDriven(pathDriven, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Connect the matrix
  MPlug plugDriverMatrix(oNode_, SwingTwistNode::aInMatrix);
  MPlug plugMatrix = fnDriver.findPlug("matrix", false, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  dgMod_.connect(plugMatrix, plugDriverMatrix);

  // Set the driver rest matrix
  MMatrix driverRestMatrix = pathDriver.inclusiveMatrix() * pathDriver.exclusiveMatrixInverse();
  MPlug plugDriverRestMatrix(oNode_, SwingTwistNode::aRestMatrix);
  MFnMatrixData fnMatrixData;
  MObject oRestMatrix = fnMatrixData.create(driverRestMatrix, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  dgMod_.newPlugValue(plugDriverRestMatrix, oRestMatrix);

  // Set the target rest matrix
  MMatrix targetRestMatrix = pathDriven.inclusiveMatrix() * pathDriven.exclusiveMatrixInverse();
  MPlug plugDrivenRestMatrix(oNode_, SwingTwistNode::aTargetRestMatrix);
  MObject oTargetRestMatrix = fnMatrixData.create(targetRestMatrix, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  dgMod_.newPlugValue(plugDrivenRestMatrix, oTargetRestMatrix);

  // Set the twist
  if (argData.isFlagSet(kTwistShort)) {
    float twist = (float)(argData.flagArgumentDouble(kTwistShort, 0, &status));
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MPlug plugTwist(oNode_, SwingTwistNode::aTwistWeight);
    dgMod_.newPlugValueFloat(plugTwist, twist);
  }

  // Set the swing
  if (argData.isFlagSet(kSwingShort)) {
    float swing = (float)(argData.flagArgumentDouble(kSwingShort, 0, &status));
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MPlug plugSwing(oNode_, SwingTwistNode::aSwingWeight);
    dgMod_.newPlugValueFloat(plugSwing, swing);
  }

  // Set the twist axis
  if (argData.isFlagSet(kTwistAxisShort)) {
    short twistAxis = (short)(argData.flagArgumentInt(kTwistAxisShort, 0, &status));
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MPlug plugSwing(oNode_, SwingTwistNode::aTwistAxis);
    dgMod_.newPlugValueShort(plugSwing, twistAxis);
  }

  // Connect the output
#if MAYA_API_VERSION >= 20200000
  MPlug plugOutMatrix(oNode_, SwingTwistNode::aOutMatrix);
  MPlug plugOffsetParentMatrix = fnDriven.findPlug("offsetParentMatrix", false, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  dgMod_.connect(plugOutMatrix, plugOffsetParentMatrix);

  // Zero out any local xform values
  std::string attributes[] = {"translateX",
                              "translateY",
                              "translateZ",
                              "rotateX",
                              "rotateY",
                              "rotateZ"
                              "jointOrientX",
                              "jointOrientY",
                              "jointOrientZ"};
  for (auto attribute : attributes) {
    MPlug plug = fnDriven.findPlug(attribute.c_str(), false, &status);
    if (!MFAIL(status)) {
      dgMod_.newPlugValueDouble(plug, 0.0);
    }
  }
#endif

  return redoIt();
}

MStatus SwingTwistCmd::redoIt() {
  MStatus status;
  clearResult();
  status = dgMod_.doIt();
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MFnDependencyNode fnNode(oNode_, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  if (name_.length()) {
    name_ = fnNode.setName(name_, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  } else {
    name_ = fnNode.name();
  }

  setResult(name_);

  return MS::kSuccess;
}

MStatus SwingTwistCmd::undoIt() {
  MStatus status;

  status = dgMod_.undoIt();
  CHECK_MSTATUS_AND_RETURN_IT(status);

  return MS::kSuccess;
}
