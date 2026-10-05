"""Fusion palette with lightweight previews and explicit, undoable creation."""

import json
from pathlib import Path
import traceback

import adsk.core
from . import generation, catalog
from .request import validate

COMMAND_ID = 'GridfinityWorkshop_UIPreview_Show'
CREATE_ID = 'GridfinityWorkshop_CreateCachedBaseplate'
PALETTE_ID = 'GridfinityWorkshop_UIPreview_Palette'
PANEL_IDS = ('SolidCreatePanel', 'SolidScriptsAddinsPanel')
ICON_FOLDER = str(Path(__file__).parent / 'resources')
_handlers = []
_started = False
_messages = []
_last_preview = None
_last_response = None
_pending = None
_last_creation = None


def _ui():
    return adsk.core.Application.get().userInterface


class _HTMLHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
        global _last_preview, _last_response
        try:
            event = adsk.core.HTMLEventArgs.cast(args)
            data = json.loads(event.data) if event.data else {}
            if event.action in ('ready', 'previewChanged'):
                _last_preview = data
                event.returnData = json.dumps({'ok': True, 'previewOnly': True})
            elif event.action == 'create':
                request_creation(data)
                event.returnData = json.dumps({'ok': True, 'queued': True})
            elif event.action == 'response':
                # Qt wraps the JavaScript return string in a data field.
                result = data.get('data') if isinstance(data, dict) else None
                _last_response = json.loads(result) if isinstance(result, str) else data
            elif event.action == 'uiError':
                adsk.core.Application.get().log('Gridfinity UI preview: ' + event.data)
            else:
                event.returnData = json.dumps({'ok': False, 'error': 'Unsupported action'})
            _messages.append({'action': event.action, 'data': data})
            del _messages[:-20]
        except Exception as error:
            adsk.core.Application.get().log(traceback.format_exc())
            args.returnData = json.dumps({'ok': False, 'error': str(error)})
            status('error', str(error))


def status(phase, message, result=None):
    palette = _ui().palettes.itemById(PALETTE_ID)
    if palette:
        palette.sendInfoToHTML('creationStatus', json.dumps({'phase':phase,'message':message,'result':result}))


def request_creation(data):
    """Queue a native command so one Create action is one Fusion undo transaction."""
    global _pending
    if _pending is not None:
        raise ValueError('A baseplate is already being created.')
    settings = validate(data)
    app = adsk.core.Application.get()
    if not app.activeDocument:
        raise ValueError('Open a Fusion design first.')
    if _ui().activeCommand != 'SelectCommand':
        raise ValueError('Finish the active Fusion command before creating a baseplate.')
    _pending = {'settings':settings,'document':app.activeDocument}
    status('creating','Creating baseplate…')
    if not _ui().commandDefinitions.itemById(CREATE_ID).execute():
        _pending = None
        raise RuntimeError('Fusion could not start the create command.')


class _GenerateHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        global _pending, _last_creation
        job = _pending
        try:
            if not job:
                raise ValueError('Choose settings in the Gridfinity palette first.')
            app = adsk.core.Application.get()
            if app.activeDocument != job['document']:
                raise ValueError('The active document changed. Create the plate again in the intended design.')
            result = generation.generate(job['settings'])
            _last_creation = result
            status('complete',f"Created {result['pieces']} piece(s) in {result['seconds']:.2f} s",result)
            app.activeViewport.fit()
        except Exception as error:
            args.executeFailed = True
            args.executeFailedMessage = str(error)
            status('error',str(error))
            adsk.core.Application.get().log(traceback.format_exc())
        finally:
            _pending = None


class _GenerateDestroyed(adsk.core.CommandEventHandler):
    def notify(self, args):
        global _pending
        if _pending is not None:
            _pending = None
            status('error','Creation cancelled. No baseplate was added.')


class _GenerateCreated(adsk.core.CommandCreatedEventHandler):
    def __init__(self, execute, destroyed):
        super().__init__()
        self.execute = execute
        self.destroyed = destroyed

    def notify(self, args):
        args.command.isRepeatable = False
        args.command.isExecutedWhenPreEmpted = False
        args.command.execute.add(self.execute)
        args.command.destroy.add(self.destroyed)


