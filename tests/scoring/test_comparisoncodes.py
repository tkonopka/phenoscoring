'''Tests for contents of scoring/comparisoncodes.py

@author: Tomasz Konopka
'''

import unittest
from scoring.comparisoncodes import ComparisonCodes
from scoring.comparisoncodes import comparison_code

class ComparisonCodesTests(unittest.TestCase):
    """Test codes for TP, FP, etc.."""
        
    def test_str(self):
        """rounding for tpr/fpr values."""
                
        # some traditional codes for true positives, etc
        code_TP = ComparisonCodes.TP
        self.assertEqual(str(code_TP), "TP")
        code_FP = ComparisonCodes.FP
        self.assertEqual(str(code_FP), "FP")
        
        # some additional codes
        code_EP = ComparisonCodes.EP
        self.assertEqual(str(code_EP), "EP")
        code_AN = ComparisonCodes.AN
        self.assertEqual(str(code_AN), "AN")
        
    def test_get_code_TP(self):
        """both model and ref are above background."""        
                                    
        result = comparison_code(0.8, 0.8, 0.1)
        self.assertEqual(result, ComparisonCodes.TP)
                
    def test_get_code_TN(self):
        """both model and ref are below background."""        
                                    
        result = comparison_code(0.01, 0.04, 0.1)
        self.assertEqual(result, ComparisonCodes.TN)
            
    def test_get_code_FP(self):
        """model is positive, but not ref"""        
                                    
        result = comparison_code(0.6, 0.02, 0.1)
        self.assertEqual(result, ComparisonCodes.FP)
        
    def test_get_code_FN(self):
        """model is negative, but not ref"""        
                                    
        result = comparison_code(0.06, 0.2, 0.1)
        self.assertEqual(result, ComparisonCodes.FN)
    
    def test_get_code_EP(self):
        """reference is positive, no data in model"""        
                                    
        result = comparison_code(0.1, 0.6, 0.1)
        self.assertEqual(result, ComparisonCodes.EP)
    
    def test_get_code_EN(self):
        """reference is negative, no other data"""        
                                    
        result = comparison_code(0.1, 0.001, 0.1)
        self.assertEqual(result, ComparisonCodes.EN)
    
    def test_get_code_AN(self):
        """model is positive, no other data"""        
                                    
        result = comparison_code(0.001, 0.1, 0.1)
        self.assertEqual(result, ComparisonCodes.AN)
    
    def test_get_code_AP(self):
        """model is positive, no other data"""        
                                    
        result = comparison_code(0.6, 0.1, 0.1)
        self.assertEqual(result, ComparisonCodes.AP)
        
    def test_get_code_U(self):
        """no information, gives U"""        
                                    
        result = comparison_code(0.1, 0.1, 0.1)
        self.assertEqual(result, ComparisonCodes.U)
    

