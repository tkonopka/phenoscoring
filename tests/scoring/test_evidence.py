'''
Tests for contents of scoring/evidence.py
'''

import json
import unittest
from scoring.evidence import estimate_update_ratio
from scoring.evidence import update_single, update_single_ratio
from scoring.evidence import InferenceDatum, InferenceChain


class EvidenceUpdateTests(unittest.TestCase):
    """Test for updating pvalues."""
    
    def test_update_increase(self):
        """tpr>fpr increases p."""
                
        self.assertGreater(update_single(0.1, 0.4, 0.1), 0.1)
        self.assertGreater(update_single(0.001, 0.2, 0.05), 0.001)

    def test_update_decrease(self):
        """tpr<fpr decreases p."""
                
        self.assertLess(update_single(0.1, 0.1, 0.3), 0.1)
        self.assertLess(update_single(0.01, 0.2, 0.5), 0.01)

    def test_update_neutral(self):
        """tpr=fpr keep p the same"""
                
        self.assertEqual(update_single(0.1, 0.4, 0.4), 0.1)        

    def test_update_ratio(self):
        """update depends on the ratio of tpr and fpr"""
                
        A = update_single(0.1, 0.4, 0.1)
        B = update_single(0.1, 0.8, 0.2)
        self.assertEqual(A, B)

    def test_update_ratio_function(self):
        """update can be performed using ratio function"""
                
        A = update_single(0.1, 0.4, 0.1)
        B = update_single_ratio(0.1, 0.25)
        self.assertAlmostEqual(A, B, )

    def test_estimate_ratio_down(self):
        """obtain an update ratio from two probabilities."""
        
        p0 = 0.1
        p1 = update_single_ratio(0.1, 2.5) # high ratio, i.e. fpr>tpr
        result = estimate_update_ratio(p0, p1)
        self.assertAlmostEqual(result, 2.5)        

    def test_estimate_ratio_up(self):
        """obtain an update ratio from two probabilities."""
        
        p0 = 0.1
        p1 = update_single_ratio(0.1, 0.2) # low ratio, i.e. fpr<tpr
        result = estimate_update_ratio(p0, p1)
        self.assertAlmostEqual(result, 0.2)
    

class EvidenceTests(unittest.TestCase):
    """Test evidence collection and assembly."""

    def test_inference_datum_string(self):
        """experiment datum can be stringified."""  
                
        d1 = InferenceDatum(0.8, 0.05)
        expected = dict(tpr=0.8, fpr=0.05)
        result = json.loads(str(d1))
        self.assertEqual(expected, result, "string and back")

    def test_chain_init_with_annotation(self):
        """can initialize an evidence chain with some annotations"""
        
        chain = InferenceChain(0.1, a=3, b=10)
        self.assertTrue(chain.has_annotation("a"))
        self.assertTrue(chain.has_annotation("b"))
        self.assertEqual(chain.a, 3)
        self.assertEqual(chain.b, 10)

    def test_inference_chain_string(self):
        """experiment chain can be stringified."""
        
        chain = InferenceChain(0.1)        
        chain.set_annotation("reference", "hello")        
        d1 = InferenceDatum(0.8, 0.05)
        chain.add(d1)
        # stringify and unstringify the object
        chainstr = str(chain)
        chainobj = json.loads(chainstr)
        # check for presence of recorded items
        self.assertEqual(chainobj["reference"], "hello")
        self.assertEqual(len(chainobj["data"]), 1)

    def test_inference_compute_posterior(self):
        """experiment chain with more than one item."""
        
        chain = InferenceChain(0.1)        
        chain.add(InferenceDatum(0.8, 0.05))
        p2 = chain.evaluate()        
        self.assertGreater(p2, 0.1, "positive evidence increase p")        
        chain.add(InferenceDatum(0.8, 0.1))
        p3 = chain.evaluate()
        self.assertGreater(p3, p2, "further evidence increases p more")

    def test_inference_chain_string_features(self):
        """string for experiment chain with more than one item ."""
    
        chain = InferenceChain(0.1)
        datum = InferenceDatum(0.6, 0.05)
        datum.set_annotation("featurename", "myfeature")
        chain.add(datum)
        datum = InferenceDatum(0.6, 0.05)
        datum.set_annotation("action", "truepos")        
        chain.add(datum)
        chainstr = chain.to_json()            
        self.assertTrue("myfeature" in chainstr)
        self.assertTrue("action" in chainstr)

    def test_rounding_individual_datum(self):
        """rounding for tpr/fpr values."""
                
        d1 = InferenceDatum(0.5+1e-10, 0.5+1e-12)
        # rounding does not happen in data representation
        self.assertNotEqual(d1.tpr, d1.fpr)
        # rounding should happen during to_json
        d1b = d1.round()        
        self.assertEqual(d1b.tpr, d1b.fpr)

    def test_rounding_chain_str(self):
        """rounding for tpr/fpr values."""
                
        d1 = InferenceDatum(0.8+1e-10, 0.1+1e-12)
        d2 = InferenceDatum(0.8+1e-10, 0.1+1e-12)
        d2.set_annotation("moredata", 0.1+1e-12)
        chain = InferenceChain(0.2+1e-10);
        chain.add(d1).add(d2)
        result = json.loads(chain.to_json())
        # low-level values are not rounded
        self.assertGreater(result["prior"], 0.2)
        # datum objects are rounded
        self.assertEqual(result["data"][0]["tpr"], 0.8)
        self.assertEqual(result["data"][1]["moredata"], 0.1)

