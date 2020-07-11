
#include <maya/MFnPlugin.h>

#include "demBonesCmd.h"
#include "ikRigNode.h"
#include "rbfNode.h"
#include "swingTwistCmd.h"
#include "swingTwistNode.h"

MStatus initializePlugin(MObject obj) {
  MStatus status;

  MFnPlugin plugin(obj, "Chad Vernon", "1.0", "any");

  status = plugin.registerNode(SwingTwistNode::kName, SwingTwistNode::id, SwingTwistNode::creator,
                               SwingTwistNode::initialize);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.registerCommand(SwingTwistCmd::kName, SwingTwistCmd::creator,
                                  SwingTwistCmd::newSyntax);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.registerNode(RBFNode::kName, RBFNode::id, RBFNode::creator, RBFNode::initialize);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.registerCommand(DemBonesCmd::kName, DemBonesCmd::creator, DemBonesCmd::newSyntax);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  status = plugin.registerNode(IKRigNode::kName, IKRigNode::id, IKRigNode::creator,
                               IKRigNode::initialize);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  return status;
}

MStatus uninitializePlugin(MObject obj) {
  MStatus status;
  MFnPlugin plugin(obj);
  status = plugin.deregisterNode(IKRigNode::id);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.deregisterCommand(DemBonesCmd::kName);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.deregisterNode(RBFNode::id);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.deregisterCommand(SwingTwistCmd::kName);
  CHECK_MSTATUS_AND_RETURN_IT(status);
  status = plugin.deregisterNode(SwingTwistNode::id);
  CHECK_MSTATUS_AND_RETURN_IT(status);

  return status;
}
