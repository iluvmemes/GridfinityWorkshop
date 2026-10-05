"""Pure retention validation and compatibility checks; no Fusion import."""
import importlib,sys,types,unittest
from pathlib import Path
pkg=types.ModuleType('_retention_unit');pkg.__path__=[str(Path(__file__).resolve().parents[2]/'workshop')];sys.modules[pkg.__name__]=pkg
validate=importlib.import_module(pkg.__name__+'.bin_request').validate
BASE=dict(family='standard',cols=1,rows=1,height=2,interior='open',dovetailLid=True,rim=False,scoop=False,label=False,magnet='off',divX=2,divY=2)
class Retention(unittest.TestCase):
 def test_legacy_and_disabled(self):
  self.assertEqual(validate(BASE)['lidRetention'],'none')
  self.assertEqual(validate(dict(BASE,dovetailLid=False,lidRetention='both'))['lidRetention'],'none')
  self.assertEqual(validate(dict(BASE,family='blank',lidRetention='both'))['lidRetention'],'none')
 def test_independent_options_and_fit(self):
  for mode in ['none','bump','magnet','both']:
   for size in ['3','6']:
    for fit,extra in [('press',.08),('clearance',.5)]:
     c=validate(dict(BASE,lidRetention=mode,lidMagnetSize=size,lidMagnetFit=fit))
     p=c['lidRetentionPlan'];self.assertEqual(len(p['detents']),2 if mode in ['bump','both'] else 0)
     self.assertEqual(p['magnets'],4 if mode in ['magnet','both'] else 0)
     self.assertEqual(c['overallMM'],19.6)
     if p['magnets']:self.assertAlmostEqual(p['diameter'],int(size)+extra)
 def test_invalid_settings(self):
  for change in [dict(lidRetention='stop'),dict(lidRetention='bump',lidDetentInterference=.3),dict(lidRetention='bump',lidDetentInterference=True),dict(lidRetention='magnet',lidMagnetSize='8'),dict(lidRetention='magnet',lidMagnetFit='loose')]:
   with self.assertRaises(ValueError):validate(dict(BASE,**change))
 def test_preserve_channel_openings(self):
  c=dict(BASE,lidRetention='magnet',interior='magnets',channelShape='round',storedDiameter=6,storedClearance=.5,channelColumns=5,channelRows=5,channelGapX=1,channelGapY=1,channelGapLinked=True)
  with self.assertRaisesRegex(ValueError,'overlap storage channels'):validate(c)
  c['channelColumns']=1;c['channelRows']=1;self.assertEqual(len(validate(c)['cavities']),1)
if __name__=='__main__':unittest.main()
