#ifndef SWINGTWIST_SWINGTWISTNODE_H
#define SWINGTWIST_SWINGTWISTNODE_H

#include <maya/MPxNode.h>

class SwingTwistNode : public MPxNode {
 public:
  SwingTwistNode();
  virtual ~SwingTwistNode();
  static void* creator();

  virtual MStatus compute(const MPlug& plug, MDataBlock& data);

  static MStatus initialize();
  static MTypeId id;
  static const MString kName;
  static MObject aOutMatrix;
  static MObject aRestMatrix;
  static MObject aTargetRestMatrix;
  static MObject aInMatrix;
  static MObject aTwistWeight;
  static MObject aSwingWeight;
  static MObject aTwistAxis;
};

#endif
