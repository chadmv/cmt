from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel


class OptionBox(object):
    """Class that wraps Maya's option box functionality.

    Maya's menu option box functionality is a bit convoluted and not well documented
    so this class can be used to simplify working with the option box.

    Users can derive from this class and implement the following four methods:

        * create_ui - Create any UI elements to display in the option box.
        * on_apply - Implement what should happen when the user hits Apply.
        * on_reset - Reset all your widgets to their default or saved values.
        * on_save - Save all the widget settings to optionVar or QSettings

    See cmt.rig.twistdecomposition.Options for a sample implementation.
    """

    def __init__(self, title, help_url=None):
        layout = mel.eval("getOptionBox")
        cmds.setParent(layout)
        mel.eval('setOptionBoxTitle("{}");'.format(title))
        self.create_ui()

        apply_close_button = mel.eval("getOptionBoxApplyAndCloseBtn;")
        cmds.button(apply_close_button, e=True, command=self._apply_and_close)
        apply_button = mel.eval("getOptionBoxApplyBtn;")
        cmds.button(apply_button, e=True, command=self._on_apply)
        close_button = mel.eval("getOptionBoxCloseBtn;")
        cmds.button(close_button, e=True, command=self._close)

        if help_url:
            help_item = mel.eval("getOptionBoxHelpItem;")
            cmds.menuItem(
                help_item,
                e=True,
                label="Help on {}".format(title),
                command='import webbrowser; webbrowser.open("{}")'.format(help_url),
            )

    def show(self):
        mel.eval("showOptionBox")
        # In getOptionBox.mel showOptionBox, it sets the Reset and Save menu item
        # commands in MEL so they expect MEL code.  We want Python so override the
        # commands after showing the option box in order to use Python
        reset_item = mel.eval("$tmp = $gOptionBoxEditMenuResetItem")
        cmds.menuItem(reset_item, e=True, command=self._on_reset)
        save_item = mel.eval("$tmp = $gOptionBoxEditMenuSaveItem")
        cmds.menuItem(save_item, e=True, command=self._on_save)

    def create_ui(self):
        raise NotImplementedError("OptionBox.create_ui not implemented")

    def _on_apply(self, *args):
        """Call back called when the Apply button is pressed.

        The only reason this method exists is so the derived on_apply doesn't have to
        have any args.

        :param args: Callback args.
        """
        self.on_apply()

    def on_apply(self):
        raise NotImplementedError("OptionBox.on_apply not implemented")

    def _on_reset(self, *args):
        """Call back called when the Reset settings menu item is pressed.

        The only reason this method exists is so the derived on_reset doesn't have to
        have any args.

        :param args: Callback args.
        """
        self.on_reset()

    def on_reset(self):
        raise NotImplementedError("OptionBox.on_reset not implemented")

    def _on_save(self, *args):
        """Call back called when the Save settings menu item is pressed.

        The only reason this method exists is so the derived on_save doesn't have to
        have any args.

        :param args: Callback args.
        """
        self.on_save()

    def on_save(self):
        raise NotImplementedError("OptionBox.on_save not implemented")

    def _apply_and_close(self, *args, **kwargs):
        """Create the twist decomposition and close the option box."""
        self.on_apply()
        mel.eval("saveOptionBoxSize")
        self._close()

    def _close(self, *args, **kwargs):
        mel.eval("hideOptionBox")
