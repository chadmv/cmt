#include "rbfNode.h"
#include "common.h"

#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnGenericAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnNumericData.h>
#include <maya/MQuaternion.h>

MTypeId RBFNode::id(0x0011581A);
MObject RBFNode::aInputs;
MObject RBFNode::aOutputs;
MObject RBFNode::aRBFFunction;
MObject RBFNode::aRadius;
MObject RBFNode::aRegularization;
MObject RBFNode::aSamples;
MObject RBFNode::aInputValues;
MObject RBFNode::aOutputValues;

const MString RBFNode::kName("rbf");

MStatus RBFNode::initialize() {
  MStatus status;

  MFnCompoundAttribute cAttr;
  MFnGenericAttribute gAttr;
  MFnEnumAttribute eAttr;
  MFnNumericAttribute nAttr;

  aOutputs = gAttr.create("output", "output");
  gAttr.setArray(true);
  gAttr.setUsesArrayDataBuilder(true);
  gAttr.setWritable(false);
  gAttr.setStorable(false);
  gAttr.addNumericDataAccept(MFnNumericData::kDouble);
  gAttr.addNumericDataAccept(MFnNumericData::k4Double);
  addAttribute(aOutputs);

  aInputs = gAttr.create("input", "input");
  gAttr.setArray(true);
  gAttr.setUsesArrayDataBuilder(true);
  gAttr.addNumericDataAccept(MFnNumericData::kDouble);
  gAttr.addNumericDataAccept(MFnNumericData::k4Double);
  addAttribute(aInputs);
  attributeAffects(aInputs, aOutputs);

  aRBFFunction = eAttr.create("rbf", "rbf");
  eAttr.setKeyable(true);
  eAttr.addField("linear", 0);
  eAttr.addField("gaussian", 1);
  eAttr.addField("thin plate", 2);
  eAttr.addField("multi quadratic biharmonic", 3);
  eAttr.addField("inv multi quadratic biharmonic", 4);
  eAttr.addField("beckert wendland c2 basis", 5);
  addAttribute(aRBFFunction);
  attributeAffects(aRBFFunction, aOutputs);

  aRadius = nAttr.create("radius", "radius", MFnNumericData::kDouble, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRadius);
  attributeAffects(aRadius, aOutputs);

  aRegularization = nAttr.create("regularization", "regularization", MFnNumericData::kDouble, 0.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRegularization);
  attributeAffects(aRegularization, aOutputs);

  aInputValues = gAttr.create("inputValues", "inputValues");
  gAttr.setArray(true);
  gAttr.setUsesArrayDataBuilder(true);
  gAttr.addNumericDataAccept(MFnNumericData::kDouble);
  gAttr.addNumericDataAccept(MFnNumericData::k4Double);
  gAttr.addDataAccept(MFnData::kMatrix);

  aOutputValues = gAttr.create("outputValues", "outputValues");
  gAttr.setArray(true);
  gAttr.setUsesArrayDataBuilder(true);
  gAttr.addNumericDataAccept(MFnNumericData::kDouble);
  gAttr.addNumericDataAccept(MFnNumericData::k4Double);
  addAttribute(aOutputs);

  aSamples = cAttr.create("sample", "sample");
  cAttr.setArray(true);
  cAttr.setUsesArrayDataBuilder(true);
  cAttr.addChild(aInputValues);
  cAttr.addChild(aOutputValues);
  addAttribute(aSamples);
  attributeAffects(aSamples, aOutputs);
  attributeAffects(aInputValues, aOutputs);
  attributeAffects(aOutputValues, aOutputs);

  return MS::kSuccess;
}

void* RBFNode::creator() { return new RBFNode(); }

RBFNode::RBFNode() {}

RBFNode::~RBFNode() {}

