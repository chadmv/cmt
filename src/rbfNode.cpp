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
  affects(aSamples);
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
      plug == aSampleInputQuats || plug == aSampleOutputValues || plug == aSampleOutputQuats) {
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

  if (dirty_) {
    // Build the system coefficients
    status = buildFeatureMatrix(data, inputCount, outputCount, inputQuatCount, outputQuatCount, rbf,
                                radius);
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
    double v = output.dot(outputScalarMatrix_.col(i));

    status = JumpToElement(hOutputs, i);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    hOutput = hOutputs.outputValue();
    hOutput.setDouble(v);
  }
  hOutputs.setAllClean();

  MArrayDataHandle hOutputRotation = data.outputArrayValue(aOutputRotate);
  MQuaternion rest;
  for (unsigned int i = 0; i < outputQuatCount; ++i) {
    MQuaternion totalTwist;
    MVector twistAxis;
    for (unsigned int j = 0; j < output.size(); ++j) {
      MQuaternion& q = outputQuatMatrix_[j][i];
      MQuaternion twist(q.x, 0.0, 0.0, q.w);
      twist.normalizeIt();
      MQuaternion swing = twist.inverse() * q;

      totalTwist *= slerp(rest, twist, output[j]);
      MMatrix swingMatrix = swing.asMatrix();
      twistAxis += MVector(swingMatrix[0][0], swingMatrix[0][1], swingMatrix[0][2]) * output[j];
    }
    if (twistAxis.length() == 0.0) {
      // If the twistAxis has been canceled out, no swing
      twistAxis = MVector::xAxis;
    }

    MQuaternion totalSwing = MVector::xAxis.rotateTo(twistAxis.normal());
    MQuaternion outQ = totalTwist * totalSwing;
    MEulerRotation euler = outQ.asEulerRotation();

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
                                    double radius) {
  MStatus status;
  MArrayDataHandle hSamples = data.inputArrayValue(aSamples);
  unsigned int sampleCount = hSamples.elementCount();
  featureMatrix_.resize(sampleCount, inputCount);
  if (sampleCount == 0) {
    return MS::kSuccess;
  }
  // Rather than solve directly to the output values, we will store 0 or 1 pose values.
  // This lets us calculate the output as a linear combination of the sample outputs and
  // will make it easier to calculate output quaternions
  MatrixXd outputMatrix = MatrixXd::Identity(sampleCount, sampleCount);

  outputScalarMatrix_.resize(sampleCount, outputCount);

  featureQuatMatrix_.resize(sampleCount);
  outputQuatMatrix_.resize(sampleCount);
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
      outputScalarMatrix_.row(i) = values;
    }

    if (outputQuatCount) {
      MArrayDataHandle hSampleOutputQuats = hSample.child(aSampleOutputQuats);
      status = getQuaternionValues(hSampleOutputQuats, outputQuatCount, outputQuatMatrix_[i]);
      CHECK_MSTATUS_AND_RETURN_IT(status);
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
