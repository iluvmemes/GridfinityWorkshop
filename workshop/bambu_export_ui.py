"""One export command shared by the toolbar and component context menu."""
from pathlib import Path
import re
import traceback
import adsk.core
import adsk.fusion
from . import bambu_export

COMMAND_ID = 'GridfinityWorkshop_ExportForBambu'
PANEL_IDS = ('SolidCreatePanel', 'SolidScriptsAddinsPanel')
_handlers = []
_menu_handler = None
_last_result = None
_last_error = None


def supported(entity):
    return bool(adsk.fusion.Occurrence.cast(entity) or adsk.fusion.Component.cast(entity)
                or adsk.fusion.BRepBody.cast(entity))


class Execute(adsk.core.CommandEventHandler):
    def notify(self, args):
        global _last_result, _last_error
        try:
            _last_error = None
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            inputs = args.firingEvent.sender.commandInputs
            selection = inputs.itemById('bambuScope')
            geometry = selection.selection(0).entity if selection.selectionCount else design.rootComponent
            dialog = app.userInterface.createFileDialog()
            dialog.title = 'Export for Bambu'
            dialog.filter = '3MF files (*.3mf)'
            dialog.initialFilename = re.sub(r'[<>:"/\\|?*]', '-', geometry.name) + '.3mf'
            if dialog.showSave() != adsk.core.DialogResults.DialogOK:
                return
            filename = str(Path(dialog.filename).with_suffix('.3mf'))
            result = bambu_export.export(design, geometry, filename)
            _last_result = result
            app.userInterface.messageBox(
                f"Exported {result['parts']} parts in one assembly.\n\n{filename}\n\n"
                'Body positions and Fusion colors are preserved. Assign your filaments in Bambu Studio.',
                'Export for Bambu')
        except Exception as error:
            _last_error = traceback.format_exc()
            args.executeFailed = True
            args.executeFailedMessage = str(error)
            adsk.core.Application.get().log(traceback.format_exc())
            adsk.core.Application.get().userInterface.messageBox(str(error), 'Export for Bambu')


class Destroy(adsk.core.CommandEventHandler):
    def __init__(self, handlers):
        super().__init__()
        self.handlers = handlers

    def notify(self, args):
        for handler in self.handlers + [self]:
            if handler in _handlers:
                _handlers.remove(handler)


class Created(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        app = adsk.core.Application.get()
        command = args.command
        command.isRepeatable = False
        command.isExecutedWhenPreEmpted = False
        selection = command.commandInputs.addSelectionInput(
            'bambuScope', 'Component or body', 'Select one component or body, or leave empty for the whole design')
        for kind in ('Occurrences', 'RootComponents', 'SolidBodies'):
            selection.addSelectionFilter(kind)
        selection.setSelectionLimits(0, 1)
        for item in app.userInterface.activeSelections:
            if supported(item.entity):
                selection.addSelection(item.entity)
                break
        command.commandInputs.addTextBoxCommandInput('bambuHint', '',
            'Exports the selected item and its child bodies as one assembly. Leave the selection empty '
            'to export the whole design. Colors and relative positions are kept. Choose a file after clicking OK.', 4, True)
        execute = Execute()
        destroy = Destroy([execute])
        command.execute.add(execute)
        command.destroy.add(destroy)
        _handlers.extend([execute, destroy])


class Menu(adsk.core.MarkingMenuEventHandler):
    def notify(self, args):
        if any(supported(entity) for entity in args.selectedEntities):
            controls = args.linearMarkingMenu.controls
            if not controls.itemById(COMMAND_ID):
                controls.addCommand(adsk.core.Application.get().userInterface.commandDefinitions.itemById(COMMAND_ID))


def start():
    global _menu_handler
    ui = adsk.core.Application.get().userInterface
    if ui.commandDefinitions.itemById(COMMAND_ID):
        return
    definition = ui.commandDefinitions.addButtonDefinition(COMMAND_ID, 'Export for Bambu…',
        'Export a component or design as one 3MF assembly, keeping its parts, colors, and positions.',
        str(Path(__file__).parent / 'resources'))
    created = Created()
    definition.commandCreated.add(created)
    _handlers.append(created)
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    for panel_id in PANEL_IDS:
        panel = workspace.toolbarPanels.itemById(panel_id)
        if panel:
            control = panel.controls.addCommand(definition)
            if panel_id == 'SolidCreatePanel':
                control.isPromotedByDefault = True
                control.isPromoted = True
    _menu_handler = Menu()
    ui.markingMenuDisplaying.add(_menu_handler)
    _handlers.append(_menu_handler)


def stop():
    global _menu_handler
    ui = adsk.core.Application.get().userInterface
    if _menu_handler:
        ui.markingMenuDisplaying.remove(_menu_handler)
        _menu_handler = None
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    for panel_id in PANEL_IDS:
        panel = workspace.toolbarPanels.itemById(panel_id) if workspace else None
        control = panel.controls.itemById(COMMAND_ID) if panel else None
        if control:
            control.deleteMe()
    definition = ui.commandDefinitions.itemById(COMMAND_ID)
    if definition:
        definition.deleteMe()
    _handlers.clear()
