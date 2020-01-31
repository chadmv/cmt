#ifndef RBF_RBFNODE_H
#define RBF_RBFNODE_H

#include <maya/MArrayDataHandle.h>
#include <maya/MDoubleArray.h>
#include <maya/MPxNode.h>
#include <maya/MQuaternion.h>

#include <Eigen/Dense>
#include <limits>
#include <vector>

using Eigen::MatrixXd;
using Eigen::VectorXd;

class RBFNode : public MPxNode {
 public:
  RBFNode();
  virtual ~RBFNode();
  static void* creator();

  virtual MStatus compute(const MPlug& plug, MDataBlock& data);

  static MStatus initialize();
  static MTypeId id;
  static const MString kName;
  static MObject aOutputValues;
  static MObject aOutputQuats;
  static MObject aInputValues;
  static MObject aInputQuats;
  static MObject aInputValueCount;
  static MObject aOutputValueCount;
  static MObject aRBFFunction;
  static MObject aRadius;
  static MObject aRegularization;
  static MObject aSamples;
  static MObject aSampleInputValues;
  static MObject aSampleInputQuats;
  static MObject aSampleOutputValues;
  static MObject aSampleOutputQuats;

 private:
  MStatus getDoubleValues(MArrayDataHandle& hArray, int count, VectorXd& values);
  MStatus getQuaternionValues(MArrayDataHandle& hArray, int count,
                              std::vector<MQuaternion>& quaternions);
  MatrixXd pseudoInverse(const MatrixXd& a,
                         double epsilon = std::numeric_limits<double>::epsilon());
};

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
