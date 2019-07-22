'''Tests for creating database structure and populating data on references.

@author: Tomasz Konopka
'''

import unittest
from os.path import abspath, join
from db.generator import DBGenerator
from phenoscoring.build import get_reference_neighbors
from phenoscoring.phenoscoring import Phenoscoring 
from phenoscoring.dbhelpers import get_refsets
from phenoscoring.dbhelpers import get_ref_priors, get_phenotype_priors
from phenoscoring.dbtables import ReferenceConcisePhenotypeTable
from phenoscoring.dbtables import ReferenceCompletePhenotypeTable
from phenoscoring.dbtables import ModelDescriptionTable
from ..testhelpers import remove_db
from ..testhelpers import CompleteTestConfig


class BuildTests(unittest.TestCase):
    """Test cases for building a phenoscoring db."""

    @classmethod      
    def setUpClass(cls):
        """For setup, ensure db does not exist."""                
        cls.config = CompleteTestConfig()            
        cls.dbfile = cls.config.db
        remove_db(cls.dbfile)
        pipeline = Phenoscoring(cls.config)        
        pipeline.build()
    
    @classmethod  
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""            
        remove_db(cls.dbfile)               

    def test_dbpath(self):
        """assemble full path to phenoscoring db. """
                        
        expected = join("tests", "testdata", "phenoscoring-testdata.sqlite")        
        self.assertEqual(abspath(self.dbfile), abspath(expected), 
                         "phenoscoring db file is inside db dir")

    def test_build_references(self):
        """can build and populate tables with reference phenotypes.""" 
                            
        concise = ReferenceConcisePhenotypeTable(self.dbfile)                    
        self.assertEqual(concise.count_rows(), 11)                          
        complete = ReferenceCompletePhenotypeTable(self.dbfile)
        self.assertGreater(complete.count_rows(), 11)

    def test_complete_references_number_phens(self):
        """complete phenotype table has all entries for the null model"""
                            
        phen_priors = get_phenotype_priors(self.dbfile)
        nullphen = set()
        D1phen = set()
        generator = DBGenerator(ReferenceCompletePhenotypeTable(self.dbfile))
        for row in generator.next():
            if row["id"] == "null":
                nullphen.add(row["phenotype"])
            if row["id"] == "DISEASE:1":
                D1phen.add(row["phenotype"])
        # null should have all phens
        self.assertEqual(len(nullphen), len(phen_priors))
        # disease phenotypes can omit some
        self.assertLessEqual(len(D1phen), len(phen_priors))

    def test_build_priors(self):
        """reference priors table is filled"""
        
        reftab = ReferenceCompletePhenotypeTable(self.dbfile)
        self.assertGreater(reftab.count_rows(), 2, "ref table is non-empty")

    def test_priors_values(self):        
        """reference priors are set and reasonable."""
        
        priors = get_ref_priors(self.dbfile)
        
        # there are four references in test dataset.
        # their priors should be 0.01 as per configuration
        self.assertAlmostEqual(priors["DISEASE:1"], 0.01)
        self.assertAlmostEqual(priors["DISEASE:2"], 0.01)        
        self.assertAlmostEqual(priors["DISEASE:3"], 0.01)
        self.assertAlmostEqual(priors["DISEASE:4"], 0.01)
        
        self.assertAlmostEqual(priors["null"], 0.96, "null prior is dependent on diseases")

    def test_priors_targeted(self):
        """can retrieve a small number of reference priors."""
        
        # retrieve targeted priors
        priors = get_ref_priors(self.dbfile, set(["DISEASE:1", "DISEASE:2"]))
        # priors should have only information on a small number of diseases
        self.assertEqual(len(priors), 2)
        self.assertEqual(sorted(list(priors.keys())), ["DISEASE:1", "DISEASE:2"])

    def test_reference_set_null(self):
        """can build reference set with null model with proper probabilities"""
                         
        priors = get_ref_priors(self.dbfile)
        phen_priors = get_phenotype_priors(self.dbfile)
        rs, _ = get_refsets(self.dbfile, priors)
        
        self.assertGreater(rs.get("Y:001", "null"), 0, 
                           "null model has some prob")
        self.assertLess(rs.get("Y:001", "null"), phen_priors["Y:001"], 
                        "null model has less prob than prior")
        missing_factor = self.config.reference_missing_factor
        self.assertAlmostEqual(rs.get("Y:001", "null"), 
                               phen_priors["Y:001"]*missing_factor, 
                               msg="null model has prob determined by missing_factor")
        self.assertAlmostEqual(rs.get("Y:004", "null"), 
                               phen_priors["Y:004"]*missing_factor, 
                               msg="another phenotype")

    def test_reference_set_general(self):
        """can build reference_set with disease profiles reference sets"""
                                     
        rs, _ = get_refsets(self.dbfile)
        priors = get_phenotype_priors(self.dbfile)
        
        # null should by proportional to priors by a factor
        self.assertAlmostEqual(rs.get("Y:001", "null"), priors["Y:001"]/2)
        self.assertAlmostEqual(rs.get("Y:002", "null"), priors["Y:002"]/2)              
        self.assertAlmostEqual(rs.get("Y:004", "null"), priors["Y:004"]/2)
        self.assertAlmostEqual(rs.get("Y:007", "null"), priors["Y:007"]/2)
        
        # DISEASE:1
        self.assertGreater(rs.get("Y:002", "DISEASE:1"), 0.5, 
                         "D:1 has X:001, which implies Y:002 via oomap")                        
        self.assertGreater(rs.get("Y:004", "DISEASE:1"), 0.5, 
                         "D:1 has X:001, which implies Y:004 via ontology")
        # DISEASE:4
        self.assertGreater(rs.get("Y:001", "DISEASE:4"), 0.1, 
                         msg="D:4 has X:003, which implies Y:001 via oomap")                        
        self.assertGreater(rs.get("Y:004", "DISEASE:4"), 0.1, 
                         msg="D:4 has X:003, which implies Y:001 and Y:002, root gets more")                
        self.assertLess(rs.get("Y:004", "DISEASE:4"), 0.9, 
                         msg="D:4 has weak evidence, should not get top marks") 

    def test_reference_set_specific(self):
        """can build reference_set with specific phenotypes"""
                                     
        gen, spec = get_refsets(self.dbfile)
        priors = get_phenotype_priors(self.dbfile)
                
        # null should be equal to prior in specific representation
        self.assertAlmostEqual(spec.get("Y:001", "null"), priors["Y:001"])              
        self.assertAlmostEqual(spec.get("Y:002", "null"), priors["Y:002"]) 
        self.assertAlmostEqual(spec.get("Y:003", "null"), priors["Y:003"])
        self.assertAlmostEqual(spec.get("Y:007", "null"), priors["Y:007"])


