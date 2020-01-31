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

struct Gaussian;
struct ThinPlate;
struct MultiQuadraticBiharmonic;
struct InverseMultiQuadraticBiharmonic;
struct BeckertWendlandC2Basis;


class RBFNode : public MPxNode {
 public:
  RBFNode();
  virtual ~RBFNode();
  static void* creator();

  virtual MStatus compute(const MPlug& plug, MDataBlock& data);

  static MStatus initialize();
  static MTypeId id;
  static const MString kName;
  static MObject aInputs;
  static MObject aOutputs;
  static MObject aRBFFunction;
  static MObject aRadius;
  static MObject aRegularization;
  static MObject aSamples;
  static MObject aInputValues;
  static MObject aOutputValues;

 private:
  MStatus getGenericValues(MArrayDataHandle& hArray, std::vector<double>& values,
                           std::vector<MQuaternion>& quaternions);
  MatrixXd pseudoInverse(const MatrixXd& a,
                         double epsilon = std::numeric_limits<double>::epsilon());
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
