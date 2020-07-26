#include "linearRegressionSolver.h"

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

#include "common.h"

LinearRegressionSolver::LinearRegressionSolver() {}

LinearRegressionSolver::~LinearRegressionSolver() {}

void LinearRegressionSolver::setFeatures(
    const MatrixXd& featureMatrix, const std::vector<std::vector<MQuaternion>>& featureQuatMatrix,
    const MatrixXd& outputScalarMatrix, const std::vector<MatrixXd>& outputQuats, short rbf,
    double radius, double regularization, SolverSpace space) {
  featureMatrix_ = featureMatrix;
  featureQuatMatrix_ = featureQuatMatrix;
  outputScalarMatrix_ = outputScalarMatrix;
  outputQuats_ = outputQuats;
  rbf_ = rbf;
  radius_ = radius;
  solverSpace_ = space;

  int sampleCount = featureMatrix_.rows() ? featureMatrix_.rows() : featureQuatMatrix_.size();
  if (sampleCount <= 1) {
    theta_.resize(0, 0);
    return;
  }
  int inputCount = featureMatrix_.cols();
  int inputQuatCount = featureQuatMatrix.size() ? featureQuatMatrix_[0].size() : 0;
  int valueCols = inputCount ? sampleCount : 0;
  // We will append the swing and twist distances for each input rotation
  // to the distance matrix
  int cols = valueCols + sampleCount * 2 * inputQuatCount;

  MatrixXd m = MatrixXd::Zero(sampleCount, cols);

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

  applyRbf(m, rbf_, radius_);

  if (inputQuatCount) {
    std::vector<MatrixXd> mQuat(inputQuatCount);
    for (int i = 0; i < inputQuatCount; ++i) {
      mQuat[i].resize(sampleCount, sampleCount * 2);
    }
    sampleRadius_ = VectorXd::Ones(sampleCount);

    // Calculate rotation distances
    double minFalloff = std::numeric_limits<double>::max();
    double swingDistance, twistDistance;
    for (int s1 = 0; s1 < sampleCount; ++s1) {
      for (int s2 = 0; s2 < sampleCount; ++s2) {
        for (int i = 0; i < inputQuatCount; ++i) {
          MQuaternion& q1 = featureQuatMatrix_[s1][i];
          MQuaternion& q2 = featureQuatMatrix_[s2][i];
          swingTwistDistance(q1, q2, swingDistance, twistDistance);
          if (solverSpace_ == SolverSpace::Swing) {
            twistDistance = 0.0;
          } else if (solverSpace_ == SolverSpace::Twist) {
            swingDistance = 0.0;
          }
          // TODO: Each feature quat should have it's own radius
          if (swingDistance > 0.000001 && swingDistance < sampleRadius_[s1]) {
            sampleRadius_[s1] = swingDistance;
          }
          if (twistDistance > 0.000001 && twistDistance < sampleRadius_[s1]) {
            sampleRadius_[s1] = twistDistance;
          }
          /*
          double _r = 57.2958;
          auto e1 = q1.asEulerRotation();
          auto e2 = q2.asEulerRotation();
          std::cout << s1 << ": (" << e1.x * _r << ", " << e1.y * _r << ", " << e1.z * _r
                    << ") <==> (" << e2.x * _r << ", " << e2.y * _r << ", " << e2.z * _r
                    << ") s : " << swingDistance << " t : " << twistDistance << std::endl;*/

          mQuat[i](s1, s2 * 2) = swingDistance;
          mQuat[i](s1, s2 * 2 + 1) = twistDistance;
        }
      }
    }
    // Insert rotational distances to main distance matrix
    int quatIndex = 0;
    for (auto& rd : mQuat) {
      // Apply rbf with per-pose radius to quaternion inputs
      for (int i = 0; i < sampleCount; ++i) {
        auto m = rd.block(0, i * 2, sampleCount, 2);
        applyRbf(m, rbf_, sampleRadius_[i] * radius_);
      }

      m.block(0, valueCols + rd.cols() * quatIndex, sampleCount, rd.cols()) = rd;
      ++quatIndex;
    }
  }

  // Rather than solve directly to the output values, we will store 0 or 1 pose values.
  // This lets us calculate the output as a linear combination of the sample outputs and
  // will make it easier to calculate output quaternions
  MatrixXd outputMatrix = MatrixXd::Identity(sampleCount, sampleCount);
  MatrixXd r = MatrixXd::Zero(cols, cols);
  r.diagonal().array() = regularization;

  MatrixXd tm = m.transpose();
  MatrixXd mat = pseudoInverse(tm * m + r) * tm;
  theta_ = (mat * outputMatrix).transpose();
}

