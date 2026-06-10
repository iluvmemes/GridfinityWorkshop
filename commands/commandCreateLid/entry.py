import adsk.core, adsk.fusion, traceback
import math
import os

from ...lib import configUtils
from ...lib import fusion360utils as futil
from ... import config
from ...lib.gridfinityUtils import const
from ...lib.gridfinityUtils.lidGenerator import createLidBody
from ...lib.gridfinityUtils.lidGeneratorInput import LidGeneratorInput
from ...lib.ui.commandUiState import CommandUiState
from ...lib.ui.unsupportedDesignTypeException import UnsupportedDesignTypeException

app = adsk.core.Application.get()
ui = app.userInterface

# Command identity information
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdLid'
CMD_NAME = 'Gridfinity lid'
CMD_Description = 'Create gridfinity lid with magnet pockets'

commandUIState = CommandUiState(CMD_NAME)

IS_PROMOTED = True

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

CONFIG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandConfig')
UI_INPUT_DEFAULTS_CONFIG_PATH = os.path.join(CONFIG_FOLDER_PATH, 'ui_input_defaults.json')

local_handlers = []

# Group IDs
LID_BASIC_SIZES_GROUP = 'lid_basic_sizes_group'
LID_DIMENSIONS_GROUP = 'lid_dimensions_group'
LID_MAGNET_GROUP = 'lid_magnet_group'
LID_HANDLE_GROUP = 'lid_handle_group'
LID_USER_CHANGES_GROUP = 'lid_user_changes_group'
LID_PREVIEW_GROUP = 'lid_preview_group'

# Buttons
LID_INPUT_CHANGES_SAVE_DEFAULTS = 'lid_input_changes_save_new_defaults'
LID_INPUT_CHANGES_RESET_TO_DEFAULTS = 'lid_input_changes_reset_to_defaults'
LID_INPUT_CHANGES_RESET_TO_FACTORY = 'lid_input_changes_factory_reset'

# Input IDs
LID_BASE_WIDTH_UNIT_INPUT_ID = 'lid_base_width_unit'
LID_BASE_LENGTH_UNIT_INPUT_ID = 'lid_base_length_unit'
LID_XY_CLEARANCE_INPUT_ID = 'lid_xy_clearance'
LID_BASES_X_INPUT_ID = 'lid_bases_x'
LID_BASES_Y_INPUT_ID = 'lid_bases_y'
LID_THICKNESS_INPUT_ID = 'lid_thickness'
LID_MAGNET_DIAMETER_INPUT_ID = 'lid_magnet_diameter'
LID_MAGNET_DEPTH_INPUT_ID = 'lid_magnet_depth'
LID_HAS_HANDLE_INPUT_ID = 'lid_has_handle'
LID_HANDLE_HEIGHT_INPUT_ID = 'lid_handle_height'
LID_HANDLE_EDGE_GAP_INPUT_ID = 'lid_handle_edge_gap'
LID_HANDLE_CORNER_FILLET_INPUT_ID = 'lid_handle_corner_fillet'
LID_HANDLE_SIDE_FILLET_INPUT_ID = 'lid_handle_side_fillet'
LID_LABEL_PRESET_DROPDOWN_ID = 'lid_label_preset'
LID_LABEL_WIDTH_INPUT_ID = 'lid_label_width'
LID_LABEL_LENGTH_INPUT_ID = 'lid_label_length'
LID_LABEL_MARGIN_INPUT_ID = 'lid_label_margin'
LID_LABEL_CORNER_FILLET_INPUT_ID = 'lid_label_corner_fillet'
LID_HANDLE_WARNING_INPUT_ID = 'lid_handle_warning'
LID_SHOW_PREVIEW_INPUT = 'lid_show_preview'
LID_SHOW_PREVIEW_MANUAL_INPUT = 'lid_show_preview_manual'

LABEL_PRESET_CUSTOM = 'Custom'
# preset name -> (label width across the handle, label length along the handle),
# cm; None means the corresponding custom input stays active. Names lead with
# the SKU printed on the label roll so users can match without converting.
LABEL_PRESETS = {
    LABEL_PRESET_CUSTOM: (None, None),
    'Niimbot/Phomemo T12*40 (12 x 40 mm)': (1.2, 4.0),
    'Niimbot/Phomemo T14*30 (14 x 30 mm)': (1.4, 3.0),
    'Niimbot/Phomemo T15*30 (15 x 30 mm)': (1.5, 3.0),
    'DYMO 11353 (13 x 25 mm)': (1.3, 2.5),
    'DYMO 11355 (19 x 51 mm)': (1.9, 5.1),
    'Brother TZe 9 mm tape': (0.9, None),
    'Brother TZe 12 mm tape': (1.2, None),
    'Brother TZe 18 mm tape': (1.8, None),
    'Brother TZe 24 mm tape': (2.4, None),
}
LABEL_PRESET_DEFAULT = 'Niimbot/Phomemo T12*40 (12 x 40 mm)'

