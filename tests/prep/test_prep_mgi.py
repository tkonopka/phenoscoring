'''
Tests for contents of phenoprep/prep_mgi.py
'''

import unittest
from os.path import join, exists
from obo.obo import MinimalObo
from phenoprep.prep_mgi import prep_MGI
from phenoprep.write import write_models
from ..testhelpers import remove_if_exists
from tools.files import open_file


testdir = join("tests", "testdata")
mgi_file = join(testdir, "MGI-GP-small.rpt")
obo_file = join(testdir, "Y.obo")
out_prefix = join(testdir, "test-prep-MGI")
desc_file = out_prefix + "-models.tsv.gz"
pheno_file = out_prefix + "-phenotypes.tsv.gz"
obo = MinimalObo(obo_file)


class PrepMGITests(unittest.TestCase):
    """Test cases for parsing information from MGI tables"""
     
    def tearDown(self):
        """remove any written-out files (if generated)"""
        remove_if_exists(desc_file)
        remove_if_exists(pheno_file)        
        pass

    def test_inputs(self):
        """check that input file exists"""
        
        self.assertEqual(exists(mgi_file), True, "input file should exist")
         
    def test_parsing(self):
        """parsing should return """
        
        models = prep_MGI(mgi_file, (0.8, 0.05), obo)
        
        # should get four models (one marker, one allele; two zygosities)
        self.assertEqual(len(models), 4)
        
        alleles = set()
        markers = set()
        for _, value in models.items():
            alleles.add(value.get("allele_id"))
            markers.add(value.get("marker_id"))
        
        self.assertEqual(len(alleles), 1)
        self.assertEqual(len(markers), 1)                

    def test_writing(self):
        """write the parsed MGI data onto files"""
        
        models = prep_MGI(mgi_file, (0.8, 0.05), obo)
        write_models(models, out_prefix)
        
        # read contents back
        self.assertTrue(exists(desc_file))
        self.assertTrue(exists(pheno_file))
        with open_file(desc_file, "rt") as f:
            desc = f.read().strip().split("\n")
        with open_file(pheno_file, "rt") as f:
            pheno = f.read().strip().split("\n")
                
        # description file should have 5 lines, 4 data lines plus header
        # this one allele_id in two zygosities - 2 genotype models
        # 2 genotypes models will give 2 marker models
        self.assertEqual(len(desc), 5)
        # phenotype file should have at least 5 lines again (more)
        self.assertGreater(len(pheno), 5)
        
         
