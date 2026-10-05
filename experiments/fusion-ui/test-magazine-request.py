"""Pure layout validation: python experiments/fusion-ui/test-magazine-request.py."""
import importlib,sys,types,unittest
from pathlib import Path
p=types.ModuleType('_magazine_tests');p.__path__=[str(Path(__file__).parent/'GridfinityUIPreview')];sys.modules[p.__name__]=p
validate=importlib.import_module(p.__name__+'.magazine_request').validate
DEFAULT=dict(family='magazine',title='Magazine',cols=2,rows=1,height=4,cartLength=68,cartWidth=17.5,
    cartridgeHeight=8,slot=.3,quantity=2,orientation='0',magnet='press',magnetDepth=2.4)

class MagazineRequests(unittest.TestCase):
    def test_optional_cutouts(self):
        self.assertTrue(validate(DEFAULT)['magazineCutouts'])
        self.assertFalse(validate({**DEFAULT,'magazineCutouts':False})['magazineCutouts'])
        with self.assertRaises(ValueError):validate({**DEFAULT,'magazineCutouts':'false'})
        with self.assertRaises(ValueError):validate({**DEFAULT,'height':2,'cartridgeHeight':4,'magazineCutouts':False})
        self.assertTrue(validate({**DEFAULT,'height':2,'cartridgeHeight':4,'magazineCutouts':True})['magazineCutouts'])
    def test_two_per_cell_width(self):
        c=validate(DEFAULT)
        self.assertEqual(c['capacity'],2);self.assertEqual(c['diameter'],6.08)
        self.assertEqual(c['widthMM'],83.5);self.assertEqual(c['depthMM'],41.5)
        self.assertAlmostEqual(c['overallMM'],66.7)
        self.assertAlmostEqual(c['seats'][1]['y']-c['seats'][0]['y'],19.3)
        self.assertAlmostEqual(c['seats'][0]['x'],1.35)
    def test_rotation_and_centering(self):
        a=validate(DEFAULT);b=validate({**DEFAULT,'cols':1,'rows':2,'orientation':'90'})
        for q,r in zip(a['seats'],b['seats']):
            for u,v in [('x','y'),('y','x'),('w','d'),('d','w')]:self.assertAlmostEqual(q[u],r[v])
    def test_rejections(self):
        for changes in [dict(quantity=3),dict(cols=1),dict(rows=7),dict(slot=.09),dict(slot=float('nan')),
            dict(orientation='45'),dict(quantity=True),dict(cartridgeHeight=3),dict(cartridgeHeight=4),dict(height=21)]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):validate({**DEFAULT,**changes})
    def test_partial_and_minimum(self):
        c=validate({**DEFAULT,'quantity':1});self.assertEqual(len(c['seats']),1)
        c=validate({**DEFAULT,'cartridgeHeight':4,'height':3});self.assertAlmostEqual(c['overallMM'],38.7)
    def test_access_windows_disjoint(self):
        for orientation in ('0','90'):
            c=validate({**DEFAULT,'cols':6,'rows':6,'quantity':12,'orientation':orientation})
            for i,a in enumerate(c['windows']):
                self.assertGreater(a['w'],0);self.assertGreater(a['d'],0)
                for b in c['windows'][i+1:]:
                    self.assertFalse(a['x']<b['x']+b['w'] and b['x']<a['x']+a['w'] and a['y']<b['y']+b['d'] and b['y']<a['y']+a['d'])

if __name__=='__main__':unittest.main()