# changes to any of these re-fit the handle margin/transition automatically so
# resizing the lid doesn't silently invalidate the selected label preset
HANDLE_AUTO_FIT_TRIGGER_IDS = [
    LID_BASES_X_INPUT_ID,
    LID_BASES_Y_INPUT_ID,
    LID_BASE_WIDTH_UNIT_INPUT_ID,
    LID_BASE_LENGTH_UNIT_INPUT_ID,
    LID_XY_CLEARANCE_INPUT_ID,
    LID_LABEL_PRESET_DROPDOWN_ID,
    LID_LABEL_WIDTH_INPUT_ID,
    LID_LABEL_LENGTH_INPUT_ID,
    LID_HAS_HANDLE_INPUT_ID,
    LID_HANDLE_HEIGHT_INPUT_ID,
    LID_HANDLE_EDGE_GAP_INPUT_ID,
    LID_HANDLE_CORNER_FILLET_INPUT_ID,
    LID_HANDLE_SIDE_FILLET_INPUT_ID,
]


def getErrorMessage(text="An unknown error occurred, please validate your inputs and try again"):
    stackTrace = traceback.format_exc()
    return f"{text}:<br>{stackTrace}"


def showErrorInMessageBox(text="An unknown error occurred, please validate your inputs and try again"):
    if ui:
        ui.messageBox(getErrorMessage(text), f"{CMD_NAME} Error")


