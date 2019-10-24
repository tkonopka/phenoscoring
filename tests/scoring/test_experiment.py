"""
Tests for contents of scoring/representation.py
"""

import unittest
from scoring.experiment import Experiment
from scoring.experiment import PositiveExperiment, NegativeExperiment


class ExperimentTests(unittest.TestCase):
    """Test cases for class PositiveExperiment and NegativeExperiment."""
        
    def test_positive(self):
        """positive experiment increases confidence."""  
        
        pe = PositiveExperiment()
        self.assertGreater(pe.update(0.5), 0.5, "positive evidence increases p")

    def test_negative(self):
        """positive experiment increases confidence."""  
        
        ne = NegativeExperiment()
        self.assertLess(ne.update(0.5), 0.5, "negative evidence decreases p")

    def test_equal_tprfpr(self):
        """positive experiment increases confidence."""  
        
        pe = PositiveExperiment(tpr=0.5, fpr=0.5)
        ne = NegativeExperiment(tpr=0.5, fpr=0.5)
        self.assertEqual(ne.update(0.5), 0.5, "updates keep p constant")
        self.assertEqual(pe.update(0.5), 0.5, "updates keep p constant")

    def test_comparisons(self):
        """intialization and comparison"""  
        
        e1 = Experiment(1, 0.4, 0.2)
        e2 = Experiment(1, 0.4, 0.2)
        e3 = Experiment(1, 0.5, 0.2)
        self.assertEqual(e1, e2, "all equal values")
        self.assertNotEqual(e1, e3, "tpr not equal")
        self.assertNotEqual(e1, 0, "different classes")            

    def test_equal_ranges(self):
        """positive experiment increases confidence."""  
                
        pe = PositiveExperiment(tpr=0.8, fpr=0.2)
        # all updates will make new p in range [0, 1]
        for x in [0.01, 0.05, 0.1, 0.2, 0.6, 0.8, 0.99]:                        
            self.assertGreater(pe.update(x), 0)
            self.assertLess(pe.update(x), 1)

    def test_equal_ordering(self):
        """positive experiment increases confidence."""  
                
        pe = PositiveExperiment(tpr=0.8, fpr=0.2)                
        self.assertGreater(pe.update(0.2), pe.update(0.1), 
                           "order relation of ps preserved by experiment")

    def test_lt_by_value(self):
        """experiments can be ordered for sorting"""  
                
        e1 = Experiment(1, tpr=0.8, fpr=0.2)
        e2 = Experiment(1, tpr=0.8, fpr=0.2)                
        self.assertFalse(e1 < e2, "equal experiments cannot be lt")
        self.assertFalse(e2 < e1, "equal experiments cannot be lt")
        e3 = Experiment(0, tpr=0.8, fpr=0.2)
        self.assertTrue(e3 < e1, "lt due to value")
        e4 = Experiment(0, tpr=1, fpr=0.3)        
        self.assertTrue(e4 < e1, "lt despite tpr and fpr values")

    def test_lt_by_tprfpr(self):
        """experiments can be ordered for sorting"""  
                
        e1 = PositiveExperiment(tpr=0.5, fpr=0.4)
        e2 = PositiveExperiment(tpr=0.8, fpr=0.1)                
        self.assertTrue(e1 < e2)
        self.assertFalse(e2 < e1)        
        e3 = PositiveExperiment(tpr=0.5, fpr=0.3)
        self.assertTrue(e3 < e1)

    def test_str(self):
        """string rep."""
        
        ee = PositiveExperiment(tpr=0.5, fpr=0.1)
        ee_str = "Experiment(1, 0.5, 0.1)"
        self.assertEqual(str(ee), ee_str)

