'''
Tests for contents of phenoprep/prep_refs.py
'''

import unittest
from os.path import join, exists
from phenoprep.prep_refs import prep_refs, get_oo_map, valid_reference_id
from phenoprep.prep_refs import prep_tech_models
from phenoprep.write import write_references
from obo.obo import MinimalObo
from ..testhelpers import remove_if_exists
from tools.files import open_file

testdir = join("tests", "testdata")
refs_file = join(testdir, "phenotab-small.tab")
obo_file = join(testdir, "Y.obo")
oo_file = join(testdir, "owlsim-small.txt")
k = 2
out_prefix = join("tests", "testdata", "test-prep-phenotab")
out_file = out_prefix + "-phenotypes.tsv.gz"

obo = MinimalObo(obo_file, True)


class ReferenceIdTests(unittest.TestCase):
    """Test cases for function valid_reference_id."""
    
    def test_accepts(self):
        """function accepts proper reference ids."""
                    
        self.assertTrue(valid_reference_id("OMIM:10001"))
        self.assertTrue(valid_reference_id("DECIPHER:10"))
        self.assertTrue(valid_reference_id("ORPHANET:9002"))
        self.assertTrue(valid_reference_id("ORPHA:9002"))
        self.assertTrue(valid_reference_id("DISEASE:1"))

    def test_rejects(self):
        """function accepts proper reference ids."""
                    
        self.assertFalse(valid_reference_id("OMIM:"))
        self.assertFalse(valid_reference_id("OMIM:1234;PMID:2330"))


class PrepRefsTests(unittest.TestCase):
    """Test cases for parsing information from MGI tables"""
    
    def setUp(self):            
        self.references, self.badphenotypes = prep_refs(refs_file, oo_file)
                   
    def tearDown(self):
        """remove any written-out files (if generated)"""
        remove_if_exists(out_file)                    
        
    def test_get_oo(self):
        """getting ontology-ontology mapping"""
        
        oomap = get_oo_map(oo_file)
        ## file has four phenotypes
        self.assertEqual(len(oomap), 4)
        self.assertTrue("X:001" in oomap)
        self.assertTrue("X:007" in oomap)
        ## term1 X:001 maps to a single other term2
        self.assertEqual(len(oomap["X:001"]), 1)
        self.assertEqual(oomap["X:001"][0][0], "Y:002")
        self.assertEqual(oomap["X:001"][0][1], 0.72)
        # term1 X:003 maps to a pair of other ontology terms
        self.assertEqual(len(oomap["X:003"]), 2)
        
    def test_inputs(self):
        """check that input file exists"""        
        self.assertEqual(exists(refs_file), True, "input file should exist")
            
    def test_identify_bad_phenotypes(self):
        """catch phenotypes that could not convert to different ontology"""
        
        self.assertEqual(len(self.badphenotypes), 1)
        self.assertTrue("X:999" in self.badphenotypes)
    
    def test_all_references_converted(self):
        """all diseases are converted into output"""
        
        # define primary (raw) ontology terms and secondary (target) terms
        term1 = set(["X:001", "X:002", "X:003", "X:007"])
        term2 = set(["Y:002", "Y:003", "Y:001", "Y:007"])        
        diseases = set(["DISEASE:1", "DISEASE:2", "DISEASE:3", "DISEASE:4"])
                
        refs = self.references
        self.assertEqual(len(refs), 4)
        self.assertEqual(set(refs.keys()), diseases)
                
        ## check that all phenotypes are converted
        self.assertEqual(len(refs["DISEASE:1"].data), 3)
        self.assertEqual(len(refs["DISEASE:2"].data), 3)
        self.assertEqual(len(refs["DISEASE:3"].data), 3)
        self.assertEqual(len(refs["DISEASE:4"].data), 2,
                         "DISEASE:4 has only X:003, changes to two Y terms")
        
        for d in diseases:
            phenotypes = set(refs[d].data.keys())            
            self.assertEqual(phenotypes.difference(term2), set())
    
    def test_writing(self):
        """write the parsed phenotypes into file"""
                
        write_references(self.references, out_prefix)
        
        # read contents back
        self.assertTrue(exists(out_file))        
        with open_file(out_file, "rt") as f:
            result = f.read().strip().split("\n")
        self.assertEqual(len(result), 12,
                         "rows 3+3+3+2 for phenotypes and 1 for header")
                   
    def test_control_models(self):
        """create models with technical controls"""
        
        c0, c1 = prep_tech_models(self.references, (0.8, 0.05), obo)
        
        # technical model sets should have one model per reference
        self.assertEqual(len(self.references), len(c0))
        self.assertEqual(len(self.references), len(c1))
        
        # all models should have at least one phenotype
        for key, model in c0.items():
            self.assertGreater(len(model.data), 0, 
                               key+" should have at least one phenotype")
            self.assertTrue(model.id.endswith("_match"))
        for key, model in c1.items():
            self.assertGreater(len(model.data), 0, 
                               key+" should have at least one phenotype")
            self.assertTrue(model.id.endswith("_siblings"))

