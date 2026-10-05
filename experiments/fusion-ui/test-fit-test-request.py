import importlib,sys,types,unittest
from pathlib import Path
package=types.ModuleType('_fit_request_test');package.__path__=[str(Path(__file__).parent/'GridfinityUIPreview')];sys.modules[package.__name__]=package
validate=importlib.import_module(package.__name__+'.fit_test_request').validate
BASE=dict(family='tests',testType='pin',testStart=.15,testStep=.05,testCount=5,pinDiameter=1.75,pinAllowance=.25,pinOverrides=False)
class FitTests(unittest.TestCase):
    def test_bore_ladder(self):
        self.assertEqual([round(s['bore'],2) for s in validate(BASE)['samples']],[1.9,1.95,2,2.05,2.1])
        for values in [dict(testCount=0),dict(testStep=float('nan')),dict(testStart=.8),dict(testCount=8)]:
            with self.subTest(values=values),self.assertRaises(ValueError):validate({**BASE,**values})
    def test_spacing_and_print_area(self):
        c=dict(BASE,testType='spacing',testStart=1,testStep=1,testCount=3,testAxis='both',testStackDepth=28,
               channelShape='round',storedDiameter=6,storedClearance=.5,channelColumns=3,channelRows=3)
        self.assertEqual([(s['w'],s['d']) for s in validate(c)['samples']],[(25.5,31.5),(27.5,33.5),(29.5,35.5)])
        with self.assertRaises(ValueError):validate(dict(c,testStart=30,storedDiameter=30,channelColumns=5,channelRows=5))
    def test_envelope_closed_height(self):
        c=validate(dict(BASE,testType='envelope',cols=6,rows=6,height=6,testPosts=True,testSource='clasp'))
        self.assertEqual(c['samples'][0]['w'],251.5);self.assertEqual(c['samples'][0]['h'],45.7)
        c=validate(dict(BASE,testType='envelope',cols=2,rows=1,height=6,testPosts=True,testSource='standard',rim=True,dovetailLid=True))
        self.assertAlmostEqual(c['samples'][0]['h'],51.4)
if __name__=='__main__':unittest.main()
