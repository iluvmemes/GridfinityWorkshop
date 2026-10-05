"""Bin catalog with native transactional creation for validated families."""
import json
from pathlib import Path
import adsk.core
from . import bin_generation,clasp_generation,cartridge_generation,magazine_generation,fit_test_generation
from .bin_request import validate
from .magazine_request import validate as validate_magazine
from .fit_test_request import validate as validate_test

COMMAND_ID = 'GridfinityWorkshop_BinCatalog_Show'
PALETTE_ID = 'GridfinityWorkshop_BinCatalog_Palette'
_handlers = []
_last_response = None
_pending = None
_last_creation = None
GENERATE_ID = 'GridfinityWorkshop_BinCatalog_Create'

class HTMLHandler(adsk.core.HTMLEventHandler):
    def notify(self, args):
        global _last_response
        try:
            if args.action in ('response', 'catalogReady'):
                data = json.loads(args.data)
                wrapped = data.get('data') if isinstance(data, dict) else None
                _last_response = json.loads(wrapped) if isinstance(wrapped, str) else data
                args.returnData = json.dumps({'ok': True, 'previewOnly': True})
            elif args.action == 'createBin':
                request_creation(json.loads(args.data))
                args.returnData = json.dumps({'ok': True, 'queued': True})
            elif args.action == 'threePreview':
                from . import three_preview
                three_preview.show()
                args.returnData=json.dumps({'ok':True})
            elif args.action == 'scoopPreview':
                from . import scoop_preview
                result=scoop_preview.show(json.loads(args.data).get('mode','solid'))
                args.returnData=json.dumps({'ok':True,'preview':result})
            else:
                args.returnData = json.dumps({'ok': False, 'error': 'Unsupported catalog action.'})
        except Exception as error:
            adsk.core.Application.get().log('Gridfinity bin catalog: ' + str(error))
            args.returnData = json.dumps({'ok':False,'error':str(error)})
            status('error',str(error))

class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        show()

class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        handler = ExecuteHandler()
        args.command.execute.add(handler)
        _handlers.append(handler)

def start():
    ui = adsk.core.Application.get().userInterface
    if ui.commandDefinitions.itemById(COMMAND_ID):
        return
    command = ui.commandDefinitions.addButtonDefinition(COMMAND_ID, 'Gridfinity Bins',
        'Explore standard bins, clasp bins, cartridges, magazines and custom blanks. Create standard bins, clasp designs, cartridges, magazines and custom blanks, or print fit tests.',
        str(Path(__file__).parent/'catalog-resources'))
    handler = CreatedHandler()
    command.commandCreated.add(handler)
    _handlers.append(handler)
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    control = workspace.toolbarPanels.itemById('SolidCreatePanel').controls.addCommand(command)
    control.isPromotedByDefault = True
    control.isPromoted = True
    definition = ui.commandDefinitions.addButtonDefinition(GENERATE_ID,'Create Gridfinity bin','Create a new bin body.','')
    generated = GenerateCreated()
    definition.commandCreated.add(generated)
    _handlers.append(generated)

def show():
    ui = adsk.core.Application.get().userInterface
    palette = ui.palettes.itemById(PALETTE_ID)
    if not palette:
        palette = ui.palettes.add(PALETTE_ID, 'Gridfinity Workshop — Bin catalog',
            (Path(__file__).parent/'catalog.html').resolve().as_uri() + '?v=24', False, True, True, 1000, 780, True)
        palette.setMinimumSize(390, 540)
        palette.dockingOption = adsk.core.PaletteDockingOptions.PaletteDockOptionsToVerticalOnly
        palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
        handler = HTMLHandler()
        palette.incomingFromHTML.add(handler)
        _handlers.append(handler)
    palette.isVisible = True
    return palette

def stop():
    from . import three_preview
    three_preview.stop()
    global _pending
    _pending=None
    ui = adsk.core.Application.get().userInterface
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    panel = workspace.toolbarPanels.itemById('SolidCreatePanel') if workspace else None
    control = panel.controls.itemById(COMMAND_ID) if panel else None
    if control:
        control.deleteMe()
    definition = ui.commandDefinitions.itemById(COMMAND_ID)
    if definition:
        definition.deleteMe()
    definition = ui.commandDefinitions.itemById(GENERATE_ID)
    if definition:
        definition.deleteMe()
    _handlers.clear()


def status(phase,message,result=None):
    p=adsk.core.Application.get().userInterface.palettes.itemById(PALETTE_ID)
    if p:p.sendInfoToHTML('creationStatus',json.dumps(dict(phase=phase,message=message,result=result)))


def request_creation(data):
    global _pending,_last_creation
    if _pending is not None:raise ValueError('A bin is already being created.')
    settings=validate_test(data) if isinstance(data,dict) and data.get('family')=='tests' else validate_magazine(data) if isinstance(data,dict) and data.get('family')=='magazine' else validate(data)
    app=adsk.core.Application.get()
    if app.userInterface.activeCommand!='SelectCommand':raise ValueError('Finish the active Fusion command first.')
    if not app.activeDocument:raise ValueError('Open a Fusion design first.')
    _pending=dict(settings=settings,document=app.activeDocument)
    status('creating','Creating geometry...')
    if settings['family'] in ('clasp','cartridge','tests'):
        # HTMLEvent is outside Command events: archive import can open its own design.
        try:
            _last_creation={'clasp':clasp_generation,'cartridge':cartridge_generation,'tests':fit_test_generation}[settings['family']].generate(settings)
            status('complete',f"Created new design in {_last_creation['seconds']:.2f} s",_last_creation)
        finally:_pending=None
        return
    queued=app.userInterface.commandDefinitions.itemById(GENERATE_ID).execute()
    if not queued:
        _pending=None
        raise RuntimeError('Fusion could not start bin creation.')

class GenerateExecute(adsk.core.CommandEventHandler):
    def notify(self,args):
        global _pending,_last_creation
        try:
            if not _pending:raise ValueError('Choose a bin in the catalog first.')
            app=adsk.core.Application.get()
            if app.activeDocument!=_pending['document']:raise ValueError('The active design changed; try Create again.')
            _last_creation=(magazine_generation if _pending['settings']['family']=='magazine' else bin_generation).generate(_pending['settings'])
            status('complete',f"Created bin in {_last_creation['seconds']:.2f} s",_last_creation)
            app.activeViewport.fit()
        except Exception as error:
            args.executeFailed=True
            args.executeFailedMessage=str(error)
            status('error',str(error))
            app=adsk.core.Application.get();app.log(str(error))
        finally:_pending=None

class GenerateDestroy(adsk.core.CommandEventHandler):
    def notify(self,args):
        global _pending
        if _pending is not None:
            _pending=None
            status('error','Creation cancelled; no bin added.')

class GenerateCreated(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
        self.execute=GenerateExecute();self.destroy=GenerateDestroy()
    def notify(self,args):
        args.command.isRepeatable=False
        args.command.isExecutedWhenPreEmpted=False
        args.command.execute.add(self.execute)
        args.command.destroy.add(self.destroy)
