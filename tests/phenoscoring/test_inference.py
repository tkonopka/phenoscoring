"""
Tests for contents of scoring/inference.py
"""


import unittest
from obo.obo import MinimalObo
from phenoscoring.phenoscoring import Phenoscoring
from phenoscoring.dbhelpers import get_refsets
from phenoscoring.dbhelpers import get_ref_priors
from scoring.referenceset import ReferenceSet
from scoring.representation import Representation
from tools.files import check_file
from ..testhelpers import remove_db
from ..testhelpers import CompleteTestConfig


class InferenceTests(unittest.TestCase):
    """Test inference prob calculations after phenoscoring build."""
    
    @classmethod
    def setUpClass(cls):
        """For setup, ensure db does not exist."""
                        
        config = CompleteTestConfig()
        config.null_prior = 0.2
        cls.dbfile = config.db        
        cls.pipeline = Phenoscoring(config)
        cls.pipeline.build()
        obopath = check_file(config.obo, config.db, "obo")
        cls.obo = MinimalObo(obopath, True)
        
        # a dummy set of default values
        cls.obodefaults = dict.fromkeys(cls.obo.ids(), 0.2)
        cls.obozeros = dict.fromkeys(cls.obo.ids(), 0)
        
        cls.ref_priors = get_ref_priors(config.db)
        cls.rs, cls.rs2 = get_refsets(config.db, ref_priors=cls.ref_priors)
        cls.rs.learn_obo(cls.obo)
        cls.rs2.learn_obo(cls.obo)
        
        # for testing individual configurations
        cls.y3model = Representation(name="Y3").set("Y:003", 0.8)        
        cls.refA = Representation(name="refA").set("Y:002", 1)
        cls.refA.defaults(cls.obozeros)
        cls.refB = Representation(name="refB").set("Y:002", 1)
        cls.refB.defaults(cls.obozeros)
    
    @classmethod
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""

        remove_db(cls.dbfile)                

    def test_checkprep(self):
        """inference only works when set is prepped"""  
                                        
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=self.obo.ids())
        with self.assertRaises(Exception):
            rs.inferenceModel(self.y3model)     

    def test_baddata(self):
        """inference should raise when input is bad"""  
        
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=["a", "b", "c"])
        rs.prep()        
        with self.assertRaises(Exception) as e:
            rs.inference(5)

    def test_between2(self):
        """inference when model equally similar to two refs"""  
        
        # let ref universe have two annotations
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=self.obo.ids(),
                          row_priors=self.obodefaults)
        rs.add(self.refA).add(self.refB)
        rs.learn_obo(self.obo)
        rs.prep()
        
        inf = rs.inference(self.y3model)
        self.assertAlmostEqual(inf["refA"], inf["refB"], msg="equally likely")        

    def test_between_refs_and_null(self):
        """inference when model is similar to two refs and a there is a null"""  
        
        # let ref universe have two annotations and one null
        rs = ReferenceSet(dict(null=0.8, refA=0.15, refB=0.15), 
                          ids=self.obo.ids(), row_priors=self.obodefaults)
        rs.add(self.refA).add(self.refB)        
        rs.learn_obo(self.obo)
        rs.prep()
        
        inf = rs.inference(self.y3model)            
        self.assertAlmostEqual(inf["refA"], inf["refB"], 
                               msg="equally likely")

    def test_model_nodata(self):
        """inference when references are unequal but model has no data"""  
        
        model = Representation(name="nodata")
        # let ref universe have two annotations and one null
        rs = ReferenceSet(dict(null=0.8, refA=0.1, refB=0.1), 
                          ids=self.obo.ids(), row_priors=self.obodefaults)
        rs.add(self.refA).add(self.refB)
        rs.learn_obo(self.obo)
        rs.prep()
        
        inf = rs.inference(model)             
        self.assertAlmostEqual(inf["refA"], inf["refB"], 
                               msg="equally likely")

    def test_difference_in_priors(self):
        """inference when model matches two references, 
        but have different priors"""  
        
        # let ref universe have two annotations and one null
        rs = ReferenceSet(dict(null=0.85, refA=0.05, refB=0.1), 
                          ids=self.obo.ids(), row_priors=self.obodefaults)
        rs.add(self.refA).add(self.refB)
        rs.learn_obo(self.obo)
        rs.prep()
        
        inf = rs.inference(self.y3model)             
        self.assertLess(inf["refA"], inf["refB"], 
                        msg="equal match, but A has weaker prior")

    def test_underflow(self):
        """attempt to get underflow in individual p."""  
        
        # let model have very sure values
        model = Representation(name="underflow")
        model.set("Y:007", 0.00001).set("Y:004", 1).set("Y:003", 1)
        # let ref universe have two annotations and one null
        refA = Representation(name="refA").set("Y:003", 1)        
        refB = Representation(name="refB").set("Y:003", 1)        
        rs = ReferenceSet(dict(null=0.98, refA=0.001, refB=0.001), 
                          ids=self.obo.ids())
        rs.add(refA).add(refB)
        rs.learn_obo(self.obo)
        rs.prep()        
                
        result = rs.inference(model, verbose=True)                 
        self.assertGreaterEqual(result["refA"], 0, 
                        msg="must always be a number, even if zero")        
        self.assertGreaterEqual(result["refB"], 0, 
                        msg="must always be a number, even if zero")
        self.assertGreaterEqual(result["refB"], 0, 
                        msg="must always be a number, even if zero")        

    def test_model_rootonly(self):
        """score a vague model."""  
                
        rr = Representation(name="vague").set("Y:004", 0.8)             
        inf = self.rs.inference(rr)
        
        self.assertAlmostEqual(inf["DISEASE:1"], inf["DISEASE:2"], 
                               "most diseases about the same")

    def test_specific_term(self):
        """score a specific model."""  

        rr = Representation(name="specific").set("Y:002", 0.99)    
        inf = self.rs.inference(rr)
        # Disease 3 has Y:007, so should be most likely among diseases
        self.assertGreater(inf["DISEASE:3"], self.ref_priors["DISEASE:3"], 
                           "D:3 has Y:7 so should increase")        
        self.assertGreater(inf["DISEASE:3"], inf["DISEASE:1"], 
                           "D:3 should become most likely")                                 
        self.assertGreater(inf["DISEASE:3"], inf["DISEASE:2"], 
                           "D:3 should become most likely")                         

    def test_refset2(self):
        """check averaging of values."""  
        
        self.assertEqual(self.rs.get("Y:004", "DISEASE:1"), 1, 
                        "raw value should be 1")        
        self.assertLess(self.rs2.get("Y:004", "DISEASE:1"), 0.9, 
                        "averaging decreases value")

    def test_refset2_inference(self):
        """inference based on specific should be smaller than on general."""
        
        rr = Representation(name="custom").set("Y:001", 0.8) 
        inf_general = self.rs.inference(rr)
        inf_specific = self.rs2.inference(rr)
        # Y:001 is shared by DISEASE:1 and DISEASE:2, so specific inf down
        self.assertLess(inf_specific["DISEASE:1"], inf_general["DISEASE:1"])

    def test_specific_term_FP_increases(self):
        """score a specific model, vaguely similar disease should increase."""  
        
        rr = Representation(name="specific").set("Y:008", 0.8)
        inf = self.rs.inference(rr)        
        
        self.assertGreater(inf["DISEASE:3"], inf["DISEASE:1"], 
                           "D3 has Y2, which is close to Y1")

