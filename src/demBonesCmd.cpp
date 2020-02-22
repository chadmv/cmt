#include "demBonesCmd.h"
#include "common.h"
#ifndef DEM_BONES_MAT_BLOCKS
#include "DemBones/MatBlocks.h"
#define DEM_BONES_DEM_BONES_MAT_BLOCKS_UNDEFINED
#endif

#include <maya/MAnimControl.h>
#include <maya/MDagPath.h>
#include <maya/MEulerRotation.h>
#include <maya/MFnAnimCurve.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnMatrixData.h>
#include <maya/MFnMesh.h>
#include <maya/MFnSet.h>
#include <maya/MFnSkinCluster.h>
#include <maya/MFnTransform.h>
#include <maya/MMatrix.h>
#include <maya/MPlug.h>
#include <maya/MTime.h>

const char* DemBonesCmd::kWeightsSmoothStepShort = "-wss";
const char* DemBonesCmd::kWeightsSmoothStepLong = "-weightsSmoothStep";
const char* DemBonesCmd::kWeightsSmoothShort = "-ws";
const char* DemBonesCmd::kWeightsSmoothLong = "-weightsSmooth";
const char* DemBonesCmd::kNumNonZeroShort = "-mi";
const char* DemBonesCmd::kNumNonZeroLong = "-maxInfluences";
const char* DemBonesCmd::kWeightItersShort = "-wi";
const char* DemBonesCmd::kWeightItersLong = "-weightIters";
const char* DemBonesCmd::kTransAffineNormShort = "-tan";
const char* DemBonesCmd::kTransAffineNormLong = "-transAffineNorm";
const char* DemBonesCmd::kTransAffineShort = "-ta";
const char* DemBonesCmd::kTransAffineLong = "-transAffine";
const char* DemBonesCmd::kBindUpdateShort = "-nu";
const char* DemBonesCmd::kBindUpdateLong = "-bindUpdate";
const char* DemBonesCmd::kTransItersShort = "-ti";
const char* DemBonesCmd::kTransItersLong = "-transIters";
const char* DemBonesCmd::kItersShort = "-i";
const char* DemBonesCmd::kItersLong = "-iters";
const char* DemBonesCmd::kInitItersShort = "-ii";
const char* DemBonesCmd::kInitItersLong = "-initIters";
const char* DemBonesCmd::kBonesShort = "-b";
const char* DemBonesCmd::kBonesLong = "-bones";
const char* DemBonesCmd::kStartFrameShort = "-sf";
const char* DemBonesCmd::kStartFrameLong = "-startFrame";
const char* DemBonesCmd::kEndFrameShort = "-ef";
const char* DemBonesCmd::kEndFrameLong = "-endFrame";
const char* DemBonesCmd::kExistingBonesShort = "-eb";
const char* DemBonesCmd::kExistingBonesLong = "-existingBones";
const MString DemBonesCmd::kName("demBones");

void* DemBonesCmd::creator() { return new DemBonesCmd; }

bool DemBonesCmd::isUndoable() const { return true; }

MSyntax DemBonesCmd::newSyntax() {
  MSyntax syntax;

  syntax.addFlag(kWeightsSmoothStepShort, kWeightsSmoothStepLong, MSyntax::kDouble);
  syntax.addFlag(kWeightsSmoothShort, kWeightsSmoothLong, MSyntax::kDouble);
  syntax.addFlag(kNumNonZeroShort, kNumNonZeroLong, MSyntax::kLong);
  syntax.addFlag(kWeightItersShort, kWeightItersLong, MSyntax::kLong);
  syntax.addFlag(kTransAffineNormShort, kTransAffineNormLong, MSyntax::kDouble);
  syntax.addFlag(kTransAffineShort, kTransAffineLong, MSyntax::kDouble);
  syntax.addFlag(kBindUpdateShort, kBindUpdateLong, MSyntax::kBoolean);
  syntax.addFlag(kTransItersShort, kTransItersLong, MSyntax::kLong);
  syntax.addFlag(kItersShort, kItersLong, MSyntax::kLong);
  syntax.addFlag(kInitItersShort, kItersLong, MSyntax::kLong);
  syntax.addFlag(kBonesShort, kBonesLong, MSyntax::kLong);
  syntax.addFlag(kStartFrameShort, kStartFrameLong, MSyntax::kDouble);
  syntax.addFlag(kEndFrameShort, kEndFrameLong, MSyntax::kDouble);
  syntax.addFlag(kExistingBonesShort, kExistingBonesLong, MSyntax::kString);
  syntax.makeFlagMultiUse(kExistingBonesShort);

  syntax.setObjectType(MSyntax::kSelectionList, 1, 1);
  syntax.useSelectionAsDefault(true);

  syntax.enableEdit(false);
  syntax.enableQuery(false);

  return syntax;
}

