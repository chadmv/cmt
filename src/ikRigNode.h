#ifndef IKRIG_IKRIGNODE_H
#define IKRIG_IKRIGNODE_H

#include <maya/MArrayDataHandle.h>
#include <maya/MFloatVector.h>
#include <maya/MMatrix.h>
#include <maya/MMatrixArray.h>
#include <maya/MPoint.h>
#include <maya/MPxNode.h>
#include <maya/MQuaternion.h>
#include <maya/MVectorArray.h>

#include <queue>

class IKRigNode : public MPxNode {
 public:
  enum IKRigPart {
    IKRig_Root,
    IKRig_Hips,
    IKRig_Chest,
    IKRig_Neck,
    IKRig_Head,

    IKRig_LeftClavicle,
    IKRig_LeftShoulder,
    IKRig_LeftElbow,
    IKRig_LeftHand,
    IKRig_LeftUpLeg,
    IKRig_LeftLoLeg,
    IKRig_LeftFoot,

    IKRig_RightClavicle,
    IKRig_RightShoulder,
    IKRig_RightElbow,
    IKRig_RightHand,
    IKRig_RightUpLeg,
    IKRig_RightLoLeg,
    IKRig_RightFoot,

    IKRig_LeftThumb01,
    IKRig_LeftThumb02,
    IKRig_LeftThumb03,
    IKRig_LeftIndex01,
    IKRig_LeftIndex02,
    IKRig_LeftIndex03,
    IKRig_LeftMiddle01,
    IKRig_LeftMiddle02,
    IKRig_LeftMiddle03,
    IKRig_LeftRing01,
    IKRig_LeftRing02,
    IKRig_LeftRing03,
    IKRig_LeftPinky01,
    IKRig_LeftPinky02,
    IKRig_LeftPinky03,

    IKRig_RightThumb01,
    IKRig_RightThumb02,
    IKRig_RightThumb03,
    IKRig_RightIndex01,
    IKRig_RightIndex02,
    IKRig_RightIndex03,
    IKRig_RightMiddle01,
    IKRig_RightMiddle02,
    IKRig_RightMiddle03,
    IKRig_RightRing01,
    IKRig_RightRing02,
    IKRig_RightRing03,
    IKRig_RightPinky01,
    IKRig_RightPinky02,
    IKRig_RightPinky03,

    IKRig_Count
  };

  IKRigNode();
  virtual ~IKRigNode();
  static void* creator();

  virtual MStatus compute(const MPlug& plug, MDataBlock& data);

  static MStatus initialize();
  static MTypeId id;
  static const MString kName;
  static MObject aOutTranslate;
  static MObject aOutRotate;
  static MObject aOutRotateX;
  static MObject aOutRotateY;
  static MObject aOutRotateZ;

  // Input Skeleton
  static MObject aInMatrix;
  static MObject aInRestMatrix;
  static MObject aTargetRestMatrix;
  static MObject aLeftLegTwistOffset;
  static MObject aRightLegTwistOffset;
  static MObject aStrideScale;
  static MObject aRootMotionScale;
  static MObject aCharacterScale;
  static MObject aHipSpace;
  static MObject aLeftHandSpace;
  static MObject aRightHandSpace;
  static MObject aLeftFootSpace;
  static MObject aRightFootSpace;
  static MObject aCalculateRootMotion;
  static MObject aHipOffset;
  static MObject aChestOffset;
  static MObject aLeftHandOffset;
  static MObject aRightHandOffset;

 private:
  static void affects(const MObject& attribute);

  MMatrix calculateRootMotion();

  MStatus calculateHipIk(float hipSpace, MArrayDataHandle& hOutputTranslate,
                         MArrayDataHandle& hOutputRotate);

  MStatus calculateLegIk(float footSpace, unsigned int upLeg, unsigned int loLeg, unsigned int foot,
                         const MMatrix& hips, float twist, MArrayDataHandle& hOutputTranslate,
                         MArrayDataHandle& hOutputRotate);

  MStatus calculateChestIk(MArrayDataHandle& hOutputTranslate, MArrayDataHandle& hOutputRotate);

  MStatus calculateArmIk(float handSpace, unsigned int clavicleIdx, unsigned int upArm,
                         unsigned int loArm, unsigned int hand, const MMatrix& chest, float twist,
                         const MMatrix& offset, MArrayDataHandle& hOutputTranslate,
                         MArrayDataHandle& hOutputRotate, MQuaternion* rotationOffset = nullptr);

  MStatus calculateHeadIk(const MMatrix& chest, MArrayDataHandle& hOutputTranslate,
                          MArrayDataHandle& hOutputRotate);

  MStatus calculateFingerIk(unsigned int finger[3], unsigned int handIdx, const MMatrix& hand, const MQuaternion& handOffset,
                            MArrayDataHandle& hOutputTranslate, MArrayDataHandle& hOutputRotate);

  MVector position(const MMatrix& m) { return MVector(m[3][0], m[3][1], m[3][2]); }

  MMatrix offsetMatrix(const MMatrix& m, const MQuaternion& r, const MVector& t);

  MMatrix scaleRelativeTo(unsigned int inputChildIdx, unsigned int inputParentIdx, double scale,
                          const MMatrix& targetParent, float localToWorldSpace = 0.0f,
                          const MMatrix& offset = MMatrix::identity, MQuaternion* rotationOffset = nullptr);

  MMatrix orientConstraint(unsigned int partIdx, unsigned int parentIdx, const MMatrix& parent,
                           const MQuaternion& offset = MQuaternion::identity);
  MMatrix parentConstraint(unsigned int partIdx, unsigned int parentIdx, float scale = 1.0f,
                           const MMatrix& offset = MMatrix::identity);

  void calculateTwoBoneIk(const MMatrix& root, const MMatrix& mid, const MMatrix& effector,
                          const MMatrix& target, const MVector& pv, MMatrix& ikA, MMatrix& ikB);

  void twoBoneIk(const MVector& a, const MVector& b, const MVector& c, const MVector& d,
                 const MVector& t, const MVector& pv, MQuaternion& a_gr, MQuaternion& b_gr);

  MStatus setOutput(MArrayDataHandle& hOutputTranslate, MArrayDataHandle& hOutputRotate,
                    unsigned int bodyPart, const MMatrix& matrix);
  float clamp(float inValue, float minValue, float maxValue) {
    if (inValue < minValue) {
      return minValue;
    }
    if (inValue > maxValue) {
      return maxValue;
    }
    return inValue;
  }

  template <class T>
  T lerp(const T& a, const T& b, double t) {
    return (b * t) + a * (1.0 - t);
  }

  MMatrixArray inputMatrix_;
  MMatrixArray inputRestMatrix_;
  MMatrixArray targetRestMatrix_;
  std::vector<MQuaternion> rotationDelta_;
  MVectorArray translationDelta_;
  MMatrix scaledRootMotion_;
  MMatrix toScaledRootMotion_;
  MMatrix hips_;
  MMatrix chest_;
  MMatrix leftHand_;
  MMatrix rightHand_;
  MMatrix leftHandOffset_;
  MMatrix rightHandOffset_;
  MMatrix hipOffset_;
  MMatrix chestOffset_;
  double hipScale_;
  double spineScale_;
  double neckScale_;
  double strideScale_;
  double rootMotionScale_;
  double characterScale_;
  std::queue<MVector> prevForward_;
};

#endif
