'''
Tests for phenoscoring/phenoscoring.py and phenoscoring/update.py

Adding and updatnig models to an existing db
'''


import unittest
from db.generator import DBGenerator
from phenoscoring.phenoscoring import Phenoscoring 
from phenoscoring.dbtables import ModelDescriptionTable, ModelPhenotypeTable
from phenoscoring.dbtables import ModelScoreTable
from ..testhelpers import remove_db
from ..testhelpers import CompleteTestConfig, MGITestConfig
from ..testhelpers import IMPCTestConfig


class AddModelsTests(unittest.TestCase):
    """Test cases for adding models to an empty phenoscoring db"""
    
    @classmethod     
    def setUpClass(self):
        """For setup, ensure db does not exist, then build a new one"""
        
        config = CompleteTestConfig()            
        self.dbfile = config.db
        remove_db(self.dbfile)        
        self.pipeline = Phenoscoring(config)
        self.pipeline.build()
    
    @classmethod 
    def tearDownClass(self):
        """At end, ensure test db is deleted."""                
        remove_db(self.dbfile)       
               
    def setUp(self):
        """At beginning of each test, make sure there are no models."""        
        self.pipeline.clearmodels()
        
    def test_build_impc(self):
        """can build a phenoscoring database using only IMPC data"""

        impc = Phenoscoring(IMPCTestConfig())            
        impc.update()
        
        ## in contrast to complete build, this db should have IMPC-only rows        
        desctab = ModelDescriptionTable(self.dbfile)                
        self.assertEqual(desctab.count_rows(), 8)        
        modeltab = ModelPhenotypeTable(self.dbfile)        
        self.assertEqual(modeltab.count_rows(), 14)
        
    def test_build_mgi(self):
        """can build a phenoscoring database using only MGI data"""

        mgi = Phenoscoring(MGITestConfig())                
        mgi.update()
        
        ## in contrast to complete config, this db should have fewer rows
        desctab = ModelDescriptionTable(self.dbfile)                
        self.assertEqual(desctab.count_rows(), 6)
        modeltab = ModelPhenotypeTable(self.dbfile)        
        self.assertEqual(modeltab.count_rows(), 9)

    def test_build_both(self):
        """can update database sequentially with MGI and IMPC"""
        
        mgi = Phenoscoring(MGITestConfig())                
        mgi.update()
        impc = Phenoscoring(IMPCTestConfig())            
        impc.update()
                
        desctab = ModelDescriptionTable(self.dbfile)        
        self.assertEqual(desctab.count_rows(), 14, "8 IMPC, 6 MGI")
        
        modeltab = ModelPhenotypeTable(self.dbfile)        
        self.assertEqual(modeltab.count_rows(), 23, "9 MGI, 14 IMPC")
        
        scoretab = ModelScoreTable(self.dbfile)
        self.assertGreater(scoretab.count_rows(), 0, "score table is non-empty")


class UpdateModelsTests(unittest.TestCase):
    """Test cases for updating a non-empty phenoscoring db with more models"""
    
    @classmethod
    def setUpClass(cls):
        """For setup, ensure db does not exist, then build a new one"""        
        config = CompleteTestConfig()
        cls.dbfile = config.db
        remove_db(cls.dbfile)        
        cls.pipeline = Phenoscoring(config)
        cls.pipeline.build()
    
    @classmethod      
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""                
        remove_db(cls.dbfile)       

    def setUp(self):
        """At beginning of each test, make sure IMPC models are loaded."""        
        self.pipeline.clearmodels()
        impc = Phenoscoring(IMPCTestConfig())            
        impc.update()
        
    def descriptions_contain(self, key, query):
        """scan an descriptions table; check some row[key] contains a query."""
    
        hit = False
        generator = DBGenerator(ModelDescriptionTable(self.dbfile))        
        for row in generator.next():            
            if query in str(row[key]):
                hit = True        
        return hit

    def test_update_nowork(self):
        """can run build repeatedly without over-inserting"""

        ## run update again, but without setting phenotypes
        impc = Phenoscoring(IMPCTestConfig())                        
        impc.model_phenotypes = None        
        impc.update()
                
        desctab = ModelDescriptionTable(self.dbfile)                
        self.assertEqual(desctab.count_rows(), 8, 
                         "number of descriptions should be unchanged")
        
        ## run again without setting anything
        impc.model_descriptions = None        
        impc.update()
        self.assertEqual(desctab.count_rows(), 8, 
                         "number of descriptions should be unchanged")
    
    def test_update_descriptions(self):
        """run update multiple times to change content of model descriptions."""
        
        desctab = ModelDescriptionTable(self.dbfile)
        self.assertEqual(desctab.count_rows(), 8, 
                         "initial set of model descriptions")
        self.assertFalse(self.descriptions_contain("description", "UPDATED"))
        
        ## run an update operation with only model descriptions 
        config = IMPCTestConfig()
        config.model_descriptions = "prep-IMPC-descriptions-update.tsv"
        config.model_phenotypes = None
        impc2 = Phenoscoring(config)
        impc2.update()
        self.assertEqual(desctab.count_rows(), 8, 
                         "number of models should be unchanged")
        self.assertTrue(self.descriptions_contain("description", "UPDATED"),
                        "descriptions in updated file contain string UPDATED")
    
    def test_update_phenotypes_badids(self):
        """update of phenotypes aborts when file contains incorrect ids."""
        
        phentab = ModelPhenotypeTable(self.dbfile)
        self.assertEqual(phentab.count_rows(), 14, "initial phenotypes")
        
        config = IMPCTestConfig()
        config.model_descriptions = None 
        config.model_phenotypes = "prep-IMPC-phenotypes-badids.tsv"      
        impc2 = Phenoscoring(config)
        impc2.update()
        self.assertEqual(phentab.count_rows(), 14, "phenotypes unchanged")
        
    def test_update_phenotypes(self):
        """update of phenotypes adds new phenotypes."""
                                
        # rerun the update, should give twice the number of phenotypes
        impc2 = Phenoscoring(IMPCTestConfig())
        impc2.update()
        phentab = ModelPhenotypeTable(self.dbfile)
        self.assertEqual(phentab.count_rows(), 28, "phenotypes added twice")
    
    def test_update_skip_compute(self):
        """run update but skip score calculation"""
                
        # extract current number of models and scores        
        desctab = ModelDescriptionTable(self.dbfile)
        scorestab = ModelScoreTable(self.dbfile)        
        num_models = desctab.count_rows()
        num_scores = scorestab.count_rows()
        
        # run an update, but without computing scores        
        config = MGITestConfig()
        config.skip_compute = True        
        mgi = Phenoscoring(config)
        mgi.update()
                                        
        self.assertGreater(desctab.count_rows(), num_models, 
                         "number of models should increase")
        self.assertEqual(scorestab.count_rows(), num_scores, 
                         "number of scores should remain")
