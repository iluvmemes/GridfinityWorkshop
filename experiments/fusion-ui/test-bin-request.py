"""Pure validation checks: python experiments/fusion-ui/test-bin-request.py."""
import importlib,sys,types,unittest
from pathlib import Path
package=types.ModuleType('_bin_request_test')
package.__path__=[str(Path(__file__).parent/'GridfinityUIPreview')]
sys.modules[package.__name__]=package
validate=importlib.import_module(package.__name__+'.bin_request').validate
DEFAULT=dict(family='clasp',title='Test',cols=2,rows=1,height=6,interior='open',rim=False,
             scoop=False,label=False,buckle=.2,pin=2,grip=2,magnet='press',diameter=99,magnetDepth=2.4,
             divX=2,divY=2,channelShape='round',storedDiameter=6,storedClearance=.5,
             channelWidth=6,channelDepth=10,channelColumns=9,channelRows=5)

class BinRequests(unittest.TestCase):
    def test_fixed_dovetail_height(self):
        for rim in (False,True):
            c=validate({**DEFAULT,'family':'standard','dovetailLid':True,'rim':rim})
            self.assertAlmostEqual(c['overallMM'],42+5.6+(3.8 if rim else 0))
        self.assertFalse(validate({**DEFAULT,'dovetailLid':True})['dovetailLid'])
        self.assertFalse(validate(DEFAULT)['dovetailLid'])
        with self.assertRaises(ValueError):validate({**DEFAULT,'dovetailLid':'yes'})
    def test_cartridge_dimensions_and_limits(self):
        base={**DEFAULT,'family':'cartridge','cartLength':68,'cartWidth':17.5,'height':4}
        c=validate(base)
        self.assertAlmostEqual(c['widthMM'],80.2)
        self.assertAlmostEqual(c['overallMM'],31.7)
        self.assertEqual(c['magnet'],'off')
        self.assertFalse(c['rim'])
        self.assertAlmostEqual(c['cavities'][0]['w'],64)
        for changes in [dict(height=3),dict(cartLength=29.9),dict(cartLength=221),dict(cartWidth=11.9),dict(cartWidth=81)]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):validate({**base,**changes})
        c=validate({**base,'interior':'magnets','channelColumns':8,'channelRows':1})
        self.assertEqual(len(c['cavities']),8)
        with self.assertRaises(ValueError):validate({**base,'interior':'magnets','channelColumns':8,'channelRows':2})
        with self.assertRaises(ValueError):validate({**base,'interior':'magnets','channelColumns':8,'channelRows':1,'channelGapX':3})

    def test_clasp_boundaries(self):
        for values in ({'cols':1},{'cols':7},{'height':5},{'height':21},{'rows':1.5},
                       {'buckle':-.1},{'pin':float('nan')},{'grip':1},{'family':'cartridge'}):
            with self.subTest(values=values),self.assertRaises(ValueError):validate({**DEFAULT,**values})

    def test_closed_height_and_press_fit(self):
        c=validate(DEFAULT)
        self.assertEqual(c['diameter'],6.08)
        self.assertAlmostEqual(c['overallMM'],45.7)
        self.assertAlmostEqual(c['cavities'][0]['w'],67.3)

    def test_channel_hardware_reservation(self):
        c=validate({**DEFAULT,'interior':'magnets'})
        self.assertEqual(len(c['cavities']),45)
        with self.assertRaises(ValueError):validate({**DEFAULT,'interior':'magnets','channelColumns':10})
        # Standard bins do not reserve the clasp's 12.2 mm closure space.
        self.assertEqual(len(validate({**DEFAULT,'family':'standard','interior':'magnets','channelColumns':10})['cavities']),50)

    def test_standard_and_blank_remain_available(self):
        for family,interior in [('standard','open'),('blank','solid')]:
            self.assertEqual(validate({**DEFAULT,'family':family,'interior':interior,'cols':1,'height':2})['heightMM'],14)

    def test_legacy_pin_sizes_and_explicit_overrides(self):
        c=validate(DEFAULT)
        self.assertEqual(list(c['pinBores'].values()),[2,2,2.2,2.2])
        c=validate({**DEFAULT,'pinDiameter':1.75,'pinAllowance':.3,'pinOverrides':False})
        for value in c['pinBores'].values():self.assertAlmostEqual(value,2.05)
        c=validate({**DEFAULT,'pinDiameter':1.75,'pinAllowance':.25,'pinOverrides':True,
                    'bodyPinAllowance':.1,'lidPinAllowance':.2,'lidLatchAllowance':.3,'bucklePinAllowance':.4})
        for actual,expected in zip(c['pinBores'].values(),[1.85,1.95,2.05,2.15]):self.assertAlmostEqual(actual,expected)
        with self.assertRaises(ValueError):validate({**DEFAULT,'pinDiameter':2.5,'pinAllowance':1,'pinOverrides':False})

    def test_independent_channel_gaps_and_capacity(self):
        c=validate({**DEFAULT,'interior':'magnets','channelColumns':6,'channelRows':3,
                    'channelGapLinked':False,'channelGapX':3,'channelGapY':5})
        self.assertAlmostEqual(c['cavities'][1]['x']-c['cavities'][0]['x'],9.5)
        self.assertAlmostEqual(c['cavities'][6]['y']-c['cavities'][0]['y'],11.5)
        with self.assertRaises(ValueError):validate({**DEFAULT,'interior':'magnets','channelGapX':3})
        with self.assertRaises(ValueError):validate({**DEFAULT,'interior':'magnets','channelGapX':float('nan')})

if __name__=='__main__':unittest.main()
