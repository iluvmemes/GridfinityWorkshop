"""UI-only Fusion palette prototype. No geometry or document operations."""

import json
from pathlib import Path
import traceback

import adsk.core

COMMAND_ID = 'GridfinityWorkshop_UIPreview_Show'
PALETTE_ID = 'GridfinityWorkshop_UIPreview_Palette'
PANEL_ID = 'SolidScriptsAddinsPanel'
_handlers = []
_started = False
_messages = []
_last_preview = None
_last_response = None


def _ui():
    return adsk.core.Application.get().userInterface


class _HTMLHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
        global _last_preview, _last_response
        try:
            event = adsk.core.HTMLEventArgs.cast(args)
            data = json.loads(event.data) if event.data else {}
            # An explicit allowlist: there is deliberately no create/generate route.
            if event.action in ('ready', 'previewChanged'):
                _last_preview = data
                event.returnData = json.dumps({'ok': True, 'previewOnly': True})
            elif event.action == 'response':
                # Qt wraps the JavaScript return string in a data field.
                result = data.get('data') if isinstance(data, dict) else None
                _last_response = json.loads(result) if isinstance(result, str) else data
            elif event.action == 'uiError':
                adsk.core.Application.get().log('Gridfinity UI preview: ' + event.data)
            else:
                event.returnData = json.dumps({'ok': False, 'error': 'UI preview only; action unsupported'})
            _messages.append({'action': event.action, 'data': data})
            del _messages[:-20]
        except Exception:
            adsk.core.Application.get().log(traceback.format_exc())


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
    panel = ui.allToolbarPanels.itemById(PANEL_ID)
    if not panel:
        raise RuntimeError('The Design workspace Add-ins panel is unavailable.')
    command = ui.commandDefinitions.addButtonDefinition(
        COMMAND_ID, 'Gridfinity UI Preview',
        'Explore drawer sizing and baseplate layout. No geometry is generated.', '')
    execute = _ExecuteHandler()
    created = _CreatedHandler(execute)
    command.commandCreated.add(created)
    _handlers.extend([execute, created])
    panel.controls.addCommand(command)
    _started = True


def show():
    """Open the local HTML in Fusion's supported embedded browser."""
    ui = _ui()
    palette = ui.palettes.itemById(PALETTE_ID)
    if not palette:
        url = (Path(__file__).parent / 'palette.html').resolve().as_uri()
        palette = ui.palettes.add(
            PALETTE_ID, 'Gridfinity Workshop — UI Preview', url,
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
        'messages': _messages,
    }


def run(context):
    start()
    show()


def stop(context):
    """Remove only this prototype's palette, control, and command."""
    global _started, _last_preview, _last_response
    ui = _ui()
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()
    panel = ui.allToolbarPanels.itemById(PANEL_ID)
    control = panel.controls.itemById(COMMAND_ID) if panel else None
    if control:
        control.deleteMe()
    command = ui.commandDefinitions.itemById(COMMAND_ID)
    if command:
        command.deleteMe()
    _handlers.clear()
    _messages.clear()
    _last_preview = _last_response = None
    _started = False
