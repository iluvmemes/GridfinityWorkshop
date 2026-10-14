"""Parameterize a working copy of the clasp reference; never edits its source."""
import sys,json,adsk.core,adsk.fusion

def run(_context: str):
    t=sys.modules['gf_clasp_dev'];t.document.activate()
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    def add(name,value,units,comment):
        p=d.userParameters.itemByName(name)
        if not p:p=d.userParameters.add(name,adsk.core.ValueInput.createByString(value),units,comment)
        return p
    add('HeightUnits','8','', 'Nominal height including 5 mm feet, in 7 mm Gridfinity units.')
    add('BodyHeight','HeightUnits * 7 mm - 5 mm','mm','Body shoulder height above the foot top.')
    add('BuckleExtra','0.2 mm','mm','Extra total lateral play over the original 0.10 mm clearance.')
    add('GripThickness','2 mm','mm','Pull-tab thickness, not outward projection.')
    mapping={'d10':'BodyHeight','d18':'BodyHeight - 4.5 mm','d26':'BodyHeight - 4.5 mm','d39':'BodyHeight - 6.8 mm',
      'd153':'BodyHeight - 18 mm','d154':'BodyHeight - 18 mm','d156':'BodyHeight - 24.1 mm',
      'd175':'BodyHeight + 1.5 mm','d180':'-(BodyHeight - 0.5 mm)','d187':'BodyHeight - 3 mm','d189':'BodyHeight - 8 mm',
      'd238':'BodyHeight - 18 mm','d245':'-(BodyHeight - 28 mm)',
      'd111':'BodyHeight - 0.8 mm','d217':'BodyHeight - 16 mm','d122':'Width - 8.9 mm - BuckleExtra','d220':'Width - 8.9 mm - BuckleExtra','d218':'GripThickness',
      'd47':'BodyHeight + 1.7 mm','d62':'BodyHeight + 3.7 mm','d73':'BodyHeight + 3.7 mm','d84':'BodyHeight + 3.7 mm','d100':'BodyHeight + 3.7 mm'}
    # Remove optional original storage cuts from the reusable enclosure template.
    body=next(c for c in d.allComponents if c.name=='Body')
    optional={'Windows other side','Windows','Window (1)','Magnet channels','Magnet channel (1)','Base magnets all cells','Base magnets per cell','Extrude13'}
    for f in reversed(list(body.features)):
        if f.name in optional:f.isSuppressed=True
    for name,expr in mapping.items():d.allParameters.itemByName(name).expression=expr
    # The prototype tapered a 41.5 mm profile for the entire 2.4 mm top section.
    # Restore the standard 0.25 mm clearance land, 2.15 mm taper and 37.2 mm waist.
    for name,expr in {'d129':'3.75 mm','d138':'1.6 mm',
        'd139':'CellsL * GridUnit / 2 - 2.4 mm','d140':'CellsW * GridUnit / 2 - 2.4 mm',
        'd141':'GridUnit - 4.8 mm','d142':'GridUnit - 4.8 mm'}.items():
        d.allParameters.itemByName(name).expression=expr
    ledge=body.features.itemByName('Standard foot clearance land')
    if not ledge:
        f=body.features.itemByName('Extrude6');f.timelineObject.rollTo(True)
        s=body.sketches.itemByName('Foot top')
        i=body.features.extrudeFeatures.createInput(s.profiles.item(0),adsk.fusion.FeatureOperations.JoinFeatureOperation)
        i.setDistanceExtent(False,adsk.core.ValueInput.createByString('-0.25 mm'));i.participantBodies=[body.bRepBodies.item(0)]
        ledge=body.features.extrudeFeatures.add(i);ledge.name='Standard foot clearance land'
        f.timelineObject.rollTo(True)
        f.startExtent=adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByString('-0.25 mm'))
        d.allParameters.itemByName('d134').expression='-2.15 mm';d.timeline.moveToEnd()
        pat=body.features.itemByName('Feet per cell');pat.timelineObject.rollTo(True)
        entities=pat.inputEntities;entities.add(ledge);pat.inputEntities=entities;d.timeline.moveToEnd()
    hardware=['Extrude13','Base magnets per cell','Base magnets all cells']
    for name in hardware:body.features.itemByName(name).isSuppressed=False
    for name in ['Feet per cell']+hardware[1:]:
        f=body.features.itemByName(name);f.timelineObject.rollTo(True)
        f.patternComputeOption=adsk.fusion.PatternComputeOptions.OptimizedPatternCompute;d.timeline.moveToEnd()
    for name in reversed(hardware):body.features.itemByName(name).isSuppressed=True
    d.computeAll()
    issues=[(c.name,f.name,f.errorOrWarningMessage) for c in d.allComponents for f in c.features if not f.isSuppressed and int(f.healthState)!=0]
    print(json.dumps({'issues':issues,'bodies':[(c.name,b.isSolid,b.volume*1000) for c in d.allComponents for b in c.bRepBodies]}))
    assert not issues
    (t.folder/'parameter-map.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
