'''
Tests for contents of phenoscoring/compute.py - computing model scores
'''


import unittest
from collections import Counter
from db.generator import DBGenerator
from phenoscoring.phenoscoring import Phenoscoring 
from phenoscoring.dbhelpers import get_model_names, get_ref_names
from phenoscoring.compute import prep_compute_packets
from tools.files import check_file
from phenoscoring.dbtables import ModelScoreTable
from ..testhelpers import remove_db
from ..testhelpers import IMPCTestConfig


class PhenoscoringComputeTests(unittest.TestCase):
    """Test cases for computing scores based on a phenoscoring db."""    
        
    @classmethod
    def setUpClass(cls):        
        """create a new db with model definitions"""
                        
        cls.config = config = IMPCTestConfig()
        cls.dbfile = dbfile = cls.config.db        
        remove_db(cls.dbfile)         
        config.scale_oo_scores = False                           
        config.obo = check_file(config.obo, dbfile)
        cls.desc_file = check_file(config.model_descriptions, dbfile)
        cls.phen_file = check_file(config.model_phenotypes, dbfile)
        # build a db
        cls.pipeline = Phenoscoring(config)        
        cls.pipeline.build()
        # add some model definitions (don't compute)
        cls.pipeline._update(cls.desc_file, cls.phen_file)
        cls.refnames = get_ref_names(cls.dbfile)
    
    @classmethod
    def tearDownClass(cls):
        """ensure test db is deleted."""

        remove_db(cls.dbfile)                

    def setUp(self):        
        """upon setup clear scores for all models"""
        
        ModelScoreTable(self.dbfile).empty()        

    def test_partitioning_large(self):
        """split model ids into groups/packets"""
        
        modelnames = get_model_names(self.dbfile)        
        
        # partition allowing a large partition_size        
        self.config.partition_size=1024
        packets = prep_compute_packets(self.config, 
                                       references=self.refnames, 
                                       models=modelnames)
        
        # in this example: partition_size is large and the data set is small
        self.assertEqual(len(packets), 1, 
                         "large partition should accommodate all data")
        self.assertEqual(len(packets[0].references), len(self.refnames),
                         "first packet should include all references")
        self.assertEqual(len(packets[0].models), len(modelnames),
                         "first packet should include all models")

    def test_paritioning_empty(self):
        """partitioning works with empty input."""
                
        packetsA = prep_compute_packets(self.config, 
                                        references=[], 
                                        models=["a", "b"])
        packetsB = prep_compute_packets(self.config, 
                                        references=["a"], 
                                        models=[])        
        self.assertEqual(packetsA, [])
        self.assertEqual(packetsB, [])        

    def test_paritioning_None(self):
        """partitioning works when one of the inputs is None."""
                
        packetsA = prep_compute_packets(self.config, 
                                        references=None, 
                                        models=["a", "b"])
        packetsB = prep_compute_packets(self.config, 
                                        references=["a"], 
                                        models=None)        
        self.assertEqual(packetsA, [])
        self.assertEqual(packetsB, [])
    
    def test_paritioning_small(self):
        """split computation into small partitions"""
        
        modelnames = get_model_names(self.dbfile)        
        
        # partition into small bits
        self.config.partition_size=2
        packets = prep_compute_packets(self.config, 
                                       references=self.refnames, 
                                       models=modelnames)
        
        self.assertGreater(len(packets), 2, 
                          "small partition means split over many packets")                 
        # each packet should have at most 2 references and at most 2 models
        for z in range(len(packets)):
            self.assertLessEqual(len(packets[z].references), 2)
            self.assertLessEqual(len(packets[z].models), 2)
        
        # check that all combinations are covered in at most one packet
        result, expected = Counter(), Counter()        
        for m in modelnames:
            for r in self.refnames:
                expected.update([m+"_"+r])
        for packet in packets:
            for m in packet.models:
                for r in packet.references:                
                    result.update([m+"_"+r])        
        self.assertEqual(result, expected)
        numrefs = len(self.refnames)
        self.assertEqual(len(result), len(modelnames)*numrefs)
        self.assertEqual(sum(result.values()), len(modelnames)*numrefs)
    
    def test_paritioning_large(self):
        """split computation into large partitions"""
        
        modelnames = get_model_names(self.dbfile)        
        
        # partition into small bits
        self.config.partition_size=1024
        packets = prep_compute_packets(self.config, 
                                       references=self.refnames, 
                                       models=modelnames)
        
        self.assertEqual(len(packets), 1, 
                          "large partition means everything fits into one")                 
        self.assertEqual(len(packets[0].references), len(self.refnames))
        self.assertEqual(len(packets[0].models), len(modelnames))

    def test_compute_scores(self):
        """perform packet calculations."""
        
        modelnames = ["MGI_MA:001_hom", "MGI_MA:001_het"]
        refnames = ["DISEASE:1", "DISEASE:3"]
        packets = prep_compute_packets(self.config, 
                                       references=refnames, 
                                       models=modelnames)
        self.assertEqual(len(packets), 1, "one packet only")
        packets[0].run()
        
        scoretab = ModelScoreTable(self.dbfile)
        numscores = scoretab.count_rows()
        self.assertEqual(numscores, 4)

    def test_compute_clear(self):
        """compute clears up objects after run"""
        
        modelnames = ["MGI_MA:001_hom", "MGI_MA:001_het"]
        refnames = ["DISEASE:1", "DISEASE:3"]
        packets = prep_compute_packets(self.config, 
                                       references=refnames, 
                                       models=modelnames)
        self.assertEqual(len(packets), 1, "one packet only")
        # packet defines references and models
        self.assertNotEqual(packets[0].references, set())
        self.assertNotEqual(packets[0].models, dict())
        packets[0].run()
        # after run, the packet should be clear
        self.assertEqual(packets[0].general_refset, None)
        self.assertEqual(packets[0].specific_refset, None)
        self.assertEqual(packets[0].references, set())
    
    def test_compute_gives_stamps(self):
        """perform packet calculations."""
        
        modelnames = ["MGI_MA:001_hom", "MGI_MA:001_het"]
        refnames = ["DISEASE:1", "DISEASE:3"]
        packets = prep_compute_packets(self.config, 
                                       references=refnames, 
                                       models=modelnames)        
        packets[0].run()
        
        generator = DBGenerator(ModelScoreTable(self.dbfile))
        stamps = []
        for row in generator.next():
            stamps.append(row["timestamp"])
        self.assertFalse(stamps[0] is None)
        self.assertFalse(stamps[1] is None)         


