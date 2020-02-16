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
  static MObject aSampleOutputMode;
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

  bool dirty_;
  std::array<LinearRegressionSolver, 3> solvers_;
  std::vector<MQuaternion> neutralQuats_;
  VectorXd neutralValues_;
};

#endif
