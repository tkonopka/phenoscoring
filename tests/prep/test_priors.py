'''
Tests for contents of phenoprep/priors.py
'''

import unittest
from os.path import join, exists
from obo.obo import MinimalObo
from phenoprep.prep_mgi import prep_MGI
from phenoprep.priors import get_priors_from_models
from phenoprep.priors import get_priors_from_reps
from phenoprep.write import write_priors
from scoring.representation import Representation
from tools.files import open_file
from ..testhelpers import remove_if_exists


testdir = join("tests", "testdata")

mgi_file = join(testdir, "MGI-GP-small.rpt")
out_prefix = join(testdir, "test-prep-MGI")
priors_file = out_prefix + "-priors.tsv.gz"

# standard ontology
obo_file = join(testdir, "Y.obo")        
obo = MinimalObo(obo_file)

# extended ontologies with intermediate terms
ext1_obo_file = join(testdir, "Y.ext1.obo")
ext1_obo = MinimalObo(ext1_obo_file)
ext2_obo_file = join(testdir, "Y.ext2.obo")
ext2_obo = MinimalObo(ext2_obo_file)


class PriorsTests(unittest.TestCase):
    """Test cases for obtaining prior probabilities for phenotypes"""        
        
    def setUp(self):
        self.models = prep_MGI(mgi_file, (0.8, 0.05), obo)
             
    def tearDown(self):
        remove_if_exists(priors_file)
        pass
        
    def test_priors_models(self):
        """generate priors for phenotypes from models"""
        
        priors, num = get_priors_from_models(self.models, set(["genotype"]), 
                                             obo)

        # should use several models to inform the prior
        self.assertGreater(num, 0)
        
        # root should have a higher prior than child nodes
        self.assertGreater(priors["Y:004"], priors["Y:001"])
        self.assertGreater(priors["Y:003"], priors["Y:001"])
        # used phenotypes should be higher than unused items in ontology
        self.assertGreater(priors["Y:002"], priors["Y:007"])
        self.assertGreater(priors["Y:002"], priors["Y:008"])
        # unused phenotypes should all be equal
        self.assertEqual(priors["Y:007"], priors["Y:008"])

    def test_priors_models_dark(self):
        """generate priors for phenotypes from models using higher dark count"""
        
        # get priors for dark count=1,2
        priors1, _ = get_priors_from_models(self.models, set(["genotype"]), 
                                            obo, dark=1)
        priors2, _ = get_priors_from_models(self.models, set(["genotype"]), 
                                            obo, dark=2)
        
        # unused phenotypes should have higher priors with dark2        
        self.assertGreater(priors2["Y:007"], priors1["Y:007"])
        self.assertGreater(priors2["Y:008"], priors1["Y:008"])

    def test_priors_reps(self):
        """generate priors for phenotypes from representations."""
       
        repA = Representation(name="A")
        repA.set("Y:006", 1)
        repB = Representation(name="B")
        repB.set("Y:001", 0.8)
        
        reps = dict(A=repA, B=repB)
        priors, num = get_priors_from_reps(reps, obo)
        self.assertGreater(num, 0)
        
    def test_signal_nonmatching_models(self):
        """check that input file exists"""
        
        priors, num = get_priors_from_models(self.models, set(["abc"]), obo)        
        self.assertEqual(num, 0, "none of the MGI models have category 'abc'")
    
    def test_writing(self):
        """check output is a two column tsv"""
        
        priors, num = get_priors_from_models(self.models, set(["genotype"]), 
                                             obo, dark=1)
        write_priors(priors, out_prefix)
        
        self.assertTrue(exists(priors_file))
        with open_file(priors_file, "rt") as f:
            data = f.read().strip().split("\n")
        self.assertEqual(len(data), 1+len(obo.ids()))
        self.assertEqual(len(data[0].split("\t")), 2)
    
    def test_ext1_obo(self):
        """adding intermediate terms should not change empirical priors.
        
        This test uses ext1_obo, which extends the ontology in a branch that
        is unused by the test models. 
        """
                        
        models = self.models
        sg = set(["genotype"])        
        priors, _ = get_priors_from_models(models, sg, obo)
        ext1_priors, _ = get_priors_from_models(models, sg, ext1_obo)
        
        for id in obo.ids():
            self.assertEqual(priors[id], ext1_priors[id],
                             "all phenotypes should have same priors")            
                    
    def test_ext2_obo(self):
        """adding intermediate terms should not change empirical priors.
        
        This test uses ext2_obo, which extends the ontology in intermediate 
        terms that are actually used by the test models.  
        """
                        
        models = self.models
        sg = set(["genotype"])        
        priors, _ = get_priors_from_models(models, sg, obo)
        ext2_priors, _ = get_priors_from_models(models, sg, ext2_obo)
        
        for id in obo.ids():
            self.assertEqual(priors[id], ext2_priors[id],
                             "all phenotypes should have same priors")            
    
