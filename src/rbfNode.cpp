#include "rbfNode.h"
#include "common.h"

#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnGenericAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnNumericData.h>
#include <maya/MQuaternion.h>

MTypeId RBFNode::id(0x0011581A);
MObject RBFNode::aInputValues;
MObject RBFNode::aInputQuats;
MObject RBFNode::aInputValueCount;
MObject RBFNode::aOutputValueCount;
MObject RBFNode::aOutputValues;
MObject RBFNode::aOutputQuats;
MObject RBFNode::aRBFFunction;
MObject RBFNode::aRadius;
MObject RBFNode::aRegularization;
MObject RBFNode::aSamples;
MObject RBFNode::aSampleInputValues;
MObject RBFNode::aSampleInputQuats;
MObject RBFNode::aSampleOutputValues;
MObject RBFNode::aSampleOutputQuats;

const MString RBFNode::kName("rbf");

MStatus RBFNode::initialize() {
  MStatus status;

  MFnCompoundAttribute cAttr;
  MFnGenericAttribute gAttr;
  MFnEnumAttribute eAttr;
  MFnNumericAttribute nAttr;

  aOutputValues = nAttr.create("outputValue", "outputValue", MFnNumericData::kDouble);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  nAttr.setWritable(false);
  nAttr.setStorable(false);
  addAttribute(aOutputValues);

  aOutputQuats = nAttr.create("outputQuat", "outputQuat", MFnNumericData::k4Double);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  nAttr.setWritable(false);
  nAttr.setStorable(false);
  addAttribute(aOutputQuats);

  aInputValues = nAttr.create("inputValue", "inputValue", MFnNumericData::kDouble);
  nAttr.setKeyable(true);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(aInputValues);
  attributeAffects(aInputValues, aOutputValues);
  attributeAffects(aInputValues, aOutputQuats);

  aInputValueCount = nAttr.create("inputValueCount", "inputValueCount", MFnNumericData::kLong);
  addAttribute(aInputValueCount);
  attributeAffects(aInputValueCount, aOutputValues);
  attributeAffects(aInputValueCount, aOutputQuats);

  aOutputValueCount = nAttr.create("outputValueCount", "outputValueCount", MFnNumericData::kLong);
  addAttribute(aOutputValueCount);
  attributeAffects(aOutputValueCount, aOutputValues);
  attributeAffects(aOutputValueCount, aOutputQuats);

  aInputQuats = nAttr.create("inputQuat", "inputQuat", MFnNumericData::k4Double);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(aInputQuats);
  attributeAffects(aInputQuats, aOutputValues);
  attributeAffects(aInputQuats, aOutputQuats);

  aRBFFunction = eAttr.create("rbf", "rbf");
  eAttr.setKeyable(true);
  eAttr.addField("linear", 0);
  eAttr.addField("gaussian", 1);
  eAttr.addField("thin plate", 2);
  eAttr.addField("multi quadratic biharmonic", 3);
  eAttr.addField("inv multi quadratic biharmonic", 4);
  eAttr.addField("beckert wendland c2 basis", 5);
  addAttribute(aRBFFunction);
  attributeAffects(aRBFFunction, aOutputValues);
  attributeAffects(aRBFFunction, aOutputQuats);

  aRadius = nAttr.create("radius", "radius", MFnNumericData::kDouble, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRadius);
  attributeAffects(aRadius, aOutputValues);
  attributeAffects(aRadius, aOutputQuats);

  aRegularization = nAttr.create("regularization", "regularization", MFnNumericData::kDouble, 0.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRegularization);
  attributeAffects(aRegularization, aOutputValues);
  attributeAffects(aRegularization, aOutputQuats);

  aSampleInputValues =
      nAttr.create("sampleInputValue", "sampleInputValue", MFnNumericData::kDouble);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);

  aSampleInputQuats = nAttr.create("sampleInputQuat", "sampleInputQuat", MFnNumericData::k4Double);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);

  aSampleOutputValues =
      nAttr.create("sampleOutputValue", "sampleOutputValue", MFnNumericData::kDouble);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);

  aSampleOutputQuats =
      nAttr.create("sampleOutputQuat", "sampleOutputQuat", MFnNumericData::k4Double);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);

  aSamples = cAttr.create("sample", "sample");
  cAttr.setArray(true);
  cAttr.setUsesArrayDataBuilder(true);
  cAttr.addChild(aSampleInputValues);
  cAttr.addChild(aSampleInputQuats);
  cAttr.addChild(aSampleOutputValues);
  cAttr.addChild(aSampleOutputQuats);
  addAttribute(aSamples);
  attributeAffects(aSamples, aOutputValues);
  attributeAffects(aSamples, aOutputQuats);
  attributeAffects(aSampleInputValues, aOutputValues);
  attributeAffects(aSampleInputValues, aOutputQuats);
  attributeAffects(aSampleInputQuats, aOutputValues);
  attributeAffects(aSampleInputQuats, aOutputQuats);
  attributeAffects(aSampleOutputValues, aOutputValues);
  attributeAffects(aSampleOutputValues, aOutputQuats);
  attributeAffects(aSampleOutputQuats, aOutputValues);
  attributeAffects(aSampleOutputQuats, aOutputQuats);

  return MS::kSuccess;
}

void* RBFNode::creator() { return new RBFNode(); }

RBFNode::RBFNode() {}

RBFNode::~RBFNode() {}

