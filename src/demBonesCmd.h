#ifndef CMT_DEMBONESCMD_H
#define CMT_DEMBONESCMD_H

#include "DemBones/DemBonesExt.h"

#include <maya/MArgDatabase.h>
#include <maya/MArgList.h>
#include <maya/MDGModifier.h>
#include <maya/MDagPath.h>
#include <maya/MDagPathArray.h>
#include <maya/MGlobal.h>
#include <maya/MObject.h>
#include <maya/MPxCommand.h>
#include <maya/MSelectionList.h>
#include <maya/MSyntax.h>

#include <iostream>

using namespace Dem;

class MyDemBones : public DemBonesExt<double, float> {
 public:
  void cbIterBegin() { std::cout << "    Iter #" << iter << ": "; }

  void cbIterEnd() { std::cout << "RMSE = " << rmse() << "\n"; }

  void cbInitSplitBegin() { std::cout << ">"; }

  void cbInitSplitEnd() { std::cout << nB; }

  void cbWeightsBegin() { std::cout << "Updating weights"; }

  void cbWeightsEnd() { std::cout << " Done! "; }

  void cbTranformationsBegin() { std::cout << "Updating trans"; }

  void cbTransformationsEnd() { std::cout << " Done! "; }

  void cbTransformationsIterEnd() { std::cout << "."; }

  void cbWeightsIterEnd() { std::cout << "."; }
};

class DemBonesCmd : public MPxCommand {
 public:
  virtual MStatus doIt(const MArgList& argList);
  virtual MStatus redoIt();
  virtual MStatus undoIt();
  virtual bool isUndoable() const;

  static void* creator();
  static MSyntax newSyntax();

  static const MString kName;
  static const char* kWeightsSmoothStepShort;
  static const char* kWeightsSmoothStepLong;
  static const char* kWeightsSmoothShort;
  static const char* kWeightsSmoothLong;
  static const char* kNumNonZeroShort;
  static const char* kNumNonZeroLong;
  static const char* kWeightItersShort;
  static const char* kWeightItersLong;
  static const char* kTransAffineNormShort;
  static const char* kTransAffineNormLong;
  static const char* kTransAffineShort;
  static const char* kTransAffineLong;
  static const char* kBindUpdateShort;
  static const char* kBindUpdateLong;
  static const char* kTransItersShort;
  static const char* kTransItersLong;
  static const char* kItersShort;
  static const char* kItersLong;
  static const char* kInitItersShort;
  static const char* kInitItersLong;
  static const char* kBonesShort;
  static const char* kBonesLong;
  static const char* kStartFrameShort;
  static const char* kStartFrameLong;
  static const char* kEndFrameShort;
  static const char* kEndFrameLong;
  static const char* kExistingBonesShort;
  static const char* kExistingBonesLong;

 private:
  MStatus readMeshSequence(double startFrame, double endFrame);
  MStatus readBindPose();
  MStatus setKeyframes(const Eigen::VectorXd& val, const Eigen::VectorXd& fTime,
                       const MDagPath& pathJoint, const MString& attributeName);
  MStatus setSkinCluster(const std::vector<std::string>& name, const Eigen::SparseMatrix<double>& w, const Eigen::MatrixXd& gb);
  Eigen::Matrix4d toMatrix4d(const MMatrix& m);

  MyDemBones model_;
  MDGModifier dgMod_;
  MString name_;
  MDagPath pathMesh_;
  MDagPathArray pathBones_;
};

#endif
