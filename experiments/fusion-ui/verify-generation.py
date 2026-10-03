"""Integration checks in a disposable Fusion design; only run deliberately."""
import importlib
import json
from pathlib import Path
import sys
import types
import adsk.core
import adsk.fusion

ROOT = Path(r'D:\Code Projects\GridfinityWorkshop')


def run(_context: str):
    pkg = sys.modules['gf_creation_verification']
    g = importlib.reload(importlib.import_module(pkg.__name__+'.generation'))
    doc = pkg.document
    doc.activate()
    design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    manager = adsk.fusion.TemporaryBRepManager.get()
    original = design.rootComponent.occurrences.item(0).component.bRepBodies.item(0)
    protected = manager.copy(original)
    original_token = original.entityToken
    samples = []
    defaults = dict(mode='grid',style='skeleton',anchor=4,columns=1,rows=1,
                    magnets=True,screws=False,magnetDiameter=6.5,magnetDepth=2.4,
                    bedWidth=220,bedDepth=220)

    def difference(a,b):
        more, less = manager.copy(a), manager.copy(b)
        assert manager.booleanOperation(more,b,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        assert manager.booleanOperation(less,a,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        return {'extraMM3':more.volume*1000,'missingMM3':less.volume*1000}

    for label, edits in [
        ('3x3 reference',dict(columns=3,rows=3)),
        ('6x6 split reference',dict(columns=6,rows=6)),
        ('drawer press-fit solid screws',dict(mode='fit',width=230,depth=190,clearance=.5,
                                             style='solid',magnetDiameter=6.08,screws=True)),
        ('2x3 solid no hardware',dict(columns=2,rows=3,style='solid',magnets=False)),
        ('1x1 skeleton no hardware',dict(magnets=False)),
    ]:
        result = g.generate(dict(defaults,**edits))
        occurrence = design.findEntityByToken(result['occurrenceToken'])[0]
        component = occurrence.component
        combined = manager.copy(component.bRepBodies.item(0))
        for body in list(component.bRepBodies)[1:]:
            assert manager.booleanOperation(combined,body,adsk.fusion.BooleanTypes.UnionBooleanType)
        record = {'case':label,'result':result,'volumeMM3':combined.volume*1000,
                  'health':[int(f.healthState) for f in component.features],
                  'fullyConstrained':all(s.isFullyConstrained for s in component.sketches)}
        if 'reference' in label:
            n = edits['columns']
            expected = manager.createFromFile(str(ROOT/f'experiments/workflow-benchmark/plate-{n}.smt')).item(0)
            t = adsk.core.Matrix3D.create(); t.translation = adsk.core.Vector3D.create(0,0,.84)
            assert manager.transform(expected,t)
            record['difference'] = difference(combined,expected)
            assert max(record['difference'].values()) < 1e-5, record
        # Parameters must regenerate the native envelope even from zero padding.
        parameter = design.userParameters.itemByName(result['paddingParameters']['left'])
        before = parameter.expression
        parameter.expression = f'{parameter.value*10+1} mm'
        assert design.computeAll()
        assert all(int(f.healthState)==0 for f in component.features)
        parameter.expression = before
        assert design.computeAll()
        record['paddingEditHealthy'] = True
        record['protectedBodyDifference'] = difference(design.findEntityByToken(original_token)[0],protected)
        assert max(record['protectedBodyDifference'].values()) < 1e-5
        for body in component.bRepBodies:
            b = body.boundingBox
            assert (b.maxPoint.x-b.minPoint.x)*10 <= defaults['bedWidth']+1e-4
            assert (b.maxPoint.y-b.minPoint.y)*10 <= defaults['bedDepth']+1e-4
        # Tokens are machine/session specific; keep the report reviewable.
        del record['result']['occurrenceToken']
        samples.append(record)
    output = ROOT/'experiments/fusion-ui/generation-verification.json'
    output.write_text(json.dumps(samples,indent=2),encoding='utf-8')
    pkg.results = samples
    print(json.dumps(samples))
