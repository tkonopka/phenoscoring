'''Tests for contents of db/db.py, db/dbtable.py

@author: Tomasz Konopka
'''


import unittest
from os.path import join
from db.db import setup_db 
from db.table import DBTableExample
from db.exporter import DBExporter
from ..testhelpers import remove_if_exists


# location of test database and tsv export
dbfile = join("tests", "testdata", "testdb.sqlite")
outfile = join("tests", "testdata", "test.tsv")


class DBExporterTests(unittest.TestCase):
    """Test cases for exporting data from a db."""
       
    def setUp(self):
        """For setup, create and fill db with a small amount of data."""
        
        setup_db(dbfile, tables=[DBTableExample])
        self.kvtab = DBTableExample(dbfile)        
        self.kvtab.add("one", 1)
        self.kvtab.add("two", 2)
        self.kvtab.add("three", 3)
        self.kvtab.add("four", 4)
        self.kvtab.save(True)
                
    def tearDown(self):
        """At end, ensure test db is deleted."""
        
        remove_if_exists(dbfile)       
        remove_if_exists(outfile)        

    def test_read_bad_class(self):
        """generator constructor fails with wrong input."""
                
        with self.assertRaises(Exception) as e:            
            reader = DBExporter(5)

    def test_write(self):
        """generator can write to an output file."""
        
        exporter = DBExporter(self.kvtab)
        exporter.to_tsv(outfile)
                
        with open(outfile, "r") as f:
            output = f.readlines()
        
        self.assertEqual(len(output), 5, "four rows plus header")
        self.assertEqual(output[0], "key\tvalue\n", "header with 2 cols")  
        self.assertEqual(output[1][:3], "one", "first row")

