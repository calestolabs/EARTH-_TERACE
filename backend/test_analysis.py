import unittest,math
from .analysis import annual,stats
class AnalysisTests(unittest.TestCase):
    def test_known_monotonic(self):
        r=stats([dict(year=2000+i,value=2*i) for i in range(10)])
        self.assertEqual(r['slope'],2);self.assertEqual(r['sen'],2);self.assertEqual(r['S'],45)
        self.assertAlmostEqual(r['p'],0.00008303070332645,places=10)
    def test_tied_constant(self):
        r=stats([dict(year=2000+i,value=20) for i in range(10)])
        self.assertEqual(r['p'],1);self.assertFalse(r['significant']);self.assertEqual(r['sen'],0)
    def test_full_years_and_date_bounds(self):
        rows=[{'date':f'2000-{i:02d}','value':1} for i in range(1,13)]+[{'date':'2001-01','value':999}]
        self.assertEqual(annual(rows,'rainfall','2000-01-01','2001-12-31')['points'],[{'year':2000,'value':12}])
        self.assertEqual(annual(rows,'soil','2000-01-02','2000-12-31')['points'],[])
    def test_weighted_mean(self):
        rows=[{'date':f'2000-{i:02d}','value':29 if i==2 else 0} for i in range(1,13)]
        self.assertAlmostEqual(annual(rows,'temperature','2000-01-01','2000-12-31')['points'][0]['value'],841/366)
    def test_insufficient(self):self.assertIsNone(stats([{'year':2000,'value':1}]))
if __name__=='__main__':unittest.main()