MStatus DemBonesCmd::doIt(const MArgList& argList) {
  MStatus status;
  // Read all the flag arguments
  MArgDatabase argData(syntax(), argList, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MSelectionList selection;
  status = argData.getObjects(selection);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = selection.getDagPath(0, pathMesh_);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = getShapeNode(pathMesh_);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  double startFrame = MAnimControl::animationStartTime().value();
  if (argData.isFlagSet(kStartFrameShort)) {
    startFrame = argData.flagArgumentDouble(kStartFrameShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  double endFrame = MAnimControl::animationEndTime().value();
  if (argData.isFlagSet(kEndFrameShort)) {
    endFrame = argData.flagArgumentDouble(kEndFrameShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }

  if (argData.isFlagSet(kExistingBonesShort)) {
    unsigned int count = argData.numberOfFlagUses(kExistingBonesShort);
    pathBones_.setLength(count);
    unsigned int pos;
    for (unsigned int i = 0; i < count; ++i) {
      MSelectionList slist;
      status = argData.getFlagArgumentPosition(kExistingBonesShort, i, pos);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      MArgList mArgs;
      status = argData.getFlagArgumentList(kExistingBonesShort, i, mArgs);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      MString boneName = mArgs.asString(0);
      status = getDagPath(boneName, pathBones_[i]);
      CHECK_MSTATUS_AND_RETURN_IT(status);
    }
  }

  status = readMeshSequence(startFrame, endFrame);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  status = readBindPose();
  CHECK_MSTATUS_AND_RETURN_IT(status);

  if (argData.isFlagSet(kItersShort)) {
    model_.nIters = argData.flagArgumentInt(kItersShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kTransItersShort)) {
    model_.nTransIters = argData.flagArgumentInt(kTransItersShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kWeightItersShort)) {
    model_.nWeightsIters = argData.flagArgumentInt(kWeightItersShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kBindUpdateShort)) {
    model_.bindUpdate = static_cast<int>(argData.flagArgumentBool(kBindUpdateShort, 0, &status));
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kTransAffineShort)) {
    model_.transAffine = argData.flagArgumentDouble(kTransAffineShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kTransAffineNormShort)) {
    model_.transAffineNorm = argData.flagArgumentDouble(kTransAffineNormShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kNumNonZeroShort)) {
    model_.nnz = argData.flagArgumentInt(kNumNonZeroShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kWeightsSmoothShort)) {
    model_.weightsSmooth = argData.flagArgumentDouble(kWeightsSmoothShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  if (argData.isFlagSet(kWeightsSmoothStepShort)) {
    model_.weightsSmoothStep = argData.flagArgumentDouble(kWeightsSmoothStepShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }

  if (argData.isFlagSet(kInitItersShort)) {
    model_.nInitIters = argData.flagArgumentDouble(kInitItersShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }

  if (argData.isFlagSet(kBonesShort) && model_.nB > 0) {
    int boneCount = argData.flagArgumentInt(kBonesShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    model_.nB += boneCount;
  }

  if (model_.nB == 0) {
    if (!argData.isFlagSet(kBonesShort)) {
      MGlobal::displayError("No joints found. Need to set the number of bones (-b/-bones)");
      return MS::kInvalidParameter;
    }

    model_.nB = argData.flagArgumentInt(kBonesShort, 0, &status);
    std::cout << "Initializing bones: 1";
    model_.init();
    std::cout << std::endl;
  }

  std::cout << "Computing Skinning Decomposition:\n";
  if (!model_.compute()) {
    return MS::kFailure;
  }

  return redoIt();
}

MStatus DemBonesCmd::readMeshSequence(double startFrame, double endFrame) {
  MStatus status;
  model_.nS = 1;
  model_.nF = static_cast<int>(endFrame - startFrame + 1.0);

  MFnMesh fnMesh(pathMesh_, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  model_.nV = fnMesh.numVertices();
  model_.v.resize(3 * model_.nF, model_.nV);
  model_.fTime.resize(model_.nF);
  model_.fStart.resize(model_.nS + 1);
  model_.fStart(0) = 0;
  model_.nB = pathBones_.length();
  model_.m.resize(model_.nF * 4, model_.nB * 4);

  int frameCount = static_cast<int>(endFrame - startFrame + 1);

  // Get bone info
  MTime time = MAnimControl::currentTime();
  time.setValue(0.0);
  status = MAnimControl::setCurrentTime(time);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  model_.boneName.resize(model_.nB);
  for (unsigned int i = 0; i < model_.nB; ++i) {
    model_.boneName[i] = pathBones_[i].partialPathName().asChar();
  }

  model_.parent.resize(model_.nB);
  model_.bind.resize(model_.nS * 4, model_.nB * 4);
  model_.preMulInv.resize(model_.nS * 4, model_.nB * 4);
  model_.rotOrder.resize(model_.nS * 3, model_.nB);
  int s = 0;

  for (int j = 0; j < model_.nB; j++) {
    std::string nj = model_.boneName[j];

    model_.parent(j) = -1;
    MDagPath parent(pathBones_[j]);
    status = parent.pop();
    if (!MFAIL(status)) {
      for (int k = 0; k < model_.nB; k++) {
        if (model_.boneName[k] == parent.partialPathName().asChar()) {
          model_.parent(j) = k;
        }
      }
    }

    model_.bind.blk4(s, j) = toMatrix4d(pathBones_[j].inclusiveMatrix());

    MFnTransform fnTransform(pathBones_[j], &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    MEulerRotation rotation;
    fnTransform.getRotation(rotation);
    switch (rotation.order) {
      case MEulerRotation::kXYZ:
        model_.rotOrder.vec3(s, j) = Eigen::Vector3i(0, 1, 2);
        break;
      case MEulerRotation::kYZX:
        model_.rotOrder.vec3(s, j) = Eigen::Vector3i(1, 2, 0);
        break;
      case MEulerRotation::kZXY:
        model_.rotOrder.vec3(s, j) = Eigen::Vector3i(2, 0, 1);
        break;
      case MEulerRotation::kXZY:
        model_.rotOrder.vec3(s, j) = Eigen::Vector3i(0, 2, 1);
        break;
      case MEulerRotation::kYXZ:
        model_.rotOrder.vec3(s, j) = Eigen::Vector3i(1, 0, 2);
        break;
      case MEulerRotation::kZYX:
        model_.rotOrder.vec3(s, j) = Eigen::Vector3i(2, 1, 0);
        break;
    }

    MMatrix preMulInv;  // Seems to always be identity
    /*MMatrix gp = pathBones_[j].exclusiveMatrix();
    pathBones_[j].exclusiveMatrixInverse() *

    if (jn[j].pParentJoint == NULL)
      preMulInv = gp.inverse();
    else {
      Matrix4d gjp = Map<Matrix4d>((double*)(jn[j].pParentJoint->EvaluateGlobalTransform()));
      preMulInv =  gp.inverse() * gjp;
    }*/
    model_.preMulInv.blk4(s, j) = toMatrix4d(preMulInv);

  }

  // TODO: Use existing bone weight
  Eigen::MatrixXd wd(0, 0);
  /*if (importer.wT.size() != 0) {
    wd = MatrixXd::Zero(model.nB, model.nV);
    for (int j = 0; j < model.nB; j++){
      wd.row(j) = importer.wT[model.boneName[j]].transpose();
    }
  }*/

  model_.w = (wd / model_.nS).sparseView(1, 1e-20);
  bool hasKeyFrame = true;
  if (!hasKeyFrame) {
    model_.m.resize(0, 0);
  }


  for (int s = 0; s < model_.nS; s++) {
    int start = model_.fStart(s);
    // Read vertex data each frame
    for (int f = 0; f < model_.nF; ++f) {
      double frame = startFrame + static_cast<double>(f);
      time.setValue(frame);
      status = MAnimControl::setCurrentTime(time);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      model_.fTime(start + f) = frame;
      MPointArray points;
      fnMesh.getPoints(points, MSpace::kWorld);

#pragma omp parallel for
      for (int i = 0; i < model_.nV; i++) {
        model_.v.col(i).segment<3>((start + f) * 3) << points[i].x, points[i].y, points[i].z;
      }

      for (int j = 0; j < model_.nB; ++j) {
        model_.m.blk4(f, j) = toMatrix4d(pathBones_[j].inclusiveMatrix()) * model_.bind.blk4(s, j).inverse();
      }
    }
    model_.fStart(s + 1) = model_.fStart(s) + model_.nF;
  }

  model_.origM = model_.m;

  model_.subjectID.resize(model_.nF);
  for (int s = 0; s < model_.nS; s++) {
    for (int k = model_.fStart(s); k < model_.fStart(s + 1); k++) {
      model_.subjectID(k) = s;
    }
  }

  return MS::kSuccess;
}

MStatus DemBonesCmd::readBindPose() {
  MStatus status;
  MTime time = MAnimControl::currentTime();
  time.setValue(0.0);
  status = MAnimControl::setCurrentTime(time);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MFnMesh fnMesh(pathMesh_, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MPointArray points;
  fnMesh.getPoints(points, MSpace::kWorld);

  model_.u.resize(model_.nS * 3, model_.nV);
  Eigen::MatrixXd v;
  v.resize(3, fnMesh.numVertices());
  for (int i = 0; i < model_.nV; i++) {
    v.col(i) << points[i].x, points[i].y, points[i].z;
  }

  model_.u.block(0, 0, 3, model_.nV) = v;

  int numPolygons = fnMesh.numPolygons();
  model_.fv.resize(numPolygons);
  for (int i = 0; i < numPolygons; i++) {
    MIntArray vertexList;
    fnMesh.getPolygonVertices(i, vertexList);
    model_.fv[i].resize(vertexList.length());
    for (unsigned int j = 0; j < model_.fv[i].size(); ++j) {
      model_.fv[i][j] = vertexList[j];
    }
  }

  return MS::kSuccess;
}

MStatus DemBonesCmd::redoIt() {
  MStatus status;
  clearResult();

  bool needCreateJoints = (model_.boneName.size() != model_.nB);
  std::vector<std::string> newBoneNames;
  MStringArray joints;

  if (needCreateJoints) {
    // model.boneName.resize(model.nB);
    int creationCount = model_.nB - static_cast<int>(model_.boneName.size());
    for (int j = 0; j < creationCount; j++) {
      std::ostringstream s;
      s << "dembones_joint" << j;
      model_.boneName.push_back(s.str());
      newBoneNames.push_back(s.str());
      joints.append(s.str().c_str());
    }
  }
  for (int s = 0; s < model_.nS; ++s) {
    Eigen::MatrixXd lr, lt, gb, lbr, lbt;
    model_.computeRTB(s, lr, lt, gb, lbr, lbt, false);

    Eigen::VectorXd val;
    for (int j = 0; j < newBoneNames.size(); ++j) {
      MString name(newBoneNames[j].c_str());
      MString cmd("createNode \"joint\" -n \"" + name + "\"");
      MGlobal::executeCommand(cmd);
    }
    int startJointIdx = newBoneNames.size() == 0 ? 0 : model_.boneName.size() - newBoneNames.size();
    for (int j = startJointIdx; j < model_.boneName.size(); ++j) {
      MDagPath pathJoint;
      status = getDagPath(model_.boneName[j].c_str(), pathJoint);
      CHECK_MSTATUS_AND_RETURN_IT(status);

      val = lr.col(j);
      setKeyframes(
          Eigen::Map<Eigen::VectorXd, 0, Eigen::InnerStride<3>>(val.data() + 0, val.size() / 3),
          model_.fTime, pathJoint, "rx");
      setKeyframes(
          Eigen::Map<Eigen::VectorXd, 0, Eigen::InnerStride<3>>(val.data() + 1, val.size() / 3),
          model_.fTime, pathJoint, "ry");
      setKeyframes(
          Eigen::Map<Eigen::VectorXd, 0, Eigen::InnerStride<3>>(val.data() + 2, val.size() / 3),
          model_.fTime, pathJoint, "rz");

      val = lt.col(j);
      setKeyframes(
          Eigen::Map<Eigen::VectorXd, 0, Eigen::InnerStride<3>>(val.data() + 0, val.size() / 3),
          model_.fTime, pathJoint, "tx");
      setKeyframes(
          Eigen::Map<Eigen::VectorXd, 0, Eigen::InnerStride<3>>(val.data() + 1, val.size() / 3),
          model_.fTime, pathJoint, "ty");
      setKeyframes(
          Eigen::Map<Eigen::VectorXd, 0, Eigen::InnerStride<3>>(val.data() + 2, val.size() / 3),
          model_.fTime, pathJoint, "tz");
    }
    status = setSkinCluster(model_.boneName, model_.w, gb);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  setResult(joints);
  /*status = dgMod_.doIt();
  CHECK_MSTATUS_AND_RETURN_IT(status);

  setResult(name_);*/

  return MS::kSuccess;
}

MStatus DemBonesCmd::setKeyframes(const Eigen::VectorXd& val, const Eigen::VectorXd& fTime,
                                  const MDagPath& pathJoint, const MString& attributeName) {
  MStatus status;
  int idx = 0;
  int nFr = (int)fTime.size();
  MFnDagNode fnNode(pathJoint, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MPlug plug = fnNode.findPlug(attributeName, false, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MFnAnimCurve fnCurve;
  MObject oCurve = fnCurve.create(plug, nullptr, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MTime time;
  MTimeArray timeArray(nFr, time);
  MDoubleArray values(nFr);
  for (int i = 0; i < nFr; ++i) {
    timeArray[i].setValue(fTime(i));
    values[i] = val(i);
  }
  status = fnCurve.addKeys(&timeArray, &values);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  return MS::kSuccess;
}

MStatus DemBonesCmd::setSkinCluster(const std::vector<std::string>& name,
                                    const Eigen::SparseMatrix<double>& w,
                                    const Eigen::MatrixXd& gb) {
  MStatus status;

  // Assume neutral is on frame 0
  MTime time = MAnimControl::currentTime();
  time.setValue(0.0);
  MAnimControl::setCurrentTime(time);

  // Skin a duplicate of the mesh
  MStringArray duplicate;
  MGlobal::executeCommand("duplicate -rr " + pathMesh_.partialPathName(), duplicate);

  MString cmd("skinCluster -tsb");
  Eigen::SparseMatrix<double> wT = w.transpose();
  int nB = (int)name.size();
  MFnMesh fnMesh(pathMesh_, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MDoubleArray weights(fnMesh.numVertices() * nB);
  MIntArray influenceIndices;
  for (int i = 0; i < nB; ++i) {
    influenceIndices.append(i);
    cmd += MString(" ") + name[i].c_str();
    for (Eigen::SparseMatrix<double>::InnerIterator it(wT, i); it; ++it) {
      weights[(int)it.row() * nB + i] = it.value();
    }
  }

  cmd += " " + duplicate[0];
  MStringArray result;
  MGlobal::executeCommand(cmd, result);

  MObject oSkin;
  status = getDependNode(result[0], oSkin);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MFnSkinCluster fnSkin(oSkin, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  MObject oSet = fnSkin.deformerSet();
  MFnSet fnSet(oSet, &status);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  MSelectionList members;
  fnSet.getMembers(members, false);
  MDagPath path;
  MObject components;
  members.getDagPath(0, path, components);

  fnSkin.setWeights(path, components, influenceIndices, weights, true);

  return MS::kSuccess;
}

Eigen::Matrix4d DemBonesCmd::toMatrix4d(const MMatrix& m) {
  Eigen::Matrix4d mat;
  mat << m[0][0], m[0][1], m[0][2], m[0][3], m[1][0], m[1][1], m[1][2], m[1][3], m[2][0], m[2][1],
      m[2][2], m[2][3], m[3][0], m[3][1], m[3][2], m[3][3];
  mat.transposeInPlace();
  return mat;
}

MStatus DemBonesCmd::undoIt() {
  MStatus status;

  /*status = dgMod_.undoIt();
  CHECK_MSTATUS_AND_RETURN_IT(status);
*/
  return MS::kSuccess;
}

#ifdef DEM_BONES_DEM_BONES_MAT_BLOCKS_UNDEFINED
#undef blk4
#undef rotMat
#undef transVec
#undef vec3
#undef DEM_BONES_MAT_BLOCKS
#endif