VectorXd LinearRegressionSolver::solve(const VectorXd& inputValues,
                                       const std::vector<MQuaternion>& inputQuats,
                                       VectorXd& outputs, MatrixXd& outputQuats) {
  int sampleCount = featureMatrix_.rows() ? featureMatrix_.rows() : featureQuatMatrix_.size();
  if (sampleCount <= 1) {
    return VectorXd();
  }
  VectorXd inputs = inputValues;
  int inputCount = inputs.size();

  VectorXd inputDistance = VectorXd::Zero(theta_.cols());
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
  applyRbf(inputDistance, rbf_, radius_);

  if (featureQuatMatrix_.size()) {
    int inputQuatCount = featureQuatMatrix_[0].size();
    // Generate rotational distance matrix from rotation inputs
    double swingDistance, twistDistance;
    int idx = inputCount ? sampleCount : 0;
    for (int i = 0; i < inputQuatCount; ++i) {
      const MQuaternion& q1 = inputQuats[i];
      for (int s1 = 0; s1 < sampleCount; ++s1) {
        int startIdx = idx;
        for (int c = 0; c < inputQuatCount; ++c) {
          MQuaternion& q2 = featureQuatMatrix_[s1][c];
          swingTwistDistance(q1, q2, swingDistance, twistDistance);
          if (solverSpace_ == SolverSpace::Swing) {
            twistDistance = 0.0;
          } else if (solverSpace_ == SolverSpace::Twist) {
            swingDistance = 0.0;
          }
          inputDistance[idx++] = swingDistance;
          inputDistance[idx++] = twistDistance;
        }
        applyRbf(inputDistance.segment(startIdx, inputQuatCount * 2), rbf_, sampleRadius_[s1]);
      }
    }
  }

  VectorXd output = theta_ * inputDistance;
  int outputCount = outputScalarMatrix_.cols();
  outputs.resize(outputCount);
  for (unsigned int i = 0; i < outputCount; ++i) {
    outputs[i] = output.dot(outputScalarMatrix_.col(i));
  }

  int outputQuatCount = outputQuats_.size();
  output.normalize();  // Weights must be normalize for weight avg of quaternions
  outputQuats.resize(4, outputQuatCount);
  for (unsigned int i = 0; i < outputQuatCount; ++i) {
    outputQuats.col(i) = averageQuaternion(outputQuats_[i], output);
  }
  return output;
}

MatrixXd pseudoInverse(const MatrixXd& a, double epsilon) {
  Eigen::JacobiSVD<MatrixXd> svd(a, Eigen::ComputeThinU | Eigen::ComputeThinV);
  double tolerance = epsilon * std::max(a.cols(), a.rows()) * svd.singularValues().array().abs()(0);
  return svd.matrixV() *
         (svd.singularValues().array().abs() > tolerance)
             .select(svd.singularValues().array().inverse(), 0)
             .matrix()
             .asDiagonal() *
         svd.matrixU().adjoint();
}

double quaternionDistance(MQuaternion& q1, MQuaternion& q2) {
  double dot = quaternionDot(q1, q2);
  return acos(2.0 * dot * dot - 1.0) / M_PI;
}

void swingTwistDistance(const MQuaternion& q1, const MQuaternion& q2, double& swingDistance,
                        double& twistDistance) {
  MQuaternion s1, t1, s2, t2;
  decomposeSwingTwist(q1, s1, t1);
  decomposeSwingTwist(q2, s2, t2);
  swingDistance = quaternionDistance(s1, s2);
  twistDistance = quaternionDistance(t1, t2);
}

void decomposeSwingTwist(const MQuaternion& q, MQuaternion& swing, MQuaternion& twist) {
  // TODO: Support different twist axis
  twist.x = q.x;
  twist.y = 0.0;
  twist.z = 0.0;
  twist.w = q.w;
  twist.normalizeIt();
  swing = twist.inverse() * q;
}

VectorXd averageQuaternion(const MatrixXd& inputQuats, const VectorXd& weights) {
  // Weighted average of multiple quaternions:
  // https://stackoverflow.com/a/27410865
  MatrixXd Q = inputQuats * weights;
  Q *= Q.transpose();
  Eigen::SelfAdjointEigenSolver<MatrixXd> solver(Q);
  auto eigenValues = solver.eigenvalues();
  double maxValue = eigenValues[0];
  int maxIndex = 0;
  for (int j = 0; j < eigenValues.size(); ++j) {
    if (eigenValues[j] > maxValue) {
      maxValue = eigenValues[j];
      maxIndex = j;
    }
  }
  VectorXd averageQuat = solver.eigenvectors().col(maxIndex);
  return averageQuat;
}