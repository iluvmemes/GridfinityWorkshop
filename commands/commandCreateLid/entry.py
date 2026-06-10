import adsk.core, adsk.fusion, traceback
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

local_handlers = []

# Group IDs
LID_BASIC_SIZES_GROUP = 'lid_basic_sizes_group'
LID_DIMENSIONS_GROUP = 'lid_dimensions_group'
LID_MAGNET_GROUP = 'lid_magnet_group'

# Input IDs
LID_BASE_WIDTH_UNIT_INPUT_ID = 'lid_base_width_unit'
LID_BASE_LENGTH_UNIT_INPUT_ID = 'lid_base_length_unit'
LID_XY_CLEARANCE_INPUT_ID = 'lid_xy_clearance'
LID_BASES_X_INPUT_ID = 'lid_bases_x'
LID_BASES_Y_INPUT_ID = 'lid_bases_y'
LID_THICKNESS_INPUT_ID = 'lid_thickness'
LID_MAGNET_DIAMETER_INPUT_ID = 'lid_magnet_diameter'
LID_MAGNET_DEPTH_INPUT_ID = 'lid_magnet_depth'


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

    commandUIState.initValue(LID_BASE_WIDTH_UNIT_INPUT_ID, const.DIMENSION_DEFAULT_WIDTH_UNIT, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_BASE_LENGTH_UNIT_INPUT_ID, const.DIMENSION_DEFAULT_WIDTH_UNIT, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_XY_CLEARANCE_INPUT_ID, const.BIN_XY_CLEARANCE, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_BASES_X_INPUT_ID, 2, adsk.core.IntegerSpinnerCommandInput.classType())
    commandUIState.initValue(LID_BASES_Y_INPUT_ID, 3, adsk.core.IntegerSpinnerCommandInput.classType())
    commandUIState.initValue(LID_THICKNESS_INPUT_ID, 0.6, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_MAGNET_DIAMETER_INPUT_ID, const.DIMENSION_MAGNET_CUTOUT_DIAMETER, adsk.core.ValueCommandInput.classType())
    commandUIState.initValue(LID_MAGNET_DEPTH_INPUT_ID, const.DIMENSION_MAGNET_CUTOUT_DEPTH, adsk.core.ValueCommandInput.classType())


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


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')
    global commandUIState
    commandUIState.onInputUpdate(changed_input)
    if isinstance(changed_input, adsk.core.GroupCommandInput) and changed_input.isExpanded:
        for input in changed_input.children:
            commandUIState.registerCommandInput(input)


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