MStatus RBFNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutputs) {
    return MS::kUnknownParameter;
  }

  short rbf = data.inputValue(aRBFFunction).asShort();
  double regularization = data.inputValue(aRegularization).asDouble();
  double radius = data.inputValue(aRadius).asDouble();

  // Get the inputs
  MArrayDataHandle hInputs = data.inputArrayValue(aInputs);
  unsigned int inputCount = hInputs.elementCount();
  std::vector<double> values;
  std::vector<MQuaternion> quaternions;
  status = getGenericValues(hInputs, values, quaternions);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  VectorXd inputs = VectorXd::Map(values.data(), values.size());

  // Build the feature matrix
  MArrayDataHandle hSamples = data.inputArrayValue(aSamples);
  unsigned int sampleCount = hSamples.elementCount();
  MatrixXd featureMatrix(sampleCount, inputCount);
  /// TODO: support quaternion input/output
  std::vector<std::vector<MQuaternion>> outputQuatMatrix;
  std::vector<VectorXd> outputValueMatrix;
  for (unsigned int i = 0; i < sampleCount; ++i) {
    status = hSamples.jumpToArrayElement(i);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    MDataHandle hSample = hSamples.inputValue(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    MArrayDataHandle hInputValues = hSample.child(aInputValues);
    status = getGenericValues(hInputValues, values, quaternions);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    VectorXd featureValues = VectorXd::Map(values.data(), values.size());
    featureMatrix.row(i) = featureValues;

    MArrayDataHandle hOutputValues = hSample.child(aOutputValues);
    status = getGenericValues(hOutputValues, values, quaternions);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    if (values.size()) {
      VectorXd outputValues = VectorXd::Map(values.data(), values.size());
      outputValueMatrix.push_back(outputValues);
    }
    if (quaternions.size()) {
      outputQuatMatrix.push_back(quaternions);
    }
  }

  MatrixXd outputMatrix;
  if (outputValueMatrix.size()) {
    outputMatrix.resize(outputValueMatrix.size(), outputValueMatrix[0].size());
    for (size_t i = 0; i < outputValueMatrix.size(); ++i) {
      outputMatrix.row(i) = outputValueMatrix[i];
    }
  }

  // Generate distance matrix from feature matrix
  // Generate distance vector from inputs
  MatrixXd m(sampleCount, sampleCount);
  VectorXd inputDistance(sampleCount);
  for (int i = 0; i < sampleCount; ++i) {
    m.col(i) = (featureMatrix.rowwise() - featureMatrix.row(i)).matrix().rowwise().norm();
    inputDistance[i] = (featureMatrix.row(i).transpose() - inputs).norm();
  }

  /// TODO: Normalize each column separately
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

  MatrixXd thetaQuat;
  if (outputQuatMatrix.size()) {
    thetaQuat = mat.transpose();
  }

  MDataHandle hOutput;
  MArrayDataHandle hOutputs = data.outputArrayValue(aOutputs);
  unsigned int outputCount = outputMatrix.cols();
  for (unsigned int i = 0; i < outputCount; ++i) {
    status = JumpToElement(hOutputs, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    hOutput = hOutputs.outputValue();
    hOutput.setGenericDouble(output[i], true);
  }
  hOutputs.setAllClean();

  return MS::kSuccess;
}

MStatus RBFNode::getGenericValues(MArrayDataHandle& hArray, std::vector<double>& values,
                                  std::vector<MQuaternion>& quaternions) {
  MStatus status;
  values.clear();
  quaternions.clear();
  unsigned int count = hArray.elementCount();
  for (int i = 0; i < count; ++i) {
    status = JumpToElement(hArray, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MDataHandle hValue = hArray.inputValue();
    bool isNumeric = false;
    bool isNull = false;
    hValue.isGeneric(isNumeric, isNull);
    if (isNumeric) {
      double v = hValue.asGenericDouble();
      values.push_back(v);
    } else {
      MObject oData = hValue.data();
      MFnNumericData fnData(oData, &status);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      MQuaternion q;
      fnData.getData4Double(q.x, q.y, q.z, q.w);
      quaternions.push_back(q);
    }
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

struct Gaussian {
  Gaussian(const double& radius) {
    static const double kFalloff = 0.707;
    r = radius > 0.0 ? radius : 0.001;
    r *= kFalloff;
  }
  const double operator()(const double& x) const { return exp(-(x * x) / (2.0 * r * r)); }
  double r;
};

struct ThinPlate {
  ThinPlate(const double& radius) { r = radius > 0.0 ? radius : 0.001; }
  const double operator()(const double& x) const {
    double v = x / r;
    v *= x;
    return v > 0.0 ? v * log(x) : v;
  }
  double r;
};

struct MultiQuadraticBiharmonic {
  MultiQuadraticBiharmonic(const double& radius) : r(radius) {}
  const double operator()(const double& x) const { return sqrt((x * x) + (r * r)); }
  double r;
};

struct InverseMultiQuadraticBiharmonic {
  InverseMultiQuadraticBiharmonic(const double& radius) : r(radius) {}
  const double operator()(const double& x) const { return 1.0 / sqrt((x * x) + (r * r)); }
  double r;
};

struct BeckertWendlandC2Basis {
  BeckertWendlandC2Basis(const double& radius) { r = radius > 0.0 ? radius : 0.001; }
  const double operator()(const double& x) const {
    double v = x / r;
    double first = (1.0 - v > 0.0) ? pow(1.0 - v, 4) : 0.0;
    double second = 4.0 * v + 1.0;
    return first * second;
  }
  double r;
};

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