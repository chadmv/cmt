#ifndef SWINGTWIST_SWINGTWISTCMD_H
#define SWINGTWIST_SWINGTWISTCMD_H

#include <maya/MArgDatabase.h>
#include <maya/MArgList.h>
#include <maya/MDGModifier.h>
#include <maya/MGlobal.h>
#include <maya/MObject.h>
#include <maya/MPxCommand.h>
#include <maya/MSelectionList.h>
#include <maya/MSyntax.h>

#include <iostream>

class SwingTwistCmd : public MPxCommand {
 public:
  virtual MStatus doIt(const MArgList& argList);
  virtual MStatus redoIt();
  virtual MStatus undoIt();
  virtual bool isUndoable() const;

  static void* creator();
  static MSyntax newSyntax();

  static const MString kName;
  static const char* kNameShort;
  static const char* kNameLong;
  static const char* kTwistShort;
  static const char* kTwistLong;
  static const char* kSwingShort;
  static const char* kSwingLong;
  static const char* kTwistAxisShort;
  static const char* kTwistAxisLong;

private:
  MDGModifier dgMod_;
  MString name_;
  MObject oNode_;

};


#endif
