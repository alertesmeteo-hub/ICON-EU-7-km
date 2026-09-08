import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_icon_eu import VARIABLES, STEPS, select_run, grid_indices, to_hourly

class PipelineTests(unittest.TestCase):
    def test_incomplete_new_run_does_not_replace_complete_run(self):
        listings = {v: {('2026090700',s):'url' for s in STEPS} for v in VARIABLES}
        for v in VARIABLES: listings[v][('2026090706',0)] = 'url'
        self.assertEqual(select_run(listings), '2026090700')
        del listings['tot_prec'][('2026090700',120)]
        with self.assertRaises(RuntimeError): select_run(listings)
    def test_grid_indices_and_longitude_wrap(self):
        m={'gridType':'regular_ll','Ni':4,'Nj':3,'jPointsAreConsecutive':0,'alternativeRowScanning':0,'iScansNegatively':0,'jScansPositively':0,'longitudeOfFirstGridPointInDegrees':359.,'latitudeOfFirstGridPointInDegrees':50.,'iDirectionIncrementInDegrees':1.,'jDirectionIncrementInDegrees':1.}
        np.testing.assert_array_equal(grid_indices(m,np.array([50.,49.]),np.array([-1.,1.])),[0,6])
        with self.assertRaises(ValueError): grid_indices(m,np.array([60.]),np.array([1.]))
    def test_units_rain_conservation_and_gust_period(self):
        raw={v:np.zeros((len(STEPS),2)) for v in VARIABLES}
        raw['t_2m'][:]=283.15; raw['u_10m'][:]=3; raw['v_10m'][:]=4; raw['vmax_10m'][:]=10
        raw['tot_prec'][:]=np.array(STEPS)[:,None]*2
        starts=[max(0,s-(1 if s<=78 else 3)) for s in STEPS]
        hourly, periods=to_hourly(raw,starts)
        self.assertEqual(hourly.shape,(120,2,5))
        np.testing.assert_allclose(hourly[0,0,:4],[10,2,18,36])
        self.assertEqual(float(hourly[:,0,1].sum()),240)
        self.assertEqual(periods[78:81],[3,3,3])
        raw['tot_prec'][-1]=0
        with self.assertRaises(ValueError): to_hourly(raw,starts)
if __name__=='__main__': unittest.main()
