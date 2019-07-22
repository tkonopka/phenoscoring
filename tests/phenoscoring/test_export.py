'''Tests for phenoscoring/phenoscoring.py with action export

Writing content of db tables to tsv files

@author: Tomasz Konopka
'''

import unittest
from os.path import exists
from io import StringIO
from phenoscoring.phenoscoring import Phenoscoring 
from phenoscoring.dbtables import ModelDescriptionTable
from phenoscoring.dbtables import ReferenceConcisePhenotypeTable
from ..testhelpers import remove_db, remove_dbaux
from ..testhelpers import MGITestConfig


class ExportTests(unittest.TestCase):
    """Test cases for exporting tables from a db"""

    @classmethod
    def setUpClass(cls):
        """For setup, ensure db does not exist"""        
        cls.config = config = MGITestConfig()            
        cls.dbfile = config.db
        remove_db(cls.dbfile)
        cls.pipeline = Phenoscoring(cls.config)        
        cls.pipeline.build()            
        cls.pipeline.update()
    
    @classmethod        
    def tearDownClass(cls):
        """At end, ensure test db is deleted"""            
        remove_db(cls.dbfile)               
            
    def tearDown(self):
        """At end of each test, remove any text files that were exported"""            
        remove_dbaux(self.dbfile)               
    
    def test_build_update(self):
        """the db setup should have references and models"""
            
        reftab = ReferenceConcisePhenotypeTable(self.dbfile)        
        self.assertGreater(reftab.count_rows(), 1)
        modeltab = ModelDescriptionTable(self.dbfile)        
        self.assertGreater(modeltab.count_rows(), 1)                
        
    def test_export(self):
        """export a table with reference priors"""
                        
        config = MGITestConfig()            
        config.table = "reference_priors"        
        
        # export the table
        out = StringIO()            
        pipeline = Phenoscoring(config)
        pipeline.export(out)

        # check some basic properties                
        outvalue = out.getvalue().strip().split("\n")
        self.assertGreater(len(outvalue), 4)        
        self.assertEqual(outvalue[0], "id\tvalue")
    
    def test_export_none(self):
        """do not export anything when a table has not been set"""
                
        out = StringIO()            
        self.pipeline.export(out)                    
        outvalue = out.getvalue().strip()        
        self.assertEqual(outvalue, '')        
    
    def test_export_ref_representations(self):
        """export matrices/json with references."""
        
        self.pipeline.export_representations()
        ref_prefix = self.pipeline.rootpath+"-references"
        
        # check files summarizing references
        self.assertTrue(exists(ref_prefix+"_data.tsv.gz"))
        self.assertTrue(exists(ref_prefix+"_column_priors.json"))
        self.assertTrue(exists(ref_prefix+"_row_priors.json"))