class PhenoscoringRecomputeTests(unittest.TestCase):
    """Test cases for computing scores based on a phenoscoring db."""    

    @classmethod
    def setUpClass(cls):        
        """create a new db with model definitions"""
                        
        cls.config = config = IMPCTestConfig()
        cls.dbfile = dbfile = cls.config.db        
        remove_db(cls.dbfile)         
        config.scale_oo_scores = False                           
        config.obo = check_file(config.obo, dbfile)
        cls.desc_file = check_file(config.model_descriptions, dbfile)
        cls.phen_file = check_file(config.model_phenotypes, dbfile)
        # build a db
        cls.pipeline = Phenoscoring(config)        
        cls.pipeline.build()
        # add some model definitions (don't compute)
        cls.pipeline.update()        
    
    @classmethod
    def tearDownClass(cls):
        """ensure test db is deleted."""

        remove_db(cls.dbfile)
    
    def test_recompute(self):
        """recompute drops scores and recreates them."""
        
        generator_before = DBGenerator(ModelScoreTable(self.dbfile))
        before = []
        for row in generator_before.next():
            before.append(row)
        self.assertGreater(len(before), 0, 
                           "db should be set up with some scores")
                
        # recomputing should drop the scores and recreate them 
        self.pipeline.recompute()
                
        generator_after = DBGenerator(ModelScoreTable(self.dbfile))
        after = []
        for row in generator_after.next():
            after.append(row)                        
        self.assertEqual(len(before), len(after),
                         "recomputing should give same result structure")
        # technically, the timestamps would be different,
        # but the default timestamp format does not capture milliseconds 