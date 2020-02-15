#include "rbfNode.h"
#include "common.h"

#include <maya/MAngle.h>
#include <maya/MEulerRotation.h>
#include <maya/MEvaluationNode.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnGenericAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnNumericData.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MQuaternion.h>

MTypeId RBFNode::id(0x0011581A);
MObject RBFNode::aInputValues;
MObject RBFNode::aInputQuats;
MObject RBFNode::aInputRestQuats;
MObject RBFNode::aInputValueCount;
MObject RBFNode::aInputQuatCount;
MObject RBFNode::aOutputValueCount;
MObject RBFNode::aOutputQuatCount;
MObject RBFNode::aOutputValues;
MObject RBFNode::aOutputRotateX;
MObject RBFNode::aOutputRotateY;
MObject RBFNode::aOutputRotateZ;
MObject RBFNode::aOutputRotate;
MObject RBFNode::aRBFFunction;
MObject RBFNode::aRadius;
MObject RBFNode::aRegularization;
MObject RBFNode::aSamples;
MObject RBFNode::aSampleRadius;
MObject RBFNode::aSampleRotationType;
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
  MFnUnitAttribute uAttr;

  aOutputValues = nAttr.create("outputValue", "outputValue", MFnNumericData::kDouble);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  nAttr.setWritable(false);
  nAttr.setStorable(false);
  addAttribute(aOutputValues);

  aOutputRotateX = uAttr.create("outputRotateX", "outputRotateX", MFnUnitAttribute::kAngle);
  aOutputRotateY = uAttr.create("outputRotateY", "outputRotateY", MFnUnitAttribute::kAngle);
  aOutputRotateZ = uAttr.create("outputRotateZ", "outputRotateZ", MFnUnitAttribute::kAngle);
  aOutputRotate =
      nAttr.create("outputRotate", "outputRotate", aOutputRotateX, aOutputRotateY, aOutputRotateZ);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  nAttr.setWritable(false);
  nAttr.setStorable(false);
  addAttribute(aOutputRotate);

  aInputValues = nAttr.create("inputValue", "inputValue", MFnNumericData::kDouble);
  nAttr.setKeyable(true);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(aInputValues);
  affects(aInputValues);

  aInputQuats = nAttr.create("inputQuat", "inputQuat", MFnNumericData::k4Double);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(aInputQuats);
  affects(aInputQuats);

  aInputRestQuats =
      nAttr.create("inputRestQuat", "inputRestQuat", MFnNumericData::k4Double, 0.0, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(aInputRestQuats);
  affects(aInputRestQuats);

  aInputValueCount = nAttr.create("inputValueCount", "inputValueCount", MFnNumericData::kLong);
  addAttribute(aInputValueCount);
  affects(aInputValueCount);

  aInputQuatCount = nAttr.create("inputQuatCount", "inputQuatCount", MFnNumericData::kLong);
  addAttribute(aInputQuatCount);
  affects(aInputQuatCount);

  aOutputValueCount = nAttr.create("outputValueCount", "outputValueCount", MFnNumericData::kLong);
  addAttribute(aOutputValueCount);
  affects(aOutputValueCount);

  aOutputQuatCount = nAttr.create("outputQuatCount", "outputQuatCount", MFnNumericData::kLong);
  addAttribute(aOutputQuatCount);
  affects(aOutputQuatCount);

  aRBFFunction = eAttr.create("rbf", "rbf");
  eAttr.setKeyable(true);
  eAttr.addField("linear", 0);
  eAttr.addField("gaussian", 1);
  eAttr.addField("thin plate", 2);
  eAttr.addField("multi quadratic biharmonic", 3);
  eAttr.addField("inv multi quadratic biharmonic", 4);
  eAttr.addField("beckert wendland c2 basis", 5);
  addAttribute(aRBFFunction);
  affects(aRBFFunction);

  aRadius = nAttr.create("radius", "radius", MFnNumericData::kDouble, 1.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRadius);
  affects(aRadius);

  aRegularization = nAttr.create("regularization", "regularization", MFnNumericData::kDouble, 0.0);
  nAttr.setKeyable(true);
  nAttr.setMin(0.0);
  addAttribute(aRegularization);
  affects(aRegularization);

  aSampleRadius = nAttr.create("sampleRadius", "sampleRadius", MFnNumericData::kDouble, 1.0);
  nAttr.setMin(0.0);

  aSampleRotationType = eAttr.create("rotationType", "rotationType");
  eAttr.addField("swing", 0);
  eAttr.addField("twist", 1);
  eAttr.addField("swing twist", 2);

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
  cAttr.addChild(aSampleRadius);
  cAttr.addChild(aSampleRotationType);
  cAttr.addChild(aSampleInputValues);
  cAttr.addChild(aSampleInputQuats);
  cAttr.addChild(aSampleOutputValues);
  cAttr.addChild(aSampleOutputQuats);
  addAttribute(aSamples);
  affects(aSamples);
  affects(aSampleRadius);
  affects(aSampleRotationType);
  affects(aSampleInputValues);
  affects(aSampleInputQuats);
  affects(aSampleOutputValues);
  affects(aSampleOutputQuats);

  return MS::kSuccess;
}

