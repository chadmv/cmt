#include "demBonesCmd.h"
#include "common.h"

#include <maya/MAnimControl.h>
#include <maya/MDagPath.h>
#include <maya/MFnAnimCurve.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnMatrixData.h>
#include <maya/MFnMesh.h>
#include <maya/MFnSet.h>
#include <maya/MFnSkinCluster.h>
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
    model_.weightsSmoothStep = argData.flagArgumentDouble(kWeightsSmoothStepShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    int boneCount = argData.flagArgumentInt(kBonesShort, 0, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    model_.nB += (boneCount - model_.nB);
  }

  if (model_.nB == 0) {
    if (!argData.isFlagSet(kBonesShort)) {
      MGlobal::displayError("No joints found. Need to set the number of bones (-b/-bones)");
      return MS::kInvalidParameter;
    }

    model_.nB = argData.flagArgumentInt(kBonesShort, 0, &status);
    std::cerr << "Initializing bones: 1";
    model_.init();
    std::cerr << std::endl;
  }

  model_.compute();

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

  int frameCount = static_cast<int>(endFrame - startFrame + 1);

  MTime time = MAnimControl::currentTime();
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

      //#pragma omp parallel for
      for (int i = 0; i < model_.nV; i++) {
        model_.v.col(i).segment<3>((start + f) * 3) << points[i].x, points[i].y, points[i].z;
      }
    }
    model_.fStart(s + 1) = model_.fStart(s) + model_.nF;
  }

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

  model_.nB = 0;  // TODO: Use existing bones
  // model_.boneName = importer.jointName;  // TODO: Use existing bones

  model_.parent.resize(model_.nB);
  model_.bind.resize(model_.nS * 4, model_.nB * 4);
  model_.preMulInv.resize(model_.nS * 4, model_.nB * 4);
  model_.rotOrder.resize(model_.nS * 3, model_.nB);

  // TODO: Use existing bones
  /*for (int j = 0; j < model_.nB; j++) {
    std::string nj = model_.boneName[j];

    model_.parent(j) = -1;
    for (int k = 0; k < model_.nB; k++) {
      if (model_.boneName[k] == importer.parent[nj]) {
        model_.parent(j) = k;
      }
    }
    model_.bind.blk4(s, j) = importer.bind[nj];
    model_.preMulInv.blk4(s, j) = importer.preMulInv[nj];
    model_.rotOrder.vec3(s, j) = importer.rotOrder[nj];
  }*/

  // TODO: Use existing bones
  Eigen::MatrixXd wd(0, 0);
  /*if (importer.wT.size() != 0) {
    wd = MatrixXd::Zero(model.nB, model.nV);
    for (int j = 0; j < model.nB; j++){
      wd.row(j) = importer.wT[model.boneName[j]].transpose();
    }
  }*/

  model_.m.resize(model_.nF * 4, model_.nB * 4);

  model_.w = (wd / model_.nS).sparseView(1, 1e-20);
  bool hasKeyFrame = false;
  if (!hasKeyFrame) {
    model_.m.resize(0, 0);
  }

  // TODO: Use existing bones
  model_.origM = model_.m;

  return MS::kSuccess;
}

MStatus DemBonesCmd::redoIt() {
  MStatus status;
  clearResult();

  bool needCreateJoints = (model_.boneName.size() != model_.nB);
  std::vector<std::string> newBoneNames;
  if (needCreateJoints) {
    // model.boneName.resize(model.nB);
    int creationCount = model_.nB - static_cast<int>(model_.boneName.size());
    for (int j = 0; j < creationCount; j++) {
      std::ostringstream s;
      s << "dembones_joint" << j;
      model_.boneName.push_back(s.str());
      newBoneNames.push_back(s.str());
    }
  }

  for (int s = 0; s < model_.nS; ++s) {
    Eigen::MatrixXd lr, lt, gb, lbr, lbt;
    model_.computeRTB(s, lr, lt, gb, lbr, lbt, false);

    Eigen::VectorXd val;
    for (int j = 0; j < newBoneNames.size(); ++j) {
      MString name(model_.boneName[j].c_str());
      MGlobal::executeCommand("createNode \"joint\" -n \"" + name + "\"");
    }
    for (int j = 0; j < model_.boneName.size(); ++j) {
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
  MObject oCurve = fnCurve.create(plug);
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

MStatus DemBonesCmd::undoIt() {
  MStatus status;

  /*status = dgMod_.undoIt();
  CHECK_MSTATUS_AND_RETURN_IT(status);
*/
  return MS::kSuccess;
}
