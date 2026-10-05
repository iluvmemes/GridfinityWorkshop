"""Run with python experiments/fusion-ui/test-request.py (no Fusion needed)."""
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('request', Path(__file__).resolve().parents[2]/'workshop/request.py')
request = importlib.util.module_from_spec(spec)
spec.loader.exec_module(request)
DEFAULT = dict(mode='grid',style='skeleton',columns=6,rows=6,anchor=4,
               magnets=True,screws=False,magnetDiameter=6.08,magnetDepth=2.4,
               bedWidth=220,bedDepth=220)

class RequestTests(unittest.TestCase):
    def test_invalid_inputs(self):
        for change in ({'columns':7},{'columns':1.5},{'columns':True},
                       {'magnetDiameter':float('nan')},{'bedWidth':float('inf')},
                       {'magnets':'yes'},{'anchor':9},{'magnetDiameter':7}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                request.validate(dict(DEFAULT,**change))

    def test_bed_boundary_and_partition(self):
        for size in (60,83.5,83.9,84,125.5,209.5,209.9,210,220,251.5):
            s=request.validate(dict(DEFAULT,bedWidth=size,bedDepth=size))
            area=0
            for p in s['pieces']:
                w,d=p['x1']-p['x0'],p['y1']-p['y0']
                self.assertLessEqual(w,size)
                self.assertLessEqual(d,size)
                area+=w*d
            self.assertAlmostEqual(area,s['widthMM']*s['depthMM'])

    def test_drawer_alignment_and_press_fit(self):
        for anchor in range(9):
            s=request.validate(dict(DEFAULT,mode='fit',width=230,depth=190,clearance=.5,anchor=anchor))
            self.assertEqual((s['columns'],s['rows']),(5,4))
            self.assertEqual(s['magnetDiameter'],6.08)
            self.assertAlmostEqual(s['left']+s['right'],19.5)
            self.assertAlmostEqual(s['back']+s['front'],21.5)
            self.assertEqual(len(s['pieces']),2)

if __name__=='__main__':
    unittest.main()
