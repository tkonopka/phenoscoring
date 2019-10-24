"""
Tests for counting hits among model scores
"""

import unittest
from phenoscoring.phenoscoring import Phenoscoring
from phenopost.counthits import count_hits, get_highscore_pairs
from tools.files import check_file
from phenoscoring.dbtables import ModelScoreTable
from ..testhelpers import remove_db
from ..testhelpers import MGITestConfig


class CounthitsTests(unittest.TestCase):
    """Test cases for counting hits in an existing db."""    
    
    @classmethod
    def setUpClass(cls):
        """For setup, ensure db does not exist."""
                
        config = MGITestConfig()        
        config.scale_oo_scores = False                   
        cls.dbfile = config.db
        config.obo = check_file(config.obo, config.db)
        cls.pipeline = Phenoscoring(config)
        cls.pipeline.build() 
        
        # first add some rows to the db by hand
        model = ModelScoreTable(config.db)            
        model.add("model:1", "DISEASE:1", "stamp", 0.95, 0.98)
        model.add("model:2", "DISEASE:1", "stamp", 0.94, 0.96)
        model.add("model:3", "DISEASE:1", "stamp", 0.24, 0.96)
        model.add("model:4", "DISEASE:2", "stamp", 0.92, 0.95)
        model.add("model:5", "DISEASE:2", "stamp", 0.86, 0.85)
        model.add("model:6", "DISEASE:3", "stamp", 0.96, 0.95)
        model.save()
                                                              
    @classmethod          
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""
        remove_db(cls.dbfile)
    
    def test_plain_hits(self):
        """count plain hits"""
                        
        hitcounts = get_highscore_pairs(self.dbfile, 0.9)
        self.assertEqual(len(hitcounts), 4, 
                         "2 hits for D:1 and 1 each D:2 and D:3")
                        
        hits = count_hits(self.dbfile, 0.8)        
        self.assertEqual(len(hits), 5, "4 diseases, 1 null")
        self.assertEqual(hits["DISEASE:1"], (2,2))
        self.assertEqual(hits["DISEASE:2"], (2,2))
        self.assertEqual(hits["DISEASE:3"], (1,1))
        self.assertEqual(hits["DISEASE:4"], (0,0))
        self.assertEqual(hits["null"], (0,0))
        
    def test_stricter_hits(self):
        """count plain hits with higher threshold"""
                        
        hits = count_hits(self.dbfile, 0.9)        
        self.assertEqual(len(hits), 5, "4 diseases, 1 null")
        self.assertEqual(hits["DISEASE:1"], (2,2))
        self.assertEqual(hits["DISEASE:2"], (1,1))
        self.assertEqual(hits["DISEASE:3"], (1,1))
        self.assertEqual(hits["DISEASE:4"], (0,0))
    
    def test_hits_two_thresholds(self):
        """count hits including a margin."""
                        
        hits3 = count_hits(self.dbfile, 0.9, 0.1)        
        self.assertEqual(len(hits3), 5, "4 diseases, 1 null")
        self.assertEqual(hits3["DISEASE:1"], (2,3))
        self.assertEqual(hits3["DISEASE:2"], (1,2))
        self.assertEqual(hits3["DISEASE:3"], (1,1))
        self.assertEqual(hits3["DISEASE:4"], (0,0))

