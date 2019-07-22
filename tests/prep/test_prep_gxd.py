'''Tests for contents of phenoprep/prep_gxd.py

@author: Tomasz Konopka
'''

import unittest
from os.path import join
from obo.obo import MinimalObo
from phenoprep.prep_gxd import get_emapa_map, get_gxd, prep_GXD

# input file paths
testdir = join("tests", "testdata")
emapa_file = join(testdir, "emapa.tsv")
obo_file = join(testdir, "Y.obo")
gxd_file = join(testdir, "gxd.tsv")

# IMPC models and phenotypes
desc_file = join(testdir, "prep-IMPC-descriptions.tsv")
phen_file = join(testdir, "prep-IMPC-phenotypes.tsv")


class PrepGXDTests(unittest.TestCase):
    """Test cases for parsing information from an EMAP-MP table"""
         
    def setUp(self):
        """have a target ontology ready"""        
        
        self.obo = MinimalObo(obo_file)
        self.emapa = get_emapa_map(emapa_file, self.obo)        

    def test_emapa_simple(self):
        """check that EMAPA codes map onto MP ids"""
        
        result = self.emapa                
        self.assertEqual(set(result["EMAPA:2"]), set(["Y:006"]), 
                         "simple mapping")
        self.assertEqual(set(result["EMAPA:3"]), set(["Y:007"]), 
                         "simple mapping")
        
   
    def test_emapa_multi(self):
        """check picking mp terms with fewest ancestors"""
        
        result = self.emapa        
        self.assertEqual(set(result["EMAPA:1"]), set(["Y:003"]), 
                         "Y:3 is closest to root")
        
    
    def test_gxd_simple(self):
        """check that input file exists"""
                
        gxd = get_gxd(gxd_file, self.emapa, (0.5, 0.05))        
        
        # check ids
        self.assertEqual(len(gxd), 3, "three models/markers")
        self.assertEqual(gxd["MA:010"].id, "GXD_MA:010")
        self.assertEqual(gxd["MA:011"].id, "GXD_MA:011")
        self.assertEqual(gxd["MA:009"].id, "GXD_MA:009")
                
        # check markers
        self.assertEqual(gxd["MA:010"].description["marker_id"], "MA:010")
        self.assertEqual(gxd["MA:011"].description["marker_id"], "MA:011")
        self.assertEqual(gxd["MA:009"].description["marker_id"], "MA:009")
        
        # check parsing and consensus for phenotype        
        self.assertEqual(len(gxd["MA:010"].data), 1, "1+")
        self.assertEqual(len(gxd["MA:011"].data), 2, "1+, 1- phenotypes")
        self.assertEqual(len(gxd["MA:009"].data), 1, "1+ after consensus")
        
        # MA:009 should be averaged over assay, weighted by strength
        # i.e. value 1, tpr_raw*(2/3)
        datum = gxd["MA:009"].data[0]
        self.assertEqual(datum.value, 1, "overall should be detected")        
        self.assertEqual(datum.tpr, (0.05 + (0.5-0.05)*0.25)*2/3)
        self.assertEqual(datum.fpr, 0.05)
        
        # MA:010 should be average (Strong, Not specified), weighted by strength only
        datum = gxd["MA:010"].data[0]
        self.assertEqual(datum.value, 1, "overall is detected")
        self.assertEqual(datum.tpr, 0.05 + (0.5-0.05)*0.75)
        self.assertEqual(datum.fpr, 0.05)
        
        
    def test_GXD_models(self):
        """augment existing models with gxd phenotypes."""
        
        gxd = get_gxd(gxd_file, self.emapa, (0.5, 0.05))        
        models = prep_GXD(desc_file, phen_file, gxd)        
        
        # all models should have expression_phenotypes set to unity
        for id, model in models.items():
            self.assertEqual(model.get("expression_phenotypes"), 1, id)