void RBFNode::affects(const MObject& attribute) {
  attributeAffects(attribute, aOutputValues);
  attributeAffects(attribute, aOutputRotate);
  attributeAffects(attribute, aOutputRotateX);
  attributeAffects(attribute, aOutputRotateY);
  attributeAffects(attribute, aOutputRotateZ);
}

void* RBFNode::creator() { return new RBFNode(); }

RBFNode::RBFNode() : dirty_(true) {}

RBFNode::~RBFNode() {}

MStatus RBFNode::setDependentsDirty(const MPlug& plug, MPlugArray& affectedPlugs) {
  if (plug == aInputValueCount || plug == aInputQuatCount || plug == aOutputValueCount ||
      plug == aOutputQuatCount || plug == aRBFFunction || plug == aRadius ||
      plug == aRegularization || plug == aSamples || plug == aSampleInputValues ||
      plug == aSampleInputQuats || plug == aSampleOutputValues || plug == aSampleOutputQuats ||
      plug == aSampleRadius || plug == aSampleRotationType) {
    dirty_ = true;
  }
  return MPxNode::setDependentsDirty(plug, affectedPlugs);
}

MStatus RBFNode::preEvaluation(const MDGContext& context, const MEvaluationNode& evaluationNode) {
  MStatus status;
  // We use m_CachedValueIsValid only for normal context
  if (!context.isNormal()) {
    return MStatus::kFailure;
  }

  if ((evaluationNode.dirtyPlugExists(aInputValueCount, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aInputQuatCount, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aOutputValueCount, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aOutputQuatCount, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aRBFFunction, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aRadius, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aRegularization, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSamples, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleRadius, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleRotationType, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleInputValues, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleInputQuats, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleOutputValues, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleOutputQuats, &status) && status)) {
    dirty_ = true;
  }
  return MS::kSuccess;
}

bool RBFNode::isPassiveOutput(const MPlug& plug) const {
  if (plug == aOutputValues || plug == aOutputRotate || plug.parent() == aOutputRotate) {
    return true;
  }
  return MPxNode::isPassiveOutput(plug);
}

