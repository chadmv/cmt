#ifndef CMT_LINEARREGRESSIONSOLVER_H
#define CMT_LINEARREGRESSIONSOLVER_H

#include <maya/MDoubleArray.h>
#include <maya/MQuaternion.h>

#include <Eigen/Dense>
#include <Eigen/Eigenvalues>

#include <limits>
#include <vector>

using Eigen::MatrixXd;
using Eigen::VectorXd;

MatrixXd pseudoInverse(const MatrixXd& a, double epsilon = std::numeric_limits<double>::epsilon());

void decomposeSwingTwist(const MQuaternion& q, MQuaternion& swing, MQuaternion& twist);

void swingTwistDistance(const MQuaternion& q1, const MQuaternion& q2, double& swingDistance,
                        double& twistDistance);

double quaternionDistance(MQuaternion& q1, MQuaternion& q2);

inline double quaternionDot(const MQuaternion& q1, const MQuaternion& q2) {
  double dotValue = (q1.x * q2.x) + (q1.y * q2.y) + (q1.z * q2.z) + (q1.w * q2.w);
  // Clamp any floating point error
  if (dotValue < -1.0) {
    dotValue = -1.0;
  } else if (dotValue > 1.0) {
    dotValue = 1.0;
  }
  return dotValue;
}

VectorXd averageQuaternion(const MatrixXd& inputQuats, const VectorXd& weights);

enum class SolverSpace { Swing, Twist, SwingTwist };

class LinearRegressionSolver {
 public:

  LinearRegressionSolver();
  virtual ~LinearRegressionSolver();
  void setFeatures(const MatrixXd& featureMatrix,
                   const std::vector<std::vector<MQuaternion>>& featureQuatMatrix,
                   const MatrixXd& outputScalarMatrix, const std::vector<MatrixXd>& outputQuats,
                   short rbf, double radius, double regularization, SolverSpace space);

  VectorXd solve(const VectorXd& inputs, const std::vector<MQuaternion>& inputQuats, VectorXd& outputs,
             MatrixXd& outputQuats);

  const std::vector<MatrixXd>& outputQuats() const { return outputQuats_; }


 private:
  double distanceNorm_;
  short rbf_;
  double radius_;
  SolverSpace solverSpace_;
  VectorXd sampleRadius_;
  VectorXd featureNorms_;
  MatrixXd featureMatrix_;
  std::vector<std::vector<MQuaternion>> featureQuatMatrix_;
  MatrixXd outputScalarMatrix_;
  std::vector<MatrixXd> outputQuats_;
  MatrixXd theta_;
};

struct Gaussian {
  Gaussian(const double& radius) {
    static const double kFalloff = 0.4;
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
    return v > 0.0 ? v * v * log(v) : v;
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

template <typename T>
void applyRbf(Eigen::MatrixBase<T>& m, short rbf, double radius) {
  switch (rbf) {
    case 0:
      break;
    case 1:
      m = m.unaryExpr(Gaussian(radius));
      break;
    case 2:
      m = m.unaryExpr(ThinPlate(radius));
      break;
    case 3:
      m = m.unaryExpr(MultiQuadraticBiharmonic(radius));
      break;
    case 4:
      m = m.unaryExpr(InverseMultiQuadraticBiharmonic(radius));
      break;
    case 5:
      m = m.unaryExpr(BeckertWendlandC2Basis(radius));
      break;
  }
}

#endif
