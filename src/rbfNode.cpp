#include "rbfNode.h"
#include "common.h"

#include <maya/MEvaluationNode.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnGenericAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnNumericData.h>

MTypeId RBFNode::id(0x0011581A);
MObject RBFNode::aInputValues;
MObject RBFNode::aInputQuats;
MObject RBFNode::aInputValueCount;
MObject RBFNode::aInputQuatCount;
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

  aInputQuats = nAttr.create("inputQuat", "inputQuat", MFnNumericData::k4Double);
  nAttr.setArray(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(aInputQuats);
  attributeAffects(aInputQuats, aOutputValues);
  attributeAffects(aInputQuats, aOutputQuats);

  aInputValueCount = nAttr.create("inputValueCount", "inputValueCount", MFnNumericData::kLong);
  addAttribute(aInputValueCount);
  attributeAffects(aInputValueCount, aOutputValues);
  attributeAffects(aInputValueCount, aOutputQuats);

  aInputQuatCount = nAttr.create("inputQuatCount", "inputQuatCount", MFnNumericData::kLong);
  addAttribute(aInputQuatCount);
  attributeAffects(aInputQuatCount, aOutputValues);
  attributeAffects(aInputQuatCount, aOutputQuats);

  aOutputValueCount = nAttr.create("outputValueCount", "outputValueCount", MFnNumericData::kLong);
  addAttribute(aOutputValueCount);
  attributeAffects(aOutputValueCount, aOutputValues);
  attributeAffects(aOutputValueCount, aOutputQuats);

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

RBFNode::RBFNode() : dirty_(true) {}

RBFNode::~RBFNode() {}

MStatus RBFNode::setDependentsDirty(const MPlug& plug, MPlugArray& affectedPlugs) {
  if (plug == aInputValueCount || plug == aInputQuatCount || plug == aOutputValueCount ||
      plug == aRBFFunction || plug == aRadius || plug == aRegularization || plug == aSamples ||
      plug == aSampleInputValues || plug == aSampleInputQuats || plug == aSampleOutputValues ||
      plug == aSampleOutputQuats) {
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
      (evaluationNode.dirtyPlugExists(aRBFFunction, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aRadius, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aRegularization, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSamples, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleInputValues, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleInputQuats, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleOutputValues, &status) && status) ||
      (evaluationNode.dirtyPlugExists(aSampleOutputQuats, &status) && status)) {
    dirty_ = true;
  }
  return MS::kSuccess;
}

MStatus RBFNode::compute(const MPlug& plug, MDataBlock& data) {
  MStatus status;

  if (plug != aOutputValues && plug != aOutputQuats) {
    return MS::kUnknownParameter;
  }

  short rbf = data.inputValue(aRBFFunction).asShort();
  double radius = data.inputValue(aRadius).asDouble();
  int inputCount = data.inputValue(aInputValueCount).asLong();
  int inputQuatCount = data.inputValue(aInputQuatCount).asLong();
  int outputCount = data.inputValue(aOutputValueCount).asLong();

  // Get the inputs
  MArrayDataHandle hInputs = data.inputArrayValue(aInputValues);
  VectorXd inputs;
  status = getDoubleValues(hInputs, inputCount, inputs);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MArrayDataHandle hInputQuats = data.inputArrayValue(aInputQuats);
  std::vector<MQuaternion> inputQuats;
  status = getQuaternionValues(hInputQuats, inputQuatCount, inputQuats);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  if (dirty_) {
    // Build the system coefficients
    status = buildFeatureMatrix(data, inputCount, outputCount, inputQuatCount, rbf, radius);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    dirty_ = false;
  }

  // Generate distance vector from inputs
  int sampleCount = featureMatrix_.rows();
  if (sampleCount == 0) {
    return MS::kSuccess;
  }
  VectorXd inputDistance = VectorXd::Zero(sampleCount);
  if (inputCount) {
    for (int i = 0; i < inputCount; ++i) {
      if (featureNorms_[i] != 0.0) {
        inputs[i] /= featureNorms_[i];
      }
    }
    for (int i = 0; i < sampleCount; ++i) {
      inputDistance[i] = (featureMatrix_.row(i).transpose() - inputs).norm();
    }
    // Normalize distances
    inputDistance /= distanceNorm_;
  }

  if (inputQuatCount) {
    // Generate rotational distance matrix from rotation inputs
    MatrixXd inputQuatDistance = MatrixXd::Zero(sampleCount, inputQuatCount);
    for (int i = 0; i < inputQuatCount; ++i) {
      MQuaternion& q1 = inputQuats[i];
      for (int s1 = 0; s1 < sampleCount; ++s1) {
        for (int c = 0; c < inputQuatCount; ++c) {
          MQuaternion& q2 = featureQuatMatrix_[s1][c];
          double distance = quaternionDistance(q1, q2);
          inputQuatDistance(s1, c) = distance;
        }
      }
    }

    // Add rotational input distances to main distance
    for (int i = 0; i < inputQuatCount; ++i) {
      inputDistance += inputQuatDistance.col(i);
    }

    // Normalized float distance is 0-1, rotational distances are 0-1
    // Added together they are 0-(inputQuatCount+1)
    // Scale back to 0-1 range
    double scalar = inputCount > 0 ? 1.0 / static_cast<double>(inputQuatCount + 1)
                                   : 1.0 / static_cast<double>(inputQuatCount);
    inputDistance *= scalar;
  }

  applyRbf(inputDistance, rbf, radius);
 
  VectorXd output = theta_ * inputDistance;

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

MStatus RBFNode::buildFeatureMatrix(MDataBlock& data, int inputCount, int outputCount,
                                    int inputQuatCount, short rbf, double radius) {
  MStatus status;
  MArrayDataHandle hSamples = data.inputArrayValue(aSamples);
  unsigned int sampleCount = hSamples.elementCount();
  featureMatrix_.resize(sampleCount, inputCount);
  if (sampleCount == 0) {
    return MS::kSuccess;
  }
  MatrixXd outputMatrix(sampleCount, outputCount);
  // TODO: support quaternion output

  featureQuatMatrix_.resize(sampleCount);
  for (unsigned int i = 0; i < sampleCount; ++i) {
    status = hSamples.jumpToArrayElement(i);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    MDataHandle hSample = hSamples.inputValue(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    if (inputCount) {
      MArrayDataHandle hInputValues = hSample.child(aSampleInputValues);
      VectorXd values;
      status = getDoubleValues(hInputValues, inputCount, values);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      featureMatrix_.row(i) = values;
    }

    if (inputQuatCount) {
      MArrayDataHandle hSampleInputQuats = hSample.child(aSampleInputQuats);
      status = getQuaternionValues(hSampleInputQuats, inputQuatCount, featureQuatMatrix_[i]);
      CHECK_MSTATUS_AND_RETURN_IT(status);
    }

    if (outputCount) {
      MArrayDataHandle hOutputValues = hSample.child(aSampleOutputValues);
      VectorXd values;
      status = getDoubleValues(hOutputValues, outputCount, values);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      outputMatrix.row(i) = values;
    }
  }
  // Generate distance matrix from feature matrix
  // Generate distance vector from inputs
  MatrixXd m = MatrixXd::Zero(sampleCount, sampleCount);
  if (inputCount) {
    featureNorms_.resize(inputCount);
    // Normalize each column so each feature is in the same scale
    for (int i = 0; i < inputCount; ++i) {
      featureNorms_[i] = featureMatrix_.col(i).norm();
      if (featureNorms_[i] != 0.0) {
        featureMatrix_.col(i) /= featureNorms_[i];
      }
    }

    for (int i = 0; i < sampleCount; ++i) {
      m.col(i) = (featureMatrix_.rowwise() - featureMatrix_.row(i)).matrix().rowwise().norm();
    }

    // Normalize distances
    distanceNorm_ = m.norm();
    m /= distanceNorm_;
  }

  if (inputQuatCount) {
    std::vector<MatrixXd> mQuat(inputQuatCount);
    for (int i = 0; i < inputQuatCount; ++i) {
      mQuat[i].resize(sampleCount, sampleCount);
    }

    // Calculate rotation distances
    for (int s1 = 0; s1 < sampleCount; ++s1) {
      for (int s2 = 0; s2 < sampleCount; ++s2) {
        for (int i = 0; i < inputQuatCount; ++i) {
          MQuaternion& q1 = featureQuatMatrix_[s1][i];
          MQuaternion& q2 = featureQuatMatrix_[s2][i];
          double distance = quaternionDistance(q1, q2);
          mQuat[i](s1, s2) = distance;
        }
      }
    }

    // Add rotational distances to main distance
    for (auto& rd : mQuat) {
      m += rd;
    }

    // Normalized float distance is 0-1, rotational distances are 0-1
    // Added together they are 0-(inputQuatCount+1)
    // Scale back to 0-1 range
    double scalar = inputCount > 0 ? 1.0 / static_cast<double>(inputQuatCount + 1)
                                   : 1.0 / static_cast<double>(inputQuatCount);
    m *= scalar;
  }

  applyRbf(m, rbf, radius);

  double regularization = data.inputValue(aRegularization).asDouble();
  MatrixXd r = MatrixXd::Zero(sampleCount, sampleCount);
  r.diagonal().array() = regularization;

  MatrixXd tm = m.transpose();
  MatrixXd mat = pseudoInverse(tm * m + r) * tm;
  theta_ = (mat * outputMatrix).transpose();

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

double RBFNode::quaternionDistance(MQuaternion& q1, MQuaternion& q2) { 
  double dot = quaternionDot(q1, q2);
  return acos(2.0 * dot * dot - 1.0) / M_PI;
}
