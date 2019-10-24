"""
Tests for phenoscoring/phenoscoring.py and phenoscoring/update.py

Adding and updatnig models to an existing db
"""

import unittest
from phenoscoring.phenoscoring import Phenoscoring
from phenoscoring.dbtables import ModelDescriptionTable, ModelPhenotypeTable
from phenoscoring.dbtables import ModelScoreTable
from ..testhelpers import remove_db
from ..testhelpers import CompleteTestConfig, IMPCTestConfig


class RemoveModelsTests(unittest.TestCase):
    """Test cases for updating a non-empty phenoscoring db with more models"""
    
    def setUp(self):
        """For setup, ensure db does not exist, then build a new one"""        
        config = CompleteTestConfig()        
        self.dbfile = config.db
        remove_db(self.dbfile)        
        self.pipeline = Phenoscoring(config)
        self.pipeline.build()
        impc = Phenoscoring(IMPCTestConfig())
        impc.update()
        
        # handles for models
        self.desctab = ModelDescriptionTable(self.dbfile)
        self.phenstab = ModelPhenotypeTable(self.dbfile)
        self.scoretab = ModelScoreTable(self.dbfile)
                
    def tearDown(self):
        """At end, ensure test db is deleted."""                
        remove_db(self.dbfile)       
  
    def test_clear_models(self):
        """can remove all models at once."""
                
        # ensure that db is non empty
        self.assertGreater(self.desctab.count_rows(), 0)                         
        self.assertGreater(self.phenstab.count_rows(), 0)                        
        self.assertGreater(self.scoretab.count_rows(), 0)                        
        
        # attempt to clear everything
        impc = Phenoscoring(IMPCTestConfig())
        impc.clearmodels()        
        self.assertEqual(self.desctab.count_rows(), 0)                         
        self.assertEqual(self.phenstab.count_rows(), 0)                        
        self.assertEqual(self.scoretab.count_rows(), 0)                        
                
    def test_remove_models(self):
        """can remove a partial set of data"""

        # get an initial set of database row counts
        num_desc = self.desctab.count_rows()
        num_phens = self.phenstab.count_rows()
        num_score = self.scoretab.count_rows()
        
        # run a model removal using a small descriptions file
        config = IMPCTestConfig()
        config.model_descriptions = "prep-IMPC-descriptions-update.tsv"
        config.model_phenotypes = None
        impc = Phenoscoring(config)
        impc.remove()
        
        # the number of rows in tables should decrease
        self.assertLess(self.desctab.count_rows(), num_desc,
                        "number of models should decrease")
        self.assertLess(self.phenstab.count_rows(), num_phens,
                        "number of phenotypes should decrease")
        self.assertLess(self.scoretab.count_rows(), num_score,
                        "number of score entries should decrease")

