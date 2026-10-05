"""Local WebGL prototype, independent of Fusion CAD generation."""
import json
from pathlib import Path
import adsk.core

PALETTE_ID='GridfinityWorkshop_ThreePreview'
_handlers=[]
_last_response=None

class Response(adsk.core.HTMLEventHandler):
    def notify(self,args):
        global _last_response
        data=json.loads(args.data)
        if isinstance(data,dict) and isinstance(data.get('data'),str):data=json.loads(data['data'])
        _last_response=data
        args.returnData=json.dumps({'ok':True})

def show():
    ui=adsk.core.Application.get().userInterface
    p=ui.palettes.itemById(PALETTE_ID)
    if not p:
        p=ui.palettes.add(PALETTE_ID,'Gridfinity - Live Three.js preview',
            (Path(__file__).parent/'three-demo.html').as_uri()+'?v=1',True,True,True,960,720,True)
        p.dockingState=adsk.core.PaletteDockingStates.PaletteDockStateFloating
        p.setMinimumSize(500,480)
        handler=Response();p.incomingFromHTML.add(handler);_handlers.append(handler)
    p.isVisible=True
    return p

def stop():
    p=adsk.core.Application.get().userInterface.palettes.itemById(PALETTE_ID)
    if p:p.deleteMe()
    _handlers.clear()