class _ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            show()
        except Exception:
            adsk.core.Application.get().log(traceback.format_exc())


class _CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, execute_handler):
        super().__init__()
        self.execute_handler = execute_handler

    def notify(self, args):
        args.command.execute.add(self.execute_handler)


def start():
    """Register a standard Fusion command; safe to call more than once."""
    global _started
    if _started:
        return
    ui = _ui()
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    panels = [workspace.toolbarPanels.itemById(panel_id) for panel_id in PANEL_IDS]
    if not all(panels):
        raise RuntimeError('The Design workspace Create or Add-ins panel is unavailable.')
    command = ui.commandDefinitions.addButtonDefinition(
        COMMAND_ID, 'Gridfinity Baseplates',
        'Fit a drawer or choose a grid size, then create printable Gridfinity baseplates.', ICON_FOLDER)
    execute = _ExecuteHandler()
    created = _CreatedHandler(execute)
    command.commandCreated.add(created)
    _handlers.extend([execute, created])
    for panel in panels:
        control = panel.controls.addCommand(command)
        if panel.id == 'SolidCreatePanel':
            control.isPromotedByDefault = True
            control.isPromoted = True
    create_command = ui.commandDefinitions.addButtonDefinition(CREATE_ID,'Create Gridfinity baseplate',
        'Create separate printable baseplate bodies.','')
    generate = _GenerateHandler()
    destroyed = _GenerateDestroyed()
    created = _GenerateCreated(generate,destroyed)
    create_command.commandCreated.add(created)
    _handlers.extend([generate,destroyed,created])
    catalog.start()
    _started = True


def show():
    """Open the local HTML in Fusion's supported embedded browser."""
    ui = _ui()
    palette = ui.palettes.itemById(PALETTE_ID)
    if not palette:
        url = (Path(__file__).parent / 'palette.html').resolve().as_uri()
        palette = ui.palettes.add(
            PALETTE_ID, 'Gridfinity Workshop — Baseplate', url,
            False, True, True, 480, 760, True)
        if not palette:
            raise RuntimeError('Fusion could not create the preview palette.')
        palette.dockingOption = adsk.core.PaletteDockingOptions.PaletteDockOptionsToVerticalOnly
        palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
        palette.setMinimumSize(360, 480)
        handler = _HTMLHandler()
        palette.incomingFromHTML.add(handler)
        _handlers.append(handler)
    palette.isVisible = True
    return palette


def inspect():
    """Ask the page for its current UI state through the official bridge."""
    palette = _ui().palettes.itemById(PALETTE_ID)
    if not palette:
        raise RuntimeError('Open the preview before inspecting it.')
    palette.sendInfoToHTML('inspect', '{}')


def diagnostics():
    palette = _ui().palettes.itemById(PALETTE_ID)
    return {
        'started': _started,
        'visible': bool(palette and palette.isVisible),
        'size': [palette.width, palette.height] if palette else None,
        'lastPreview': _last_preview,
        'lastResponse': _last_response,
        'lastCreation': _last_creation,
        'creationPending': _pending is not None,
        'messages': _messages,
    }


def run(context):
    start()


def stop(context):
    """Remove only the workshop palettes, controls, and commands."""
    global _started, _last_preview, _last_response, _pending
    catalog.stop()
    ui = _ui()
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    for panel_id in PANEL_IDS:
        panel = workspace.toolbarPanels.itemById(panel_id) if workspace else None
        control = panel.controls.itemById(COMMAND_ID) if panel else None
        if control:
            control.deleteMe()
    command = ui.commandDefinitions.itemById(COMMAND_ID)
    if command:
        command.deleteMe()
    command = ui.commandDefinitions.itemById(CREATE_ID)
    if command:
        command.deleteMe()
    _handlers.clear()
    _messages.clear()
    _last_preview = _last_response = None
    _started = False
    _pending = None
