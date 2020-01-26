import maya.OpenMayaMPx as OpenMayaMPx
import cmt.plugins.swingtwist as swingtwist


def initializePlugin(obj):
    plugin = OpenMayaMPx.MFnPlugin(obj, 'Chad Vernon', '1.0', 'Any')

    # plugin.registerNode(swingtwist.SwingTwistNode.name, swingtwist.SwingTwistNode.id,
    #                     swingtwist.SwingTwistNode.creator, swingtwist.SwingTwistNode.initialize)
    #
    # plugin.registerCommand(swingtwist.SwingTwistCommand.name, swingtwist.SwingTwistCommand.creator,
    #                        swingtwist.SwingTwistCommand.command_syntax)
    #

def uninitializePlugin(obj):
    plugin = OpenMayaMPx.MFnPlugin(obj)

    # plugin.deregisterCommand(swingtwist.SwingTwistCommand.name)
    # plugin.deregisterNode(swingtwist.SwingTwistNode.id)
