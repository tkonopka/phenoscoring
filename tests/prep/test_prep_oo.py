'''Tests for preparing ontology-ontology mappings

@author: Tomasz Konopka
'''

from os.path import join
import unittest
from obo.obo import MinimalObo
from phenoprep.prep_oo import prep_oo
from phenoprep.write import write_oo
from tools.files import open_file
from ..testhelpers import remove_if_exists

testdir = join("tests", "testdata")
obo_file = join(testdir, "Y.obo")
obo = MinimalObo(obo_file)

# file with a multi-line ontology-ontology map
largefile = join(testdir, "owlsim-large.txt")
# file with a 1-to-1 ontology map
smallfile = join(testdir, "owlsim-multi.txt")
# file for writing output
outfile = join(testdir, "owlsim-multi-oomap.tsv.gz")


class PrepOOTests(unittest.TestCase):
    """Test cases creating ontology-ontology map."""
    
    def tearDown(self):
        """remove any written-out files (if generated)"""
        remove_if_exists(outfile)                        
    
    def test_prep_oo(self):
        """Parse small obo file, identify ids"""  
                
        output = prep_oo(largefile, obo, True)
        self.assertEqual(len(output), 6)
        
        # first lines should map X:001 to Y:001 and sibling Y:002 
        self.assertEqual(output[0][0], "X:001")
        self.assertEqual(output[0][1], "Y:001")
        self.assertAlmostEqual(output[0][2], 0.56)        
        self.assertEqual(output[1][0], "X:001")
        self.assertEqual(output[1][1], "Y:002")
        self.assertAlmostEqual(output[1][2], 0.72)
        # next two lines should map X:002 and X:003
        self.assertEqual(output[2][0], "X:002")
        self.assertEqual(output[3][0], "X:003")
    
    def test_write_oo(self):
        """can write output to a tabular file with columns"""
        
        output = prep_oo(largefile, obo, True)
        write_oo(output, join(testdir, "owlsim-multi"))
        
        with open_file(outfile, "rt") as f:
            result = f.read().strip()        
        with open_file(smallfile, "rt") as f:
            expected = f.read().strip()
                
        self.assertEqual(result, expected)
