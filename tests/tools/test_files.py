'''
Tests for contents of tools/files.py
'''

import unittest
from os.path import join, exists
from tools.files import check_file, write_dict, values_in_column
from ..testhelpers import remove_if_exists


testdir = join("tests", "testdata")
out_tsv = join(testdir, "outfile.tsv")
out_gz = join(testdir, "outfile.tsv.gz")


class CheckFileTests(unittest.TestCase):
    """Test cases for function check_file."""
    
    def tearDown(self):
        """remove any written-out files (if generated)"""         
                   
        remove_if_exists(out_tsv)
        remove_if_exists(out_gz)
        
    def test_check(self):
        """check succeeds."""
                
        file_path = join("tests", "testdata", "small.obo")        
        selected_path = check_file(file_path, None, required=None)        
        self.assertEqual(selected_path, file_path)    
    
    def test_uses_fallback(self):
        """check doesn't find file, returns fallback."""
                
        file_path = join("tests", "not-a-dir", "small.obo")
        fallback_path = join("tests", "testdata", "small.obo")
        selected_path = check_file(file_path, fallback_path, required=None)        
        self.assertEqual(selected_path, fallback_path)
        
    
    def test_allow_none(self):
        """allows a file check to return None."""
                        
        result = check_file(None, None, required="aaa", allow_none=True)
        self.assertEqual(result, None)
    
    def test_detects_required(self):
        """check raises exception when a required file is not present."""
                
        with self.assertRaises(Exception):
            check_file(None, None, required=True)
                        
    def test_detects_missing(self):
        """neither primary or fallback file exist."""
                
        file_path = join("tests", "not-a-dir", "small.obo")
        fallback_path = join("tests", "also-not-a-dir", "small.obo")
        
        with self.assertRaises(Exception):
            check_file(file_path, fallback_path)

    def test_write_dict_gz(self):
        """write a dictionary into a gzip file"""
                
        data = dict(a=10, b=20)
        write_dict(data, out_gz)
        self.assertTrue(exists(out_gz))
        self.assertFalse(exists(out_tsv))
        
    def test_write_dict_tsv(self):
        """write a dictionary, automatically gzip"""
                
        data = dict(a=10, b=20)
        write_dict(data, out_tsv)
        self.assertTrue(exists(out_gz))
        self.assertFalse(exists(out_tsv))
        
    def test_read_values_from_column(self):
        """obtain some values from a single column in a file."""
        
        # create a file
        data = dict(a=1, z=2, b=3, y=4)
        write_dict(data, out_gz)
        ids = values_in_column(out_gz, "id")
        values = values_in_column(out_gz, "value")
        datastr = [str(_) for _ in data.values()]
        self.assertEqual(sorted(ids), sorted(data.keys()))
        self.assertEqual(sorted(values), sorted(datastr))
        
    def test_write_dict_multicolumn(self):
        """write a dictionary with multiple columns"""
        
        data = dict(a=(1,8), b=(2,3))
        write_dict(data, out_gz, colnames=("id", "X", "Y"))
        ids = values_in_column(out_gz, "id")
        X = values_in_column(out_gz, "X")
        Y = values_in_column(out_gz, "Y")
        
        # this assumes that the dictionary get written out in order
        self.assertEqual(ids, ["a","b"])
        self.assertEqual(X, ["1", "2"])
        self.assertEqual(Y, ["8", "3"])

