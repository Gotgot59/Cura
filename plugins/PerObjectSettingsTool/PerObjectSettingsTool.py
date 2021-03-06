# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Tool import Tool
from UM.Scene.Selection import Selection
from UM.Application import Application
from UM.Preferences import Preferences
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator

##  This tool allows the user to add & change settings per node in the scene.
#   The settings per object are kept in a ContainerStack, which is linked to a node by decorator.
class PerObjectSettingsTool(Tool):
    def __init__(self):
        super().__init__()
        self._model = None

        self.setExposedProperties("SelectedObjectId", "ContainerID", "SelectedActiveExtruder")

        self._advanced_mode = False
        self._multi_extrusion = False

        Selection.selectionChanged.connect(self.propertyChanged)

        Preferences.getInstance().preferenceChanged.connect(self._onPreferenceChanged)
        self._onPreferenceChanged("cura/active_mode")

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)
        self._onGlobalContainerChanged()

    def event(self, event):
        return False

    def getSelectedObjectId(self):
        selected_object = Selection.getSelectedObject(0)
        selected_object_id = id(selected_object)
        return selected_object_id

    def getContainerID(self):
        selected_object = Selection.getSelectedObject(0)
        try:
            return selected_object.callDecoration("getStack").getId()
        except AttributeError:
            return ""

    ##  Gets the active extruder of the currently selected object.
    #
    #   \return The active extruder of the currently selected object.
    def getSelectedActiveExtruder(self):
        selected_object = Selection.getSelectedObject(0)
        return selected_object.callDecoration("getActiveExtruder")

    ##  Changes the active extruder of the currently selected object.
    #
    #   \param extruder_stack_id The ID of the extruder to print the currently
    #   selected object with.
    def setSelectedActiveExtruder(self, extruder_stack_id):
        selected_object = Selection.getSelectedObject(0)
        stack = selected_object.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            selected_object.addDecorator(SettingOverrideDecorator())
        selected_object.callDecoration("setActiveExtruder", extruder_stack_id)

    def _onPreferenceChanged(self, preference):
        if preference == "cura/active_mode":
            self._advanced_mode = Preferences.getInstance().getValue(preference) == 1
            self._updateEnabled()

    def _onGlobalContainerChanged(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            self._multi_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1
            self._updateEnabled()

    def _updateEnabled(self):
        Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, self._advanced_mode or self._multi_extrusion)