MStatus RBFNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutputValues && plug != aOutputRotate) {
    return MS::kUnknownParameter;
  }

  short rbf = data.inputValue(aRBFFunction).asShort();
  double radius = data.inputValue(aRadius).asDouble();
  int inputCount = data.inputValue(aInputValueCount).asLong();
  int inputQuatCount = data.inputValue(aInputQuatCount).asLong();
  int outputCount = data.inputValue(aOutputValueCount).asLong();
  int outputQuatCount = data.inputValue(aOutputQuatCount).asLong();

  // Get the inputs
  MArrayDataHandle hInputs = data.inputArrayValue(aInputValues);
  VectorXd inputs;
  status = getDoubleValues(hInputs, inputCount, inputs);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MArrayDataHandle hInputQuats = data.inputArrayValue(aInputQuats);
  std::vector<MQuaternion> inputQuats;
  status = getQuaternionValues(hInputQuats, inputQuatCount, inputQuats);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MArrayDataHandle hInputRestQuats = data.inputArrayValue(aInputRestQuats);
  std::vector<MQuaternion> inputRestQuats;
  status = getQuaternionValues(hInputRestQuats, inputQuatCount, inputRestQuats);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  for (int i = 0; i < inputQuatCount; ++i) {
    // Convert to relative to neutral to have identity at rest
    inputQuats[i] = inputQuats[i] * inputRestQuats[i].inverse();
  }

  if (dirty_) {
    // Build the system coefficients
    status = buildFeatureMatrix(data, inputCount, outputCount, inputQuatCount, outputQuatCount, rbf,
                                radius, inputRestQuats);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    dirty_ = false;
  }

  MatrixXd outputScalars = MatrixXd::Zero(3, outputCount);
  int scalarCount = 0;
  int quatCount = 0;
  std::vector<MVector> twistAxis(outputQuatCount);
  std::vector<MQuaternion> totalTwist(outputQuatCount);
  for (int i = 0; i < 3; ++i) {
    VectorXd scalars;
    MatrixXd quats;
    solvers_[i].solve(inputs, inputQuats, scalars, quats);
    if (scalars.size()) {
      outputScalars.row(i) = scalars;
    }

    for (int c = 0; c < quats.cols(); ++c) {
      VectorXd col = quats.col(c);
      MQuaternion q(col.data());
      MQuaternion swing;
      MQuaternion twist;
      decomposeSwingTwist(q, swing, twist);
      totalTwist[c] *= twist;
      MMatrix m = swing.asMatrix();
      twistAxis[c] += MVector(m[0][0], m[0][1], m[0][2]);
    }
  }
  VectorXd outValues = outputScalars.colwise().sum();

  MDataHandle hOutput;
  MArrayDataHandle hOutputs = data.outputArrayValue(aOutputValues);
  for (unsigned int i = 0; i < outputCount; ++i) {
    status = JumpToElement(hOutputs, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    hOutput = hOutputs.outputValue();
    hOutput.setDouble(outValues[i]);
  }
  hOutputs.setAllClean();

  MArrayDataHandle hOutputRotation = data.outputArrayValue(aOutputRotate);
  for (unsigned int i = 0; i < outputQuatCount; ++i) {
    MQuaternion q = totalTwist[i] * MVector::xAxis.rotateTo(twistAxis[i].normal());

    MEulerRotation euler = q.asEulerRotation();

    status = JumpToElement(hOutputRotation, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    hOutput = hOutputRotation.outputValue();

    MAngle rx(euler.x);
    MAngle ry(euler.y);
    MAngle rz(euler.z);
    MDataHandle hX = hOutput.child(aOutputRotateX);
    MDataHandle hY = hOutput.child(aOutputRotateY);
    MDataHandle hZ = hOutput.child(aOutputRotateZ);
    hX.setMAngle(rx);
    hY.setMAngle(ry);
    hZ.setMAngle(rz);
    hX.setClean();
    hY.setClean();
    hZ.setClean();
  }
  hOutputRotation.setAllClean();

  return MS::kSuccess;
}

MStatus RBFNode::buildFeatureMatrix(MDataBlock& data, int inputCount, int outputCount,
                                    int inputQuatCount, int outputQuatCount, short rbf,
                                    double radius, const std::vector<MQuaternion>& inputRestQuats) {
  MStatus status;
  MArrayDataHandle hSamples = data.inputArrayValue(aSamples);
  unsigned int sampleCount = hSamples.elementCount();
  if (sampleCount == 0) {
    return MS::kSuccess;
  }

  std::array<std::vector<VectorXd>, 3> inputScalars;
  std::array<std::vector<VectorXd>, 3> outputScalars;
  std::array<std::vector<std::vector<MQuaternion>>, 3> inputQuats;
  std::array<std::vector<std::vector<MQuaternion>>, 3> outputQuats;

  for (unsigned int i = 0; i < sampleCount; ++i) {
    status = hSamples.jumpToArrayElement(i);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    MDataHandle hSample = hSamples.inputValue(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    // sampleRadius_[i] = hSample.child(aSampleRadius).asDouble();
    short rotationType = hSample.child(aSampleRotationType).asShort();

    if (inputCount) {
      MArrayDataHandle hInputValues = hSample.child(aSampleInputValues);
      VectorXd values;
      status = getDoubleValues(hInputValues, inputCount, values);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      inputScalars[rotationType].push_back(values);
    }

    if (inputQuatCount) {
      MArrayDataHandle hSampleInputQuats = hSample.child(aSampleInputQuats);
      std::vector<MQuaternion> quats;
      status = getQuaternionValues(hSampleInputQuats, inputQuatCount, quats);
      CHECK_MSTATUS_AND_RETURN_IT(status);

      // Convert into deltas from rest
      for (int j = 0; j < inputQuatCount; ++j) {
        quats[j] = quats[j] * inputRestQuats[j].inverse();
      }
      inputQuats[rotationType].push_back(quats);
    }

    if (outputCount) {
      MArrayDataHandle hOutputValues = hSample.child(aSampleOutputValues);
      VectorXd values;
      status = getDoubleValues(hOutputValues, outputCount, values);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      outputScalars[rotationType].push_back(values);
    }

    if (outputQuatCount) {
      MArrayDataHandle hSampleOutputQuats = hSample.child(aSampleOutputQuats);
      std::vector<MQuaternion> quats;
      status = getQuaternionValues(hSampleOutputQuats, outputQuatCount, quats);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      outputQuats[rotationType].push_back(quats);
    }
  }

  double regularization = data.inputValue(aRegularization).asDouble();

  // Convert inputs and outputs to matrices to store in regression solvers
  for (int i = 0; i < 3; ++i) {
    MatrixXd inputs;
    if (inputScalars[i].size()) {
      inputs.resize(inputScalars[i].size(), inputScalars[i][0].size());
      int row = 0;
      for (auto& v : inputScalars[i]) {
        inputs.row(row++) = v;
      }
    }

    MatrixXd outputs;
    if (outputScalars[i].size()) {
      outputs.resize(outputScalars[i].size(), outputScalars[i][0].size());
      int row = 0;
      for (auto& v : outputScalars[i]) {
        outputs.row(row++) = v;
      }
    }

    // Store quats as column matrix so we can use weighted quaternion averaging
    std::vector<MatrixXd> outQuats;
    if (outputQuats[i].size()) {
      outQuats.resize(outputQuatCount);

      for (int j = 0; j < outputQuatCount; ++j) {
        outQuats[j].resize(4, outputQuats[i].size());
      }
      int sampleIdx = 0;
      for (auto& sample : outputQuats[i]) {
        int quatIdx = 0;
        for (auto& q : sample) {
          outQuats[quatIdx](0, sampleIdx) = q.x;
          outQuats[quatIdx](1, sampleIdx) = q.y;
          outQuats[quatIdx](2, sampleIdx) = q.z;
          outQuats[quatIdx](3, sampleIdx) = q.w;
          ++quatIdx;
        }
        ++sampleIdx;
      }
    }
    SolverSpace space[] = {SolverSpace::Swing, SolverSpace::Twist, SolverSpace::SwingTwist};
    solvers_[i].setFeatures(inputs, inputQuats[i], outputs, outQuats, rbf, radius, regularization,
                            space[i]);
  }

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
    MDataHandle hQuaternion = hArray.inputValue(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    double4& values = hQuaternion.asDouble4();
    MQuaternion q(values);
    quaternions[i] = q;
  }
  return MS::kSuccess;
}