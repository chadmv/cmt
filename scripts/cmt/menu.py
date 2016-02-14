"""
Contains the menu creation functions as wells as any other functions the menus rely on.
"""

import webbrowser
import maya.cmds as cmds
import maya.mel as mel
import cmt


def create_menu():
    """Creates the CMT menu."""
    gmainwindow = mel.eval('$tmp = $gMainWindow;')
    menu = cmds.menu(parent=gmainwindow, tearOff=True, label='CMT')

    rig_menu = cmds.menuItem(subMenu=True, tearOff=True, parent=menu, label='Rigging')
    cmds.menuItem(parent=rig_menu,
                  label='Orient Joints',
                  command='import cmt.rig.orientjoints as oj; oj.OrientJointsWindow()',
                  image='orientJoint.png')
    cmds.menuItem(parent=rig_menu,
                  label='Rename Chain',
                  command='import cmt.name; cmt.name.rename_chain_ui()',
                  image='menuIconModify.png',
                  imageOverlayLabel='name')

    utility_menu = cmds.menuItem(subMenu=True, tearOff=True, parent=menu, label='Utility')
    cmds.menuItem(parent=utility_menu,
                  label='Unit Test Runner',
                  command='import cmt.test.mayaunittestui; cmt.test.mayaunittestui.show()',
                  imageOverlayLabel='Test')
    cmds.menuItem(parent=utility_menu,
                  label='Resource Browser',
                  command='import maya.app.general.resourceBrowser as rb; rb.resourceBrowser().run()',
                  imageOverlayLabel='name')

    cmds.menuItem(parent=menu, divider=True, dividerLabel='About')
    cmds.menuItem(parent=menu,
                  label='About CMT',
                  command='import cmt.menu; cmt.menu.about()',
                  image='menuIconHelp.png')
    cmds.menuItem(parent=menu,
                  label='Documentation',
                  command='import cmt.menu; cmt.menu.documentation()',
                  image='menuIconHelp.png')


def documentation():
    """Opens the documentation web page."""
    webbrowser.open('https://github.com/chadmv/cmt/wiki')


def about():
    """Displays the CMT About dialog."""
    name = 'cmt_about'
    if cmds.window(name, exists=True):
        cmds.deleteUI(name, window=True)
    if cmds.windowPref(name, exists=True):
        cmds.windowPref(name, remove=True)
    window = cmds.window(name, title='About CMT', widthHeight=(600, 500), sizeable=False)
    form = cmds.formLayout(nd=100)
    text = cmds.scrollField(editable=False, wordWrap=True, text=cmt.__doc__.strip())
    button = cmds.button(label='Documentation', command='import cmt.menu; cmt.menu.documentation()')
    margin = 8
    cmds.formLayout(form, e=True,
                    attachForm=(
                        (text, 'top', margin),
                        (text, 'right', margin),
                        (text, 'left', margin),
                        (text, 'bottom', 40),
                        (button, 'right', margin),
                        (button, 'left', margin),
                        (button, 'bottom', margin),
                    ),
                    attachControl=(
                        (button, 'top', 2, text)
                    ))
    cmds.showWindow(window)

