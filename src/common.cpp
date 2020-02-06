#include "common.h"

#include <maya/MArrayDataBuilder.h>
#include <maya/MArrayDataHandle.h>
#include <maya/MDataHandle.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnMesh.h>
#include <maya/MGlobal.h>
#include <maya/MItMeshVertex.h>
#include <maya/MSelectionList.h>
#include <algorithm>

MStatus JumpToElement(MArrayDataHandle& hArray, unsigned int index) {
  MStatus status;
  status = hArray.jumpToElement(index);
  if (MFAIL(status)) {
    MArrayDataBuilder builder = hArray.builder(&status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    builder.addElement(index, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    status = hArray.set(builder);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    status = hArray.jumpToElement(index);
    CHECK_MSTATUS_AND_RETURN_IT(status);
  }
  return status;
}

void StartProgress(const MString& title, unsigned int count) {
  if (MGlobal::mayaState() == MGlobal::kInteractive) {
    MString message = "progressBar -e -bp -ii true -st \"";
    message += title;
    message += "\" -max ";
    message += count;
    message += " $gMainProgressBar;";
    MGlobal::executeCommand(message);
  }
}

void StepProgress(int step) {
  if (MGlobal::mayaState() == MGlobal::kInteractive) {
    MString message = "progressBar -e -s ";
    message += step;
    message += " $gMainProgressBar;";
    MGlobal::executeCommand(message);
  }
}

bool ProgressCancelled() {
  if (MGlobal::mayaState() == MGlobal::kInteractive) {
    int cmdResult = 0;
    MGlobal::executeCommand("progressBar -query -isCancelled $gMainProgressBar", cmdResult);
    return cmdResult != 0;
  }
  return false;
}

void EndProgress() {
  if (MGlobal::mayaState() == MGlobal::kInteractive) {
    MGlobal::executeCommand("progressBar -e -ep $gMainProgressBar;");
  }
}

bool isShapeNode(MDagPath& path) {
  return path.node().hasFn(MFn::kMesh) || path.node().hasFn(MFn::kNurbsCurve) ||
         path.node().hasFn(MFn::kNurbsSurface);
}

MStatus getShapeNode(MDagPath& path, bool intermediate) {
  MStatus status;

  if (isShapeNode(path)) {
    // Start at the transform so we can honor the intermediate flag.
    path.pop();
  }

  if (path.hasFn(MFn::kTransform)) {
    unsigned int shapeCount = path.childCount();

    for (unsigned int i = 0; i < shapeCount; ++i) {
      status = path.push(path.child(i));
      CHECK_MSTATUS_AND_RETURN_IT(status);
      if (!isShapeNode(path)) {
        path.pop();
        continue;
      }

      MFnDagNode fnNode(path, &status);
      CHECK_MSTATUS_AND_RETURN_IT(status);
      if ((!fnNode.isIntermediateObject() && !intermediate) ||
          (fnNode.isIntermediateObject() && intermediate)) {
        return MS::kSuccess;
      }
      // Go to the next shape
      path.pop();
    }
  }

  // No valid shape node found.
  return MS::kFailure;
}

MStatus getDagPath(const MString& name, MDagPath& path) {
  MStatus status;
  MSelectionList list;
  status = MGlobal::getSelectionListByName(name, list);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = list.getDagPath(0, path);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  return MS::kSuccess;
}

MStatus getDependNode(const MString& name, MObject& oNode) {
  MStatus status;
  MSelectionList list;
  status = MGlobal::getSelectionListByName(name, list);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = list.getDependNode(0, oNode);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  return MS::kSuccess;
}

MStatus DeleteIntermediateObjects(MDagPath& path) {
  MStatus status;
  MDagPath pathMesh(path);
  while (getShapeNode(pathMesh, true) == MS::kSuccess) {
    status = MGlobal::executeCommand("delete " + pathMesh.partialPathName());
    CHECK_MSTATUS_AND_RETURN_IT(status);
    pathMesh = MDagPath(path);
  }
  return MS::kSuccess;
}
