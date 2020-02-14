#ifndef RBF_RBFNODE_H
#define RBF_RBFNODE_H

#include <maya/MArrayDataHandle.h>
#include <maya/MDoubleArray.h>
#include <maya/MPxNode.h>
#include <maya/MQuaternion.h>

#include <Eigen/Dense>
#include <Eigen/Eigenvalues>
#include "linearRegressionSolver.h"

#include <array>
#include <limits>
#include <vector>

using Eigen::MatrixXd;
using Eigen::VectorXd;

class RBFNode : public MPxNode {
 public:
  enum SolverSpace { RBF_SWING, RBF_TWIST, RBF_SWINGTWIST };

  RBFNode();
  virtual ~RBFNode();
  static void* creator();

  virtual MStatus setDependentsDirty(const MPlug& plug, MPlugArray& affectedPlugs) override;
  virtual MStatus preEvaluation(const MDGContext& context,
                                const MEvaluationNode& evaluationNode) override;
  virtual MStatus compute(const MPlug& plug, MDataBlock& data) override;
  virtual bool isPassiveOutput(const MPlug& plug) const override;

  static MStatus initialize();
  static MTypeId id;
  static const MString kName;
  static MObject aOutputValues;
  static MObject aOutputRotateX;
  static MObject aOutputRotateY;
  static MObject aOutputRotateZ;
  static MObject aOutputRotate;
  static MObject aInputValues;
  static MObject aInputQuats;
  static MObject aInputRestQuats;
  static MObject aInputValueCount;
  static MObject aInputQuatCount;
  static MObject aOutputValueCount;
  static MObject aOutputQuatCount;
  static MObject aRBFFunction;
  static MObject aRadius;
  static MObject aRegularization;
  static MObject aSamples;
  static MObject aSampleRadius;
  static MObject aSampleRotationType;
  static MObject aSampleInputValues;
  static MObject aSampleInputQuats;
  static MObject aSampleOutputValues;
  static MObject aSampleOutputQuats;

 private:
  static void affects(const MObject& attribute);
  MStatus buildFeatureMatrix(MDataBlock& data, int inputCount, int outputCount, int inputQuatCount,
                             int outputQuatCount, short rbf, double radius,
                             const std::vector<MQuaternion>& inputRestQuats);
  MStatus getDoubleValues(MArrayDataHandle& hArray, int count, VectorXd& values);
  MStatus getQuaternionValues(MArrayDataHandle& hArray, int count,
                              std::vector<MQuaternion>& quaternions);
  //MatrixXd pseudoInverse(const MatrixXd& a,
  //                       double epsilon = std::numeric_limits<double>::epsilon());
  //void decomposeSwingTwist(const MQuaternion& q, MQuaternion& swing, MQuaternion& twist);
  //void swingTwistDistance(MQuaternion& q1, MQuaternion& q2, double& swingDistance,
  //                        double& twistDistance);
  //double quaternionDistance(MQuaternion& q1, MQuaternion& q2);

  //inline double quaternionDot(const MQuaternion& q1, const MQuaternion& q2) {
  //  double dotValue = (q1.x * q2.x) + (q1.y * q2.y) + (q1.z * q2.z) + (q1.w * q2.w);
  //  // Clamp any floating point error
  //  if (dotValue < -1.0) {
  //    dotValue = -1.0;
  //  } else if (dotValue > 1.0) {
  //    dotValue = 1.0;
  //  }
  //  return dotValue;
  //}

  bool dirty_;
  /*double distanceNorm_;
  VectorXd sampleRadius_;
  VectorXd featureNorms_;
  MatrixXd featureMatrix_;
  std::vector<std::vector<MQuaternion>> featureQuatMatrix_;
  MatrixXd outputScalarMatrix_;
  std::vector<std::vector<MQuaternion>> outputQuatMatrix_;
  std::vector<MatrixXd> outputQuats_;
  MatrixXd theta_;*/

  std::array<LinearRegressionSolver, 3> solvers_;
};

#endif
