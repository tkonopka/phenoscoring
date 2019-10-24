"""
Tests for contents of phenoscoring/phenotypedatum.py
"""

import unittest
from datetime import datetime
from scoring.experiment import Experiment
from phenoscoring.phenotypedatum import PhenotypeDatum
from phenoscoring.time import timestamp_format


e1 = Experiment(1, 0.8, 0.05)
e2 = Experiment(0, 0.8, 0.05)
e3 = Experiment(1, 0.6, 0.15)


class PhenotypeDatumTests(unittest.TestCase):
    """Test cases for handling object with phenotype and experiment"""
    
    def test_init(self):
        """init of basic object"""
                
        datum = PhenotypeDatum("MP:1", Experiment(1, 0.7, 0.1))
                
        self.assertEqual(datum.phenotype, "MP:1")
        self.assertEqual(datum.value, 1)
        self.assertEqual(datum.tpr, 0.7)
        self.assertEqual(datum.fpr, 0.1)
        self.assertFalse(datum.timestamp is None)

    def test_str(self):
        """object can be summarized."""
        
        datum = PhenotypeDatum("MP:001", e1)        
        datum_str = repr(datum)        
        self.assertTrue("MP:001" in datum_str)
        self.assertTrue("Experiment" in datum_str)
        self.assertTrue("0.8" in datum_str)

    def test_default_timestamp(self):
        """default should set a timestamp"""
        
        now = datetime.now()            
        datum = PhenotypeDatum("MP:1", Experiment(1, 0.7, 0.1))
        stamp = datetime.strptime(datum.timestamp, timestamp_format)
        diff = (now-stamp).total_seconds()
        self.assertLess(diff, 60, "stamps should be within a few seconds")

    def test_compare_by_phenotype(self):
        """comparison should compare phenotypes, experiments, timestamps"""
        d1 = PhenotypeDatum("MP:1", e1, "2018")
        d2 = PhenotypeDatum("MP:1", e1, "2018")
        d3 = PhenotypeDatum("MP:2", e1, "2018")
        self.assertTrue(d1==d2)
        self.assertTrue(d1!=d3)        

    def test_compare_by_experiment(self):
        """comparison should compare phenotypes, experiments, timestamps"""
        d1 = PhenotypeDatum("MP:1", e1, "2018")
        d2 = PhenotypeDatum("MP:1", e2, "2018")
        self.assertFalse(d1==d2)
    
    def test_compare_by_timestamp(self):
        """comparison should compare phenotypes, experiments, timestamps"""
        d1 = PhenotypeDatum("MP:1", e1, "2018")
        d2 = PhenotypeDatum("MP:1", e1, "2017")        
        self.assertFalse(d1==d2)            

    def test_order_by_phenotype(self):
        d1 = PhenotypeDatum("MP:1", e1, "2018")
        d2 = PhenotypeDatum("MP:2", e1, "2018")
        self.assertTrue(d1<d2)
        self.assertTrue(d2>d1)

    def test_order_by_value(self):
        d1 = PhenotypeDatum("MP:1", e2, "2018")
        d2 = PhenotypeDatum("MP:1", e1, "2018")
        self.assertTrue(d1<d2)
        self.assertTrue(d2>d1)
    
    def test_order_by_timestamp(self):
        d1 = PhenotypeDatum("MP:1", e1, "2016")
        d2 = PhenotypeDatum("MP:1", e1, "2018")
        self.assertTrue(d1<d2)
        self.assertTrue(d2>d1)

