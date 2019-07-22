'''Tests for contents of phenoprep/prep_impc.py

@author: Tomasz Konopka
'''

import unittest
from os.path import join, exists
from obo.obo import MinimalObo
from phenoprep.prep_imputation import get_UA_models, make_scaled_cooc 
from phenoprep.prep_imputation import get_models_by_phenotype, impute_IMPC
from phenoprep.prep_impc import prep_IMPC, sex_code, get_IMPC_hits_summary
from phenoprep.write import write_models, write_phenotype_cooc
from phenoprep.write import write_hits_summary
from ..testhelpers import remove_if_exists
from tools.files import open_file

# input file paths
testdir = join("tests", "testdata")
impc_file = join(testdir, "IMPC-stats-small.csv")
obo_file = join(testdir, "Y.obo")
out_prefix = join(testdir, "test-prep-IMPC")


# output file paths
desc_file = out_prefix + "-models.tsv.gz"
pheno_file = out_prefix + "-phenotypes.tsv.gz"
hits_file = out_prefix + "-hits-summary.tsv.gz"
imputed_desc_file = out_prefix + "-imputed-models.tsv.gz"
imputed_pheno_file = out_prefix + "-imputed-phenotypes.tsv.gz"
cooc_full_file = out_prefix+"-full-cooc.tsv.gz"
cooc_simJ_file = out_prefix+"-simJ-cooc.tsv.gz"
cooc_freq_file = out_prefix+"-freq-cooc.tsv.gz"


