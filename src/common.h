#ifndef CMT_COMMON_H
#define CMT_COMMON_H

#include <maya/MDagPath.h>
#include <maya/MDoubleArray.h>
#include <maya/MFloatVectorArray.h>
#include <maya/MIntArray.h>
#include <maya/MMatrix.h>
#include <maya/MPoint.h>
#include <maya/MPointArray.h>
#include <maya/MString.h>
#include <map>
#include <vector>
#include <set>


MStatus JumpToElement(MArrayDataHandle& hArray, unsigned int index);

/**
  Helper function to start a new progress bar.
  @param[in] title Status title.
  @param[in] count Progress bar maximum count.
*/
void StartProgress(const MString& title, unsigned int count);


/**
  Helper function to increase the progress bar by the specified amount.
  @param[in] step Step amount.
*/
void StepProgress(int step);


/**
  Check if the progress has been cancelled.
  @return true if the progress has been cancelled.
*/
bool ProgressCancelled();


/**
  Ends any running progress bar.
*/
void EndProgress();


/**
  Checks if the path points to a shape node.
  @param[in] path A dag path.
  @return true if the path points to a shape node.
 */
bool isShapeNode(MDagPath& path);


/**
  Ensures that the given dag path points to a non-intermediate shape node.
  @param[in,out] path Path to a dag node that could be a transform or a shape.
  On return, the path will be to a shape node if one exists.
  @param[in] intermediate true to get the intermediate shape.
  @return MStatus.
 */
MStatus getShapeNode(MDagPath& path, bool intermediate=false);


/**
  Get the MDagPath of an object.
  @param[in] name Name of a dag node.
  @param[out] path Storage for the dag path.
 */
MStatus getDagPath(const MString& name, MDagPath& path);

/**
  Get the MObject of an object.
  @param[in] name Name of the node.
  @param[out] oNode Storage for the MObject.
 */
MStatus getDependNode(const MString& name, MObject& oNode);


/**
  Delete all intermediate shapes of the given dag path.
  @param[in] path MDagPath.
 */
MStatus DeleteIntermediateObjects(MDagPath& path);


template <typename T>
struct ThreadData {
  unsigned int start;
  unsigned int end;
  unsigned int numTasks;
  T* pData;
};


/**
  Creates the data stuctures that will be sent to each thread.  Divides the vertices into
  discrete chunks to be evaluated in the threads.
  @param[in] taskCount The number of individual tasks we want to divide the calculation into.
  @param[in] elementCount The number of vertices or elements to be divided up.
  @param[in] taskData The TaskData or BindData object.
  @param[out] threadData The array of ThreadData objects.  It is assumed the array is of size taskCount.
*/
template <typename T>
void CreateThreadData(int taskCount, unsigned int elementCount, T* taskData, ThreadData<T>* threadData) {
  unsigned int taskLength = (elementCount + taskCount - 1) / taskCount;
  unsigned int start = 0;
  unsigned int end = taskLength;
  int lastTask = taskCount - 1;
  for(int i = 0; i < taskCount; i++) {
    if (i == lastTask) {
      end = elementCount;
    }
    threadData[i].start = start;
    threadData[i].end = end;
    threadData[i].numTasks = taskCount;
    threadData[i].pData = taskData;

    start += taskLength;
    end += taskLength;
  }
}

#endif