class BuildNeighborsTests(unittest.TestCase):
    """Test cases for identifying nearest neighbors of diseases."""

    @classmethod
    def setUpClass(cls):
        """For setup, ensure db does not exist."""
        cls.config = CompleteTestConfig()
        cls.dbfile = cls.config.db
        cls.k = cls.config.reference_neighbors_k
        remove_db(cls.dbfile)
        pipeline = Phenoscoring(cls.config)
        pipeline.build()
        cls.neighbors = get_reference_neighbors(cls.dbfile, cls.k)

    @classmethod
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""
        remove_db(cls.dbfile)

    def test_neighbors_structure(self):
        """structure of database table with neighbors"""

        neighbors = self.neighbors
        self.assertEqual(len(neighbors), 4, "four diseases in test set")
        self.assertEqual(len(neighbors["DISEASE:1"]), self.k)

    def test_neighbors_similar_diseases(self):
        """Similar diseases should be neighbors"""

        neighbors = self.neighbors
        self.assertEqual(neighbors["DISEASE:1"][0], "DISEASE:2")
        self.assertEqual(neighbors["DISEASE:2"][0], "DISEASE:1")

    def test_neighbors_close_to_null(self):
        """Diseases with few phenotypes should be neighbors to null"""

        neighbors = self.neighbors
        self.assertEqual(neighbors["DISEASE:4"][0], "null")


class AvoidBuildTests(unittest.TestCase):
    """Test cases for avoiding resetting phenoscoring db."""
    
    def setUp(self):
        """For setup, ensure db does not exist."""                
        self.config = CompleteTestConfig()            
        self.dbfile = self.config.db
        remove_db(self.dbfile)
        pipeline = Phenoscoring(CompleteTestConfig())        
        pipeline.build()        
        # add something into the db
        self.desctab = ModelDescriptionTable(self.dbfile)
        self.desctab.add(id="a", category="test")
        self.desctab.save()        

    def tearDown(self):
        """At end, ensure test db is deleted."""            
        remove_db(self.dbfile)               

    def test_can_avoid_rebuild(self):
        """stops processing if build() called a second time."""
        
        # make sure to start the db has something         
        self.assertGreater(self.desctab.count_rows(), 0)
        # attempt rebuild
        config = CompleteTestConfig()
        config.reset = False
        pipeline = Phenoscoring(config)
        pipeline.build()                
        # the tables should still be non-empty
        self.assertGreater(self.desctab.count_rows(), 0)

    def test_reset_build(self):
        """stops processing if build() called a second time."""
        
        # make sure to start the db has something         
        self.assertGreater(self.desctab.count_rows(), 0)
        # rebuild
        config = CompleteTestConfig()
        config.reset = True
        pipeline = Phenoscoring(config)
        pipeline.build()                
        # the tables should now be cleared in the build
        self.assertEqual(self.desctab.count_rows(), 0)