class PrepIMPCTests(unittest.TestCase):
    """Test cases for parsing information from IMPC tables"""
         
    def tearDown(self):
        """remove any written-out files (if generated)"""
        all_files = [desc_file, pheno_file, hits_file,
                    imputed_desc_file, imputed_pheno_file,
                    cooc_full_file, cooc_freq_file, cooc_simJ_file]        
        for x in all_files:
            remove_if_exists(x)
        
    def test_inputs(self):
        """check that input file exists"""
        
        self.assertEqual(exists(impc_file), True, "input file should exist")
        
    def test_sex_code(self):
        """translation from IMPC gender string to a one-letter code."""
        
        self.assertEqual(sex_code("female,male"), "B")
        self.assertEqual(sex_code("male"), "M")
        self.assertEqual(sex_code("M"), "M")
        self.assertEqual(sex_code("female"), "F")
        self.assertEqual(sex_code("F"), "F")
        self.assertEqual(sex_code("male,female"), "B")
        self.assertEqual(sex_code(""), "U")
    
    def test_parsing_empty(self):
        """parsing empty input return empty dict"""
        
        result = prep_IMPC(None, None, None)
        self.assertEqual(result, dict())
    
    def test_parsing(self):
        """parsing should return model descriptions"""
        
        models = prep_IMPC(impc_file, (0.8, 0.05), 0.01)
        
        # should get eight models
        # two marker, two allele; one zygosity
        # one set of 4 with positive phenoytpes,
        # one set of 4 with negative phenotypes
        # that is 8. Then x3 for universal/male/female
        self.assertEqual(len(models), 24)
        
        alleles = set()
        markers = set()
        for _,value in models.items():
            alleles.add(value.description["allele_id"])
            markers.add(value.description["marker_id"])
        
        self.assertEqual(len(alleles), 2)
        self.assertEqual(len(markers), 2)          
        
        # count the male and female models
        males, females, unspecified = 0, 0, 0
        for _,value in models.items():
            sex = value.description["sex"]
            if sex =="M":
                males += 1
            elif sex == "F":
                females += 1
            elif sex:
                unspecified +=1
        self.assertEqual(males, females, "should be paired and equal")
        self.assertEqual(males, unspecified, "should be paired and equal")
        self.assertGreater(males, 0)        
    
    def test_writing(self):
        """write the parsed MGI data onto files"""
        
        models = prep_IMPC(impc_file, (0.8, 0.05), 0.01)
        write_models(models, out_prefix)
        
        # read contents back
        self.assertTrue(exists(desc_file))
        self.assertTrue(exists(pheno_file))
        with open_file(desc_file, "rt") as f:
            desc = f.read().strip().split("\n")
        with open_file(pheno_file, "rt") as f:
            pheno = f.read().strip().split("\n")
        
        # description file should have 25 lines, 24 data lines plus header
        self.assertEqual(len(desc), 25)
        # phenotype file should have at least 7 lines (more)
        self.assertGreater(len(pheno), 7)
          
    def test_hits_summary(self):
        """get a summary of number of hits."""
        
        tested, hits = get_IMPC_hits_summary(impc_file, 0.01)        
        self.assertEqual(len(tested), len(hits))
        
        # objects tested and hits should have the same keys
        self.assertEqual(set(tested.keys()), set(hits.keys()))
        # number of hits should be smaller than number of tested 
        for key in tested:            
            self.assertTrue(len(hits[key])<=len(tested[key]))
                
    def test_write_hits_summary(self):
        """get a summary of number of hits."""
        
        tested, hits = get_IMPC_hits_summary(impc_file, 0.01)        
        write_hits_summary(tested, hits, out_prefix)
        
        self.assertTrue(exists(hits_file))
        with open_file(hits_file, "rt") as f:
            summary = f.read().strip().split("\n")
        
        # output should have three phenotypes plus header
        self.assertEqual(len(summary), 4)
    
    def test_imputing(self):
        """create new models based on UA."""
        
        obo = MinimalObo(obo_file)
        models = prep_IMPC(impc_file, (0.8, 0.05), 0.01)
        models_allele = get_UA_models(models, "allele")
        imputed = impute_IMPC(models_allele, obo, 0)
        write_models(imputed, out_prefix+"-imputed")
        
        # check output files exist and contain proper content
        self.assertTrue(exists(imputed_desc_file))
        self.assertTrue(exists(imputed_pheno_file))
        with open_file(imputed_desc_file, "rt") as f:
            desc = f.read().strip().split("\n")
        with open_file(imputed_pheno_file, "rt") as f:
            pheno = f.read().strip().split("\n")
        
        # description file should have 3 lines, 2 desc lines plus header
        self.assertEqual(len(desc), 3)
        # phenotype file should have a few lines
        self.assertGreater(len(pheno), 3)
            
    def test_scaled_cooc(self):
        """write out cooc matrices"""
        
        obo = MinimalObo(obo_file)
        models = prep_IMPC(impc_file, (0.8, 0.05), 0.01)
        models_allele = get_UA_models(models, "allele")        
        observed = get_models_by_phenotype(models_allele, 1)
        # write out various types of cooc matrices        
        cooc_full, phenindex = make_scaled_cooc(observed, obo, 0, "full")
        write_phenotype_cooc(cooc_full, phenindex, out_prefix + "-full")
        cooc_freq, phenindex = make_scaled_cooc(observed, obo, 0, "freq")
        write_phenotype_cooc(cooc_freq, phenindex, out_prefix + "-freq")
        cooc_simJ, phenindex = make_scaled_cooc(observed, obo, 0, "simJ")
        write_phenotype_cooc(cooc_simJ, phenindex, out_prefix + "-simJ")
                            
        # check the numerics of the matrices
        for p1, i1 in phenindex.items():
            for p2, i2 in phenindex.items():                
                observed = cooc_full[i1, i2]
                expected = cooc_freq[i1, i2]*(1-cooc_simJ[i1, i2])                                
                self.assertEqual(observed, expected) 
        
        # check all the files exist        
        self.assertTrue(exists(cooc_full_file))
        self.assertTrue(exists(cooc_freq_file))
        self.assertTrue(exists(cooc_simJ_file))
        
        # very gently (not rigorously check content of files)
        with open_file(cooc_full_file, "rt") as f:
            full = f.read().strip().split("\n")
        self.assertGreater(len(full), 2)