MStatus RBFNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutputValues && plug != aOutputQuats) {
    return MS::kUnknownParameter;
  }

  short rbf = data.inputValue(aRBFFunction).asShort();
  double regularization = data.inputValue(aRegularization).asDouble();
  double radius = data.inputValue(aRadius).asDouble();
  int inputCount = data.inputValue(aInputValueCount).asLong();
  int outputCount = data.inputValue(aOutputValueCount).asLong();

  // Get the inputs
  MArrayDataHandle hInputs = data.inputArrayValue(aInputValues);
  VectorXd inputs;
  status = getDoubleValues(hInputs, inputCount, inputs);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  // Build the feature matrix
  MArrayDataHandle hSamples = data.inputArrayValue(aSamples);
  unsigned int sampleCount = hSamples.elementCount();
  MatrixXd featureMatrix(sampleCount, inputCount);
  MatrixXd outputMatrix(sampleCount, outputCount);
  // TODO: support quaternion input/output

  std::vector<std::vector<MQuaternion>> outputQuatMatrix;
  for (unsigned int i = 0; i < sampleCount; ++i) {
    status = hSamples.jumpToArrayElement(i);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    MDataHandle hSample = hSamples.inputValue(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    MArrayDataHandle hInputValues = hSample.child(aSampleInputValues);
    VectorXd values;
    status = getDoubleValues(hInputValues, inputCount, values);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    featureMatrix.row(i) = values;

    MArrayDataHandle hOutputValues = hSample.child(aSampleOutputValues);
    status = getDoubleValues(hOutputValues, outputCount, values);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    outputMatrix.row(i) = values;
  }
  // Generate distance matrix from feature matrix
  // Generate distance vector from inputs
  MatrixXd m(sampleCount, sampleCount);
  VectorXd inputDistance(sampleCount);
  for (int i = 0; i < sampleCount; ++i) {
    m.col(i) = (featureMatrix.rowwise() - featureMatrix.row(i)).matrix().rowwise().norm();
    inputDistance[i] = (featureMatrix.row(i).transpose() - inputs).norm();
  }

  // TODO: Normalize each column separately
  double maxValue = m.maxCoeff();
  m /= maxValue;
  inputDistance /= maxValue;
  applyRbf(m, rbf, radius);
  applyRbf(inputDistance, rbf, radius);

  MatrixXd r = MatrixXd::Zero(sampleCount, sampleCount);
  r.diagonal().array() = regularization;

  MatrixXd tm = m.transpose();
  MatrixXd mat = pseudoInverse(tm * m + r) * tm;
  MatrixXd theta = (mat * outputMatrix).transpose();
  VectorXd output = theta * inputDistance;

  MDataHandle hOutput;
  MArrayDataHandle hOutputs = data.outputArrayValue(aOutputValues);
  for (unsigned int i = 0; i < outputCount; ++i) {
    status = JumpToElement(hOutputs, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    hOutput = hOutputs.outputValue();
    hOutput.setDouble(output[i]);
  }
  hOutputs.setAllClean();

  return MS::kSuccess;
}

MStatus RBFNode::getDoubleValues(MArrayDataHandle& hArray, int count, VectorXd& values) {
  MStatus status;
  values.resize(count);
  for (int i = 0; i < count; ++i) {
    status = JumpToElement(hArray, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    values[i] = hArray.inputValue().asDouble();
  }
  return MS::kSuccess;
}

MStatus RBFNode::getQuaternionValues(MArrayDataHandle& hArray, int count,
                                     std::vector<MQuaternion>& quaternions) {
  MStatus status;
  quaternions.resize(count);
  for (int i = 0; i < count; ++i) {
    status = JumpToElement(hArray, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MObject oData = hArray.inputValue().data();
    MFnNumericData fnData(oData, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MQuaternion q;
    fnData.getData4Double(q.x, q.y, q.z, q.w);
    quaternions[i] = q;
  }
  return MS::kSuccess;
}

MatrixXd RBFNode::pseudoInverse(const MatrixXd& a, double epsilon) {
  Eigen::JacobiSVD<MatrixXd> svd(a, Eigen::ComputeThinU | Eigen::ComputeThinV);
  double tolerance = epsilon * std::max(a.cols(), a.rows()) * svd.singularValues().array().abs()(0);
  return svd.matrixV() *
         (svd.singularValues().array().abs() > tolerance)
             .select(svd.singularValues().array().inverse(), 0)
             .matrix()
             .asDiagonal() *
         svd.matrixU().adjoint();
}

/*
for i in range(4):
    cube = "pCube{}".format(i+1)
    cmds.connectAttr("{}.tx".format(cube), "rbf1.sample[{}].inputValues[0]".format(i))
    cmds.connectAttr("{}.ty".format(cube), "rbf1.sample[{}].inputValues[1]".format(i))
    cmds.connectAttr("{}.tz".format(cube), "rbf1.sample[{}].inputValues[2]".format(i))
    cmds.connectAttr("{}.sx".format(cube), "rbf1.sample[{}].outputValues[0]".format(i))
    cmds.connectAttr("{}.sy".format(cube), "rbf1.sample[{}].outputValues[1]".format(i))
    cmds.connectAttr("{}.sz".format(cube), "rbf1.sample[{}].outputValues[2]".format(i))
cmds.connectAttr("rbf1.output[0]", "pCube5.sx")
cmds.connectAttr("rbf1.output[1]", "pCube5.sy")
cmds.connectAttr("rbf1.output[2]", "pCube5.sz")
*/