def initDefaultUiState():
    global commandUIState
    commandUIState.initValue(LID_BASIC_SIZES_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(LID_DIMENSIONS_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(LID_MAGNET_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(LID_HANDLE_GROUP, True, adsk.core.GroupCommandInput.classType())
    commandUIState.initValue(LID_PREVIEW_GROUP, True, adsk.core.GroupCommandInput.classType())

    commandUIState.initValue(LID_BASE_WIDTH_UNIT_INPUT_ID, const.DIMENSION_DEFAULT_WIDTH_UNIT, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_BASE_LENGTH_UNIT_INPUT_ID, const.DIMENSION_DEFAULT_WIDTH_UNIT, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_XY_CLEARANCE_INPUT_ID, const.BIN_XY_CLEARANCE, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_BASES_X_INPUT_ID, 2, adsk.core.IntegerSpinnerCommandInput.classType())
    commandUIState.initValue(LID_BASES_Y_INPUT_ID, 3, adsk.core.IntegerSpinnerCommandInput.classType())
    commandUIState.initValue(LID_THICKNESS_INPUT_ID, 0.6, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_MAGNET_DIAMETER_INPUT_ID, const.DIMENSION_MAGNET_CUTOUT_DIAMETER, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_MAGNET_DEPTH_INPUT_ID, const.DIMENSION_MAGNET_CUTOUT_DEPTH, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_HAS_HANDLE_INPUT_ID, False, adsk.core.BoolValueCommandInput.classType())
    commandUIState.initValue(LID_HANDLE_HEIGHT_INPUT_ID, 0.6, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_HANDLE_EDGE_GAP_INPUT_ID, 0.3, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_HANDLE_CORNER_FILLET_INPUT_ID, 0.2, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_HANDLE_SIDE_FILLET_INPUT_ID, 0.2, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_LABEL_PRESET_DROPDOWN_ID, LABEL_PRESET_DEFAULT, adsk.core.DropDownCommandInput.classType())
    commandUIState.initValue(LID_LABEL_WIDTH_INPUT_ID, 1.2, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_LABEL_LENGTH_INPUT_ID, 4.0, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_LABEL_MARGIN_INPUT_ID, 0.3, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_LABEL_CORNER_FILLET_INPUT_ID, 0.15, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_USER_CHANGES_GROUP, True, adsk.core.GroupCommandInput.classType())

    recordedDefaults = configUtils.readJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH)
    if recordedDefaults is not None and 'static_ui' in recordedDefaults:
        staticUiState = recordedDefaults['static_ui']
        if staticUiState is not None:
            futil.log(f'{CMD_NAME} Found previously saved default values, restoring {staticUiState}')
            try:
                commandUIState.initValues(staticUiState)
                futil.log(f'{CMD_NAME} Successfully restored default values')
            except Exception as err:
                futil.log(f'{CMD_NAME} Failed to restore default values, err: {err}')


def start():
    try:
        futil.log(f'{CMD_NAME} Command Start Event')
        addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)

        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
            futil.add_handler(cmd_def.commandCreated, command_created)

            workspace = ui.workspaces.itemById(WORKSPACE_ID)
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
            control.isPromoted = addinConfig['UI'].getboolean('is_promoted')

        initDefaultUiState()
        ui.statusMessage = ""
    except Exception as err:
        futil.log(f'{CMD_NAME} Error occurred at the start, {err}, {getErrorMessage()}')
        ui.statusMessage = f"{CMD_NAME} failed to initialize"
        showErrorInMessageBox(f"{CMD_NAME} Critical error occurred at the start")


def stop():
    futil.log(f'{CMD_NAME} Command Stop Event')
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control: adsk.core.CommandControl = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    addinConfig = configUtils.readConfig(CONFIG_FOLDER_PATH)
    addinConfig['UI']['is_promoted'] = 'yes' if command_control.isPromoted else 'no'
    configUtils.writeConfig(addinConfig, CONFIG_FOLDER_PATH)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    global commandUIState

    args.command.setDialogInitialSize(400, 400)

    inputs = args.command.commandInputs
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits

    basicSizesGroup = inputs.addGroupCommandInput(LID_BASIC_SIZES_GROUP, 'Basic sizes')
    basicSizesGroup.isExpanded = commandUIState.getState(LID_BASIC_SIZES_GROUP)
    commandUIState.registerCommandInput(basicSizesGroup)

    baseWidthUnitInput = basicSizesGroup.children.addValueInput(
        LID_BASE_WIDTH_UNIT_INPUT_ID, 'Base width unit (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_BASE_WIDTH_UNIT_INPUT_ID))
    )
    baseWidthUnitInput.minimumValue = 1
    baseWidthUnitInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(baseWidthUnitInput)

    baseLengthUnitInput = basicSizesGroup.children.addValueInput(
        LID_BASE_LENGTH_UNIT_INPUT_ID, 'Base length unit (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_BASE_LENGTH_UNIT_INPUT_ID))
    )
    baseLengthUnitInput.minimumValue = 1
    baseLengthUnitInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(baseLengthUnitInput)

    xyClearanceInput = basicSizesGroup.children.addValueInput(
        LID_XY_CLEARANCE_INPUT_ID, 'XY clearance (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_XY_CLEARANCE_INPUT_ID))
    )
    xyClearanceInput.minimumValue = 0.01
    xyClearanceInput.isMinimumInclusive = True
    xyClearanceInput.maximumValue = 0.05
    xyClearanceInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(xyClearanceInput)

    dimensionsGroup = inputs.addGroupCommandInput(LID_DIMENSIONS_GROUP, 'Lid dimensions')
    dimensionsGroup.isExpanded = commandUIState.getState(LID_DIMENSIONS_GROUP)
    commandUIState.registerCommandInput(dimensionsGroup)

    basesXInput = dimensionsGroup.children.addIntegerSpinnerCommandInput(
        LID_BASES_X_INPUT_ID, 'Bases X (u)', 1, 100, 1,
        commandUIState.getState(LID_BASES_X_INPUT_ID)
    )
    commandUIState.registerCommandInput(basesXInput)

    basesYInput = dimensionsGroup.children.addIntegerSpinnerCommandInput(
        LID_BASES_Y_INPUT_ID, 'Bases Y (u)', 1, 100, 1,
        commandUIState.getState(LID_BASES_Y_INPUT_ID)
    )
    commandUIState.registerCommandInput(basesYInput)

    lidThicknessInput = dimensionsGroup.children.addValueInput(
        LID_THICKNESS_INPUT_ID, 'Lid thickness (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_THICKNESS_INPUT_ID))
    )
    lidThicknessInput.minimumValue = const.BIN_BASE_HEIGHT + const.BIN_COMPARTMENT_BOTTOM_THICKNESS
    lidThicknessInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(lidThicknessInput)

    magnetGroup = inputs.addGroupCommandInput(LID_MAGNET_GROUP, 'Magnet pockets')
    magnetGroup.isExpanded = commandUIState.getState(LID_MAGNET_GROUP)
    commandUIState.registerCommandInput(magnetGroup)

    magnetDiameterInput = magnetGroup.children.addValueInput(
        LID_MAGNET_DIAMETER_INPUT_ID, 'Magnet pocket diameter (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_MAGNET_DIAMETER_INPUT_ID))
    )
    magnetDiameterInput.minimumValue = 0.1
    magnetDiameterInput.isMinimumInclusive = True
    magnetDiameterInput.maximumValue = 1
    magnetDiameterInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(magnetDiameterInput)

    magnetDepthInput = magnetGroup.children.addValueInput(
        LID_MAGNET_DEPTH_INPUT_ID, 'Magnet pocket depth (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_MAGNET_DEPTH_INPUT_ID))
    )
    magnetDepthInput.minimumValue = 0.1
    magnetDepthInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(magnetDepthInput)

    handleGroup = inputs.addGroupCommandInput(LID_HANDLE_GROUP, 'Lift handle / label')
    handleGroup.isExpanded = commandUIState.getState(LID_HANDLE_GROUP)
    commandUIState.registerCommandInput(handleGroup)

    hasHandleInput = handleGroup.children.addBoolValueInput(
        LID_HAS_HANDLE_INPUT_ID, 'Add lift handle', True, '',
        commandUIState.getState(LID_HAS_HANDLE_INPUT_ID)
    )
    commandUIState.registerCommandInput(hasHandleInput)

    handleHeightInput = handleGroup.children.addValueInput(
        LID_HANDLE_HEIGHT_INPUT_ID, 'Handle height (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_HANDLE_HEIGHT_INPUT_ID))
    )
    handleHeightInput.minimumValue = 0.2
    handleHeightInput.isMinimumInclusive = True
    handleHeightInput.maximumValue = 3
    handleHeightInput.isMaximumInclusive = True
    commandUIState.registerCommandInput(handleHeightInput)

    handleEdgeGapInput = handleGroup.children.addValueInput(
        LID_HANDLE_EDGE_GAP_INPUT_ID, 'Gap to lid edge (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_HANDLE_EDGE_GAP_INPUT_ID))
    )
    handleEdgeGapInput.minimumValue = 0
    handleEdgeGapInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(handleEdgeGapInput)

    handleCornerFilletInput = handleGroup.children.addValueInput(
        LID_HANDLE_CORNER_FILLET_INPUT_ID, 'Ramp corner fillet (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_HANDLE_CORNER_FILLET_INPUT_ID))
    )
    handleCornerFilletInput.minimumValue = 0
    handleCornerFilletInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(handleCornerFilletInput)

    handleSideFilletInput = handleGroup.children.addValueInput(
        LID_HANDLE_SIDE_FILLET_INPUT_ID, 'Side edge fillet (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_HANDLE_SIDE_FILLET_INPUT_ID))
    )
    handleSideFilletInput.minimumValue = 0
    handleSideFilletInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(handleSideFilletInput)

    labelPresetDropdown = handleGroup.children.addDropDownCommandInput(
        LID_LABEL_PRESET_DROPDOWN_ID, 'Label size', adsk.core.DropDownStyles.TextListDropDownStyle
    )
    labelPresetDefault = commandUIState.getState(LID_LABEL_PRESET_DROPDOWN_ID)
    if labelPresetDefault not in LABEL_PRESETS:
        # saved defaults may reference a preset name from an older version
        labelPresetDefault = LABEL_PRESET_DEFAULT
        commandUIState.initValue(LID_LABEL_PRESET_DROPDOWN_ID, labelPresetDefault, adsk.core.DropDownCommandInput.classType())
    for presetName in LABEL_PRESETS:
        labelPresetDropdown.listItems.add(presetName, presetName == labelPresetDefault)
    commandUIState.registerCommandInput(labelPresetDropdown)

    labelWidthInput = handleGroup.children.addValueInput(
        LID_LABEL_WIDTH_INPUT_ID, 'Custom label width (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_LABEL_WIDTH_INPUT_ID))
    )
    labelWidthInput.minimumValue = 0.3
    labelWidthInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(labelWidthInput)

    labelLengthInput = handleGroup.children.addValueInput(
        LID_LABEL_LENGTH_INPUT_ID, 'Custom label length (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_LABEL_LENGTH_INPUT_ID))
    )
    labelLengthInput.minimumValue = 1
    labelLengthInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(labelLengthInput)

    labelMarginInput = handleGroup.children.addValueInput(
        LID_LABEL_MARGIN_INPUT_ID, 'Recess edge to handle edge (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_LABEL_MARGIN_INPUT_ID))
    )
    labelMarginInput.minimumValue = 0.05
    labelMarginInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(labelMarginInput)

    labelCornerFilletInput = handleGroup.children.addValueInput(
        LID_LABEL_CORNER_FILLET_INPUT_ID, 'Label corner fillet (mm)', defaultLengthUnits,
        adsk.core.ValueInput.createByReal(commandUIState.getState(LID_LABEL_CORNER_FILLET_INPUT_ID))
    )
    labelCornerFilletInput.minimumValue = 0
    labelCornerFilletInput.isMinimumInclusive = True
    commandUIState.registerCommandInput(labelCornerFilletInput)

    handleWarningInput = handleGroup.children.addTextBoxCommandInput(LID_HANDLE_WARNING_INPUT_ID, '', '', 2, True)
    handleWarningInput.isFullWidth = True
    handleWarningInput.isVisible = False
    commandUIState.registerCommandInput(handleWarningInput)

    userChangesGroup = inputs.addGroupCommandInput(LID_USER_CHANGES_GROUP, 'Changes')
    userChangesGroup.isExpanded = commandUIState.getState(LID_USER_CHANGES_GROUP)
    commandUIState.registerCommandInput(userChangesGroup)
    saveAsDefaultsButtonInput = userChangesGroup.children.addBoolValueInput(LID_INPUT_CHANGES_SAVE_DEFAULTS, 'Save as new defaults', False, '', False)
    saveAsDefaultsButtonInput.text = 'Save'
    resetToDefaultsButtonInput = userChangesGroup.children.addBoolValueInput(LID_INPUT_CHANGES_RESET_TO_DEFAULTS, 'Reset to defaults', False, '', False)
    resetToDefaultsButtonInput.text = 'Reset'
    factoryResetButtonInput = userChangesGroup.children.addBoolValueInput(LID_INPUT_CHANGES_RESET_TO_FACTORY, 'Wipe saved settings', False, '', False)
    factoryResetButtonInput.text = 'Factory reset'

    previewGroup = inputs.addGroupCommandInput(LID_PREVIEW_GROUP, 'Preview')
    previewGroup.isExpanded = commandUIState.getState(LID_PREVIEW_GROUP)
    commandUIState.registerCommandInput(previewGroup)
    showPreviewInput = previewGroup.children.addBoolValueInput(LID_SHOW_PREVIEW_INPUT, 'Show auto update preview (slow)', True, '', False)
    commandUIState.registerCommandInput(showPreviewInput)
    showPreviewManualInput = previewGroup.children.addBoolValueInput(LID_SHOW_PREVIEW_MANUAL_INPUT, 'Update preview once', False, '', False)
    showPreviewManualInput.isFullWidth = True
    commandUIState.registerCommandInput(showPreviewManualInput)

    autoFitHandle()
    onChangeValidate()

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    generateLid(args)


def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs
    if is_all_input_valid(inputs):
        showPreview: adsk.core.BoolValueCommandInput = inputs.itemById(LID_SHOW_PREVIEW_INPUT)
        showPreviewManual: adsk.core.BoolValueCommandInput = inputs.itemById(LID_SHOW_PREVIEW_MANUAL_INPUT)
        if showPreview.value or showPreviewManual.value:
            args.isValidResult = generateLid(args)
            showPreviewManual.value = False
    else:
        args.executeFailed = True
        args.executeFailedMessage = 'Some inputs are invalid, unable to generate preview'


def onChangeValidate():
    global commandUIState
    hasHandle: bool = commandUIState.getState(LID_HAS_HANDLE_INPUT_ID)
    presetWidth, presetLength = LABEL_PRESETS.get(commandUIState.getState(LID_LABEL_PRESET_DROPDOWN_ID), (None, None))
    commandUIState.getInput(LID_HANDLE_HEIGHT_INPUT_ID).isEnabled = hasHandle
    commandUIState.getInput(LID_HANDLE_EDGE_GAP_INPUT_ID).isEnabled = hasHandle
    commandUIState.getInput(LID_HANDLE_CORNER_FILLET_INPUT_ID).isEnabled = hasHandle
    commandUIState.getInput(LID_HANDLE_SIDE_FILLET_INPUT_ID).isEnabled = hasHandle
    commandUIState.getInput(LID_LABEL_PRESET_DROPDOWN_ID).isEnabled = hasHandle
    commandUIState.getInput(LID_LABEL_WIDTH_INPUT_ID).isEnabled = hasHandle and presetWidth is None
    commandUIState.getInput(LID_LABEL_LENGTH_INPUT_ID).isEnabled = hasHandle and presetLength is None
    commandUIState.getInput(LID_LABEL_MARGIN_INPUT_ID).isEnabled = hasHandle
    commandUIState.getInput(LID_LABEL_CORNER_FILLET_INPUT_ID).isEnabled = hasHandle
    showPreview: bool = commandUIState.getInput(LID_SHOW_PREVIEW_INPUT).value
    commandUIState.getInput(LID_SHOW_PREVIEW_MANUAL_INPUT).isVisible = not showPreview

    # tell the user when the selected label cannot fit this lid at all,
    # instead of silently disabling OK and the preview
    handleWarning: adsk.core.TextBoxCommandInput = commandUIState.getInput(LID_HANDLE_WARNING_INPUT_ID)
    showWarning = False
    if hasHandle:
        labelWidth = presetWidth if presetWidth is not None else commandUIState.getState(LID_LABEL_WIDTH_INPUT_ID)
        labelLength = presetLength if presetLength is not None else commandUIState.getState(LID_LABEL_LENGTH_INPUT_ID)
        xyClearance = commandUIState.getState(LID_XY_CLEARANCE_INPUT_ID)
        edgeGap = commandUIState.getState(LID_HANDLE_EDGE_GAP_INPUT_ID)
        lidWidth = commandUIState.getState(LID_BASE_WIDTH_UNIT_INPUT_ID) * commandUIState.getState(LID_BASES_X_INPUT_ID) - xyClearance * 2
        lidLength = commandUIState.getState(LID_BASE_LENGTH_UNIT_INPUT_ID) * commandUIState.getState(LID_BASES_Y_INPUT_ID) - xyClearance * 2
        showWarning = (
            not handleFitsSpan(lidWidth, lidLength, labelWidth, labelLength, edgeGap)
            and not handleFitsSpan(lidLength, lidWidth, labelWidth, labelLength, edgeGap)
        )
        if showWarning:
            handleWarning.formattedText = '<b>Label does not fit this lid in either direction.</b> Pick a smaller label or increase the lid size.'
    handleWarning.isVisible = showWarning


def autoFitHandle():
    """Re-fit the handle margin and end transition when the lid dimensions or
    label change, so a previously valid label preset doesn't silently
    invalidate the dialog. Only ever shrinks values; never grows them back."""
    global commandUIState
    if not commandUIState.getState(LID_HAS_HANDLE_INPUT_ID):
        return
    presetWidth, presetLength = LABEL_PRESETS.get(commandUIState.getState(LID_LABEL_PRESET_DROPDOWN_ID), (None, None))
    labelWidth = presetWidth if presetWidth is not None else commandUIState.getState(LID_LABEL_WIDTH_INPUT_ID)
    labelLength = presetLength if presetLength is not None else commandUIState.getState(LID_LABEL_LENGTH_INPUT_ID)
    xyClearance = commandUIState.getState(LID_XY_CLEARANCE_INPUT_ID)
    handleHeight = commandUIState.getState(LID_HANDLE_HEIGHT_INPUT_ID)
    edgeGap = commandUIState.getState(LID_HANDLE_EDGE_GAP_INPUT_ID)
    lidWidth = commandUIState.getState(LID_BASE_WIDTH_UNIT_INPUT_ID) * commandUIState.getState(LID_BASES_X_INPUT_ID) - xyClearance * 2
    lidLength = commandUIState.getState(LID_BASE_LENGTH_UNIT_INPUT_ID) * commandUIState.getState(LID_BASES_Y_INPUT_ID) - xyClearance * 2
    if isHandleAlongY(lidWidth, lidLength, labelWidth, labelLength, edgeGap):
        spanLength, acrossLength = lidLength, lidWidth
    else:
        spanLength, acrossLength = lidWidth, lidLength

    recessLength = labelLength + const.LID_LABEL_RECESS_CLEARANCE
    recessWidth = labelWidth + const.LID_LABEL_RECESS_CLEARANCE
    # room per side for margin + side fillet (across) / margin + corner
    # setback (along, bounded by the corner radius)
    halfBudgetAcross = (acrossLength - const.BIN_CORNER_FILLET_RADIUS * 2 - recessWidth) / 2
    halfBudgetAlong = (spanLength - edgeGap * 2 - recessLength - 0.2) / 2

    # clamp the fillet radii first: against the handle height (so the features
    # can compute) and against the lid geometry (leaving room for the minimum
    # margin)
    sideFillet = commandUIState.getState(LID_HANDLE_SIDE_FILLET_INPUT_ID)
    maxSideFillet = math.floor(min(handleHeight - 0.05, halfBudgetAcross - 0.05) * 100) / 100
    if maxSideFillet >= 0 and sideFillet > maxSideFillet:
        futil.log(f'{CMD_NAME} Auto-fitting side fillet {sideFillet} -> {maxSideFillet}')
        commandUIState.updateValue(LID_HANDLE_SIDE_FILLET_INPUT_ID, maxSideFillet)
        sideFillet = maxSideFillet
    cornerFillet = commandUIState.getState(LID_HANDLE_CORNER_FILLET_INPUT_ID)
    maxCornerFillet = math.floor(min(handleHeight, halfBudgetAlong - 0.05) * 100) / 100
    if maxCornerFillet >= 0 and cornerFillet > maxCornerFillet:
        futil.log(f'{CMD_NAME} Auto-fitting corner fillet {cornerFillet} -> {maxCornerFillet}')
        commandUIState.updateValue(LID_HANDLE_CORNER_FILLET_INPUT_ID, maxCornerFillet)
        cornerFillet = maxCornerFillet

    # then the margin gets whatever room remains
    margin = commandUIState.getState(LID_LABEL_MARGIN_INPUT_ID)
    maxMargin = math.floor(min(halfBudgetAcross - sideFillet, halfBudgetAlong - cornerFillet) * 100) / 100
    if maxMargin >= 0.05 and margin > maxMargin:
        futil.log(f'{CMD_NAME} Auto-fitting label margin {margin} -> {maxMargin}')
        commandUIState.updateValue(LID_LABEL_MARGIN_INPUT_ID, maxMargin)

    # recess corner fillet is bounded by the recess outline
    labelCornerFillet = commandUIState.getState(LID_LABEL_CORNER_FILLET_INPUT_ID)
    maxLabelCornerFillet = math.floor((min(recessWidth, recessLength) / 2 - 0.05) * 100) / 100
    if maxLabelCornerFillet >= 0 and labelCornerFillet > maxLabelCornerFillet:
        futil.log(f'{CMD_NAME} Auto-fitting label corner fillet {labelCornerFillet} -> {maxLabelCornerFillet}')
        commandUIState.updateValue(LID_LABEL_CORNER_FILLET_INPUT_ID, maxLabelCornerFillet)


def refreshUi():
    global commandUIState
    commandUIState.forceUIRefresh()
    onChangeValidate()


def saveUIInputsAsDefaults():
    futil.log(f'{CMD_NAME} Saving UI state to file')
    result = configUtils.dumpJsonConfig(UI_INPUT_DEFAULTS_CONFIG_PATH, {
        'static_ui': commandUIState.toDict(ignoreKeys=[LID_SHOW_PREVIEW_INPUT, LID_SHOW_PREVIEW_MANUAL_INPUT, LID_HANDLE_WARNING_INPUT_ID]),
    })
    if result:
        futil.log(f'{CMD_NAME} Saved successfully')
    else:
        futil.log(f'{CMD_NAME} UI state failed to save')


def getEffectiveLabelSize(inputs: adsk.core.CommandInputs) -> tuple[float, float]:
    labelPreset: adsk.core.DropDownCommandInput = inputs.itemById(LID_LABEL_PRESET_DROPDOWN_ID)
    labelWidth: adsk.core.ValueCommandInput = inputs.itemById(LID_LABEL_WIDTH_INPUT_ID)
    labelLength: adsk.core.ValueCommandInput = inputs.itemById(LID_LABEL_LENGTH_INPUT_ID)
    presetName = labelPreset.selectedItem.name if labelPreset.selectedItem else LABEL_PRESET_DEFAULT
    presetWidth, presetLength = LABEL_PRESETS.get(presetName, (None, None))
    return (
        presetWidth if presetWidth is not None else labelWidth.value,
        presetLength if presetLength is not None else labelLength.value,
    )


def handleFitsSpan(spanLength: float, acrossLength: float, labelWidth: float, labelLength: float, edgeGap: float) -> bool:
    """Can the handle + label physically fit with this span axis, assuming the
    margin and both fillet radii are shrunk to their minimums? The bar stops
    edgeGap short of the lid edges."""
    minMargin = 0.05
    minRampRun = 0.1
    recessLength = labelLength + const.LID_LABEL_RECESS_CLEARANCE
    recessWidth = labelWidth + const.LID_LABEL_RECESS_CLEARANCE
    fitsAcross = recessWidth + minMargin * 2 <= acrossLength - const.BIN_CORNER_FILLET_RADIUS * 2
    fitsAlong = recessLength + minMargin * 2 + minRampRun * 2 <= spanLength - edgeGap * 2
    return fitsAcross and fitsAlong


def isHandleAlongY(lidWidth: float, lidLength: float, labelWidth: float, labelLength: float, edgeGap: float) -> bool:
    """Handle spans X by default; flip to Y when the label only fits the long way."""
    return (
        not handleFitsSpan(lidWidth, lidLength, labelWidth, labelLength, edgeGap)
        and handleFitsSpan(lidLength, lidWidth, labelWidth, labelLength, edgeGap)
    )


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')
    global commandUIState
    if changed_input.id == LID_INPUT_CHANGES_SAVE_DEFAULTS:
        saveUIInputsAsDefaults()
    elif changed_input.id == LID_INPUT_CHANGES_RESET_TO_DEFAULTS:
        initDefaultUiState()
        refreshUi()
    elif changed_input.id == LID_INPUT_CHANGES_RESET_TO_FACTORY:
        configUtils.deleteConfigFile(UI_INPUT_DEFAULTS_CONFIG_PATH)
        initDefaultUiState()
        refreshUi()
    else:
        commandUIState.onInputUpdate(changed_input)
    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded:
        for input in changed_input.children:
            commandUIState.registerCommandInput(input)
    if changed_input.id in HANDLE_AUTO_FIT_TRIGGER_IDS:
        autoFitHandle()
    onChangeValidate()


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    futil.log(f'{CMD_NAME} Validate Input Event')
    inputs = args.inputs
    args.areInputsValid = is_all_input_valid(inputs)


def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event "{args.terminationReason}"')
    global local_handlers
    local_handlers = []


def is_all_input_valid(inputs: adsk.core.CommandInputs) -> bool:
    baseWidthUnit: adsk.core.ValueCommandInput = inputs.itemById(LID_BASE_WIDTH_UNIT_INPUT_ID)
    baseLengthUnit: adsk.core.ValueCommandInput = inputs.itemById(LID_BASE_LENGTH_UNIT_INPUT_ID)
    xyClearance: adsk.core.ValueCommandInput = inputs.itemById(LID_XY_CLEARANCE_INPUT_ID)
    basesX: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(LID_BASES_X_INPUT_ID)
    basesY: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(LID_BASES_Y_INPUT_ID)
    lidThickness: adsk.core.ValueCommandInput = inputs.itemById(LID_THICKNESS_INPUT_ID)
    magnetDiameter: adsk.core.ValueCommandInput = inputs.itemById(LID_MAGNET_DIAMETER_INPUT_ID)
    magnetDepth: adsk.core.ValueCommandInput = inputs.itemById(LID_MAGNET_DEPTH_INPUT_ID)

    result = True
    result = result and baseWidthUnit.value > 1
    result = result and baseLengthUnit.value > 1
    result = result and xyClearance.value >= 0.01 and xyClearance.value <= 0.05
    result = result and basesX.value > 0
    result = result and basesY.value > 0
    result = result and lidThickness.value >= const.BIN_BASE_HEIGHT + const.BIN_COMPARTMENT_BOTTOM_THICKNESS
    result = result and magnetDiameter.value > 0
    result = result and magnetDepth.value > 0

    hasHandle: adsk.core.BoolValueCommandInput = inputs.itemById(LID_HAS_HANDLE_INPUT_ID)
    if hasHandle.value:
        handleHeight: adsk.core.ValueCommandInput = inputs.itemById(LID_HANDLE_HEIGHT_INPUT_ID)
        handleEdgeGap: adsk.core.ValueCommandInput = inputs.itemById(LID_HANDLE_EDGE_GAP_INPUT_ID)
        cornerFillet: adsk.core.ValueCommandInput = inputs.itemById(LID_HANDLE_CORNER_FILLET_INPUT_ID)
        sideFillet: adsk.core.ValueCommandInput = inputs.itemById(LID_HANDLE_SIDE_FILLET_INPUT_ID)
        labelMargin: adsk.core.ValueCommandInput = inputs.itemById(LID_LABEL_MARGIN_INPUT_ID)
        labelWidth, labelLength = getEffectiveLabelSize(inputs)
        lidWidth = baseWidthUnit.value * basesX.value - xyClearance.value * 2
        lidLength = baseLengthUnit.value * basesY.value - xyClearance.value * 2
        if isHandleAlongY(lidWidth, lidLength, labelWidth, labelLength, handleEdgeGap.value):
            spanLength, acrossLength = lidLength, lidWidth
        else:
            spanLength, acrossLength = lidWidth, lidLength
        recessLength = labelLength + const.LID_LABEL_RECESS_CLEARANCE
        recessWidth = labelWidth + const.LID_LABEL_RECESS_CLEARANCE
        handleWidth = recessWidth + (labelMargin.value + sideFillet.value) * 2
        result = result and handleHeight.value >= 0.2
        result = result and handleEdgeGap.value >= 0
        result = result and labelMargin.value >= 0.05
        result = result and labelWidth > 0 and labelLength > 0
        # fillet bounds: side fillet must not consume the bar's vertical face,
        # corner fillet must not exceed the bar height, recess corner fillet
        # must not degenerate the recess outline
        labelCornerFillet: adsk.core.ValueCommandInput = inputs.itemById(LID_LABEL_CORNER_FILLET_INPUT_ID)
        result = result and sideFillet.value >= 0 and sideFillet.value <= handleHeight.value - 0.05
        result = result and cornerFillet.value >= 0 and cornerFillet.value <= handleHeight.value
        result = result and labelCornerFillet.value >= 0 and labelCornerFillet.value <= min(recessWidth, recessLength) / 2 - 0.05
        # handle (incl. side fillet reservation) must fit between the rounded
        # lid corners
        result = result and handleWidth <= acrossLength - const.BIN_CORNER_FILLET_RADIUS * 2
        # flat top (recess + border + corner blend setback) must leave at
        # least a token ramp run at each end of the bar, inset by the edge gap
        result = result and recessLength + (labelMargin.value + cornerFillet.value) * 2 + 0.2 <= spanLength - handleEdgeGap.value * 2
    return result


def generateLid(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    baseWidthUnit: adsk.core.ValueCommandInput = inputs.itemById(LID_BASE_WIDTH_UNIT_INPUT_ID)
    baseLengthUnit: adsk.core.ValueCommandInput = inputs.itemById(LID_BASE_LENGTH_UNIT_INPUT_ID)
    xyClearance: adsk.core.ValueCommandInput = inputs.itemById(LID_XY_CLEARANCE_INPUT_ID)
    basesX: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(LID_BASES_X_INPUT_ID)
    basesY: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(LID_BASES_Y_INPUT_ID)
    lidThickness: adsk.core.ValueCommandInput = inputs.itemById(LID_THICKNESS_INPUT_ID)
    magnetDiameter: adsk.core.ValueCommandInput = inputs.itemById(LID_MAGNET_DIAMETER_INPUT_ID)
    magnetDepth: adsk.core.ValueCommandInput = inputs.itemById(LID_MAGNET_DEPTH_INPUT_ID)

    try:
        des = adsk.fusion.Design.cast(app.activeProduct)
        if des.designType == adsk.fusion.DesignTypes.DirectDesignType:
            raise UnsupportedDesignTypeException('Timeline must be enabled for the generator to work')
        root = adsk.fusion.Component.cast(des.rootComponent)

        lidName = 'Gridfinity lid {}x{}'.format(int(basesX.value), int(basesY.value))
        originalTimelineCount = des.timeline.count

        if des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
            newCmpOcc = adsk.fusion.Occurrences.cast(root.occurrences).addNewComponent(adsk.core.Matrix3D.create())
            newCmpOcc.component.name = lidName
            newCmpOcc.activate()
            gridfinityLidComponent: adsk.fusion.Component = newCmpOcc.component
        else:
            gridfinityLidComponent: adsk.fusion.Component = des.rootComponent

        lidInput = LidGeneratorInput()
        lidInput.basesX = basesX.value
        lidInput.basesY = basesY.value
        lidInput.baseWidth = baseWidthUnit.value
        lidInput.baseLength = baseLengthUnit.value
        lidInput.xyClearance = xyClearance.value
        lidInput.lidThickness = lidThickness.value
        lidInput.magnetDiameter = magnetDiameter.value
        lidInput.magnetDepth = magnetDepth.value
        lidInput.hasHandle = inputs.itemById(LID_HAS_HANDLE_INPUT_ID).value
        if lidInput.hasHandle:
            labelWidth, labelLength = getEffectiveLabelSize(inputs)
            lidWidth = baseWidthUnit.value * basesX.value - xyClearance.value * 2
            lidLength = baseLengthUnit.value * basesY.value - xyClearance.value * 2
            handleEdgeGapValue = inputs.itemById(LID_HANDLE_EDGE_GAP_INPUT_ID).value
            lidInput.handleAlongY = isHandleAlongY(lidWidth, lidLength, labelWidth, labelLength, handleEdgeGapValue)
            lidInput.handleHeight = inputs.itemById(LID_HANDLE_HEIGHT_INPUT_ID).value
            lidInput.handleEdgeGap = handleEdgeGapValue
            lidInput.handleCornerFilletRadius = inputs.itemById(LID_HANDLE_CORNER_FILLET_INPUT_ID).value
            lidInput.handleSideFilletRadius = inputs.itemById(LID_HANDLE_SIDE_FILLET_INPUT_ID).value
            lidInput.labelCornerFilletRadius = inputs.itemById(LID_LABEL_CORNER_FILLET_INPUT_ID).value
            lidInput.labelWidth = labelWidth
            lidInput.labelLength = labelLength
            lidInput.labelMargin = inputs.itemById(LID_LABEL_MARGIN_INPUT_ID).value

        lidBody = createLidBody(lidInput, gridfinityLidComponent)
        lidBody.name = lidName

        lidGroup = des.timeline.timelineGroups.add(originalTimelineCount, des.timeline.count - 1)
        lidGroup.name = lidName

    except UnsupportedDesignTypeException as err:
        args.executeFailed = True
        args.executeFailedMessage = 'Design type is unsupported. Please enable timeline feature to proceed.'
        return False
    except Exception as err:
        args.executeFailed = True
        args.executeFailedMessage = getErrorMessage()
        futil.log(f'{CMD_NAME} Error occurred, {err}, {getErrorMessage()}')
        return False
    return True
