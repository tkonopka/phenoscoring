'''Tests for extracting details of scoring calculations.

@author: Tomasz Konopka
'''

import json
import unittest
from phenoscoring.phenoscoring import Phenoscoring 
from tools.files import check_file
from ..testhelpers import remove_db
from ..testhelpers import MGITestConfig


class PhenocomputeExplainTests(unittest.TestCase):
    """Test cases for explaining score calculations"""
    
    @classmethod  
    def setUpClass(cls):
        """create a new db with some model and references definitions."""
        
        config = MGITestConfig()
        config.action = "build"                      
        cls.dbfile = config.db
        config.obo = check_file(config.obo, config.db)
        # build a new database
        cls.pipeline = Phenoscoring(config)        
        cls.pipeline.build()
        # add model and definitions (don't compute scores)
        desc_file = check_file(config.model_descriptions, config.db)                                        
        phen_file = check_file(config.model_phenotypes, config.db)                                                   
        cls.pipeline._update(desc_file, phen_file)        

    @classmethod      
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""

        remove_db(cls.dbfile)                
    
    def test_explain_nonexistent(self):
        """get details of general score calculation (nonexistent model)"""
        
        # set the pipeline to explain
        self.pipeline.config.explain = "general"
        self.pipeline.config.model = "GA:100"
        self.pipeline.config.reference = "DISEASE:3"
        result = self.pipeline.explain()               
        result_data = json.loads(result)
        
        self.assertEqual(len(result_data), 1, "one model")
        # content of output should reproduce inputs
        data = result_data[0]
        self.assertEqual(data["reference"], "DISEASE:3")
        self.assertEqual(data["model"], "GA:100")
        self.assertGreater(data["prior"], 0)
        self.assertEqual(len(data["data"]), 0,
                         "nonexistent model has no phenotypes to score")
    
    def test_explain_general(self):
        """get details of general score calculation"""
                
        # set the pipeline to explain
        self.pipeline.config.explain = "general"
        self.pipeline.config.model = "MGI_MA:001_hom"
        self.pipeline.config.reference = "DISEASE:3"
        result = self.pipeline.explain()            
        result_data = json.loads(result)
        
        self.assertEqual(len(result_data), 1, "one model")
        data = result_data[0]
        self.assertEqual(data["reference"], "DISEASE:3")
        self.assertEqual(data["model"], "MGI_MA:001_hom")
        self.assertGreater(data["prior"], 0)
        self.assertGreater(len(data["data"]), 0, 
                           "model has phenotypes to score")        
        self.assertGreater(data["posterior"], data["prior"],
                           "this model should increase score with D:3")
    
    def test_explain_specific(self):
        """get details based on specific scores."""

        self.pipeline.config.explain = "specific"
        self.pipeline.config.model = "MGI_MA:001_hom"
        self.pipeline.config.reference = "DISEASE:3"
        result = self.pipeline.explain()            
        result_data = json.loads(result)
        
        self.assertEqual(len(result_data), 1, "one model")

    def test_explain_other(self):
        """get details based on specific scores."""
        
        self.pipeline.config.explain = "other"
        self.pipeline.config.model = "MGI_MA:001_hom"
        self.pipeline.config.reference = "DISEASE:3"                
        result = self.pipeline.explain()
        self.assertTrue("must be" in result)            

    def test_explain_multiple(self):
        """get details based on specific scores."""
        
        self.pipeline.config.explain = "general"
        self.pipeline.config.model = "MGI_MA:001_hom,MGI_MA:001_hom"
        self.pipeline.config.reference = "DISEASE:3,DISEASE:2"                        
        result = self.pipeline.explain()
        self.assertTrue("DISEASE:3" in result)
        self.assertTrue("DISEASE:2" in result)
    
    def test_explain_mismatched_models_refs(self):
        """get details based on specific scores."""
        
        self.pipeline.config.explain = "general"
        self.pipeline.config.model = "MGI_MA:001_hom,MGI_MA:002_hom"
        self.pipeline.config.reference = "DISEASE:3"                
        with self.assertRaises(Exception):
            result = self.pipeline.explain()

