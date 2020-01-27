"""
Contains the menu creation functions as wells as any other functions the menus rely on.
"""

import webbrowser
import maya.cmds as cmds
import maya.mel as mel
from cmt.settings import DOCUMENTATION_ROOT


def create_menu():
    """Creates the CMT menu."""
    gmainwindow = mel.eval("$tmp = $gMainWindow;")
    menu = cmds.menu(parent=gmainwindow, tearOff=True, label="CMT")

    # Rig
    rig_menu = cmds.menuItem(subMenu=True, tearOff=True, parent=menu, label="Rigging")
    cmds.menuItem(
        parent=rig_menu,
        label="Freeze to offsetParentMatrix",
        command="import cmt.rig.common; cmt.rig.common.freeze_to_parent_offset()",
    )
    cmds.menuItem(
        parent=rig_menu,
        label="CQueue",
        command="import cmt.cqueue.window; cmt.cqueue.window.show()",
        imageOverlayLabel="cqueue",
    )
    cmds.menuItem(parent=rig_menu, divider=True, dividerLabel="Skeleton")
    cmds.menuItem(
        parent=rig_menu,
        label="Orient Joints",
        command="import cmt.rig.orientjoints as oj; oj.OrientJointsWindow()",
        image="orientJoint.png",
    )
    cmds.menuItem(
        parent=rig_menu,
        label="Rename Chain",
        command="import cmt.name; cmt.name.rename_chain_ui()",
        image="menuIconModify.png",
        imageOverlayLabel="name",
    )
    cmds.menuItem(
        parent=rig_menu,
        label="Export Skeleton",
        command="import cmt.rig.skeleton as skeleton; skeleton.dump()",
        image="kinJoint.png",
    )
    cmds.menuItem(
        parent=rig_menu,
        label="Import Skeleton",
        command="import cmt.rig.skeleton as skeleton; skeleton.load()",
        image="kinJoint.png",
    )
    item = cmds.menuItem(
        parent=rig_menu,
        label="Connect Twist Joint",
        command="import cmt.rig.swingtwist as st; st.create_from_menu()",
    )
    cmds.menuItem(
        parent=rig_menu,
        insertAfter=item,
        optionBox=True,
        command="import cmt.rig.swingtwist as st; st.display_menu_options()",
    )
    cmds.menuItem(parent=rig_menu, divider=True, dividerLabel="Animation Rig")
    cmds.menuItem(
        parent=rig_menu,
        label="Control Creator",
        command="import cmt.rig.control_ui as control_ui; control_ui.show()",
        image="orientJoint.png",
    )
    cmds.menuItem(
        parent=rig_menu,
        label="Export Selected Control Curves",
        command="import cmt.rig.control as control; control.export_curves()",
    )

    cmds.menuItem(
        parent=rig_menu,
        label="Import Control Curves",
        command="import cmt.rig.control as control; control.import_curves()",
    )

    # Deform
    deform_menu = cmds.menuItem(subMenu=True, tearOff=True, parent=menu, label="Deform")
    cmds.menuItem(parent=deform_menu, divider=True, dividerLabel="Skinning")
    cmds.menuItem(
        parent=deform_menu,
        label="Export Skin Weights",
        command="import cmt.deform.skinio as skinio; skinio.export_skin()",
        image="exportSmoothSkin.png",
    )
    cmds.menuItem(
        parent=deform_menu,
        label="Import Skin Weights",
        command="import cmt.deform.skinio as skinio; skinio.import_skin(to_selected_shapes=True)",
        image="importSmoothSkin.png",
    )

    utility_menu = cmds.menuItem(
        subMenu=True, tearOff=True, parent=menu, label="Utility"
    )
    cmds.menuItem(
        parent=utility_menu,
        label="Unit Test Runner",
        command="import cmt.test.mayaunittestui; cmt.test.mayaunittestui.show()",
        imageOverlayLabel="Test",
    )
    cmds.menuItem(
        parent=utility_menu,
        label="Reload",
        command="import cmt.reloadmodules; cmt.reloadmodules.reload_modules()",
        imageOverlayLabel="Test",
    )
    cmds.menuItem(
        parent=utility_menu,
        label="Resource Browser",
        command="import maya.app.general.resourceBrowser as rb; rb.resourceBrowser().run()",
        imageOverlayLabel="name",
    )

    cmds.menuItem(
        parent=menu,
        label="Shapes UI",
        command="import cmt.deform.shapesui; cmt.deform.shapesui.show()",
    )

    cmds.menuItem(
        parent=menu,
        label="Run Script",
        command="import cmt.pipeline.runscript; cmt.pipeline.runscript.show()",
    )

    cmds.menuItem(parent=menu, divider=True, dividerLabel="About")
    cmds.menuItem(
        parent=menu,
        label="About CMT",
        command="import cmt.menu; cmt.menu.about()",
        image="menuIconHelp.png",
    )
    cmds.menuItem(
        parent=menu,
        label="Documentation",
        command="import cmt.menu; cmt.menu.documentation()",
        image="menuIconHelp.png",
    )


def documentation():
    """Opens the documentation web page."""
    webbrowser.open(DOCUMENTATION_ROOT)


def about():
    """Displays the CMT About dialog."""
    name = "cmt_about"
    if cmds.window(name, exists=True):
        cmds.deleteUI(name, window=True)
    if cmds.windowPref(name, exists=True):
        cmds.windowPref(name, remove=True)
    window = cmds.window(
        name, title="About CMT", widthHeight=(600, 500), sizeable=False
    )
    form = cmds.formLayout(nd=100)
    text = cmds.scrollField(editable=False, wordWrap=True, text=cmt.__doc__.strip())
    button = cmds.button(
        label="Documentation", command="import cmt.menu; cmt.menu.documentation()"
    )
    margin = 8
    cmds.formLayout(
        form,
        e=True,
        attachForm=(
            (text, "top", margin),
            (text, "right", margin),
            (text, "left", margin),
            (text, "bottom", 40),
            (button, "right", margin),
            (button, "left", margin),
            (button, "bottom", margin),
        ),
        attachControl=((button, "top", 2, text)),
    )
    cmds.showWindow(window)
