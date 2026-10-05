"""Instrument, do not replace, the production catalog HTML callback.
Load into a retained module namespace in Fusion. setup() attaches a second
observer and wraps the original notify method for entry/exit evidence.
"""
import adsk.core,sys,json,time
from pathlib import Path
OUT=Path(r'D:\Code Projects\GridfinityWorkshop\.agents\qa\runs\2026-10-04\bridge-investigation')
OUT.mkdir(parents=True,exist_ok=True)
def catalog():
 return next(m for n,m in list(sys.modules.items()) if str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/catalog.py'))
def log(kind,**details):
 with (OUT/'events.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(kind=kind,time=time.time(),**details),default=str)+'\n')
class Observer(adsk.core.HTMLEventHandler):
 def __init__(self):super().__init__()
 def notify(self,args):log('observer',action=args.action,data=args.data[:240])
def setup():
 m=catalog();original=m.HTMLHandler.notify
 def traced(self,args):
  log('original-entry',action=args.action,handler=id(self))
  original(self,args)
  log('original-exit',action=args.action,responseSet=m._last_response is not None,pending=m._pending is not None,created=m._last_creation is not None)
 m.HTMLHandler.notify=traced
 p=adsk.core.Application.get().userInterface.palettes.itemById(m.PALETTE_ID)
 observer=Observer();assert p.incomingFromHTML.add(observer)
 sys._qa_bridge_observer=observer
 log('setup',url=p.htmlFileURL,handlers=[str(type(h)) for h in m._handlers],module=m.__name__)
 p.sendInfoToHTML('inspect','{}')
 return original
