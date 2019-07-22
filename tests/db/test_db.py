'''Tests for contents of db/db.py, db/dbtable.py

@author: Tomasz Konopka
'''


import os
import unittest
from db.db import setup_db, get_conn 
from db.table import DBTable, DBTableExample
from ..testhelpers import remove_if_exists

## location of test database
dbfile = os.path.join("tests", "testdata", "testdb.sqlite")
       

class DBTableNoFields(DBTable):
    """An example subclass of DBTable that is not valid"""
        
    tabname = "bad_table"


class DBTests(unittest.TestCase):
    """Test cases for basic manipulation of dbs."""
    
    
    def setUp(self):
        """For setup, ensure db does not exist."""
        remove_if_exists(dbfile)                        
          
    def tearDown(self):
        """At end, ensure test db is deleted."""     
        remove_if_exists(dbfile)
            
    def test_dbinit(self):
        """Can create a database file"""
        
        self.assertFalse(os.path.exists(dbfile))
        setup_db(dbfile, tables=[DBTableExample])
        self.assertTrue(os.path.exists(dbfile))
            
    def test_db_reinit_noreset(self):
        """Avoid a database file"""
                
        ## create a database with a table
        setup_db(dbfile, tables=[DBTableExample], reset=True)
        kvtab = DBTableExample(dbfile)
        kvtab.add("one", 1)
        kvtab.save()
        ## try to re-init
        setup_db(dbfile, tables=[DBTableExample])
        ## default is reset=False, so data should still be present
        self.assertEqual(kvtab.count_rows(), 1, 
                           "should have one row")        

    def test_db_reinit_reset(self):
        """Avoid a database file"""
                
        ## create a database with a table
        setup_db(dbfile, tables=[DBTableExample], reset=True)
        kvtab = DBTableExample(dbfile)
        kvtab.add("one", 1)
        kvtab.save()
        ## try to re-init
        setup_db(dbfile, tables=[DBTableExample], reset=True)
        ## default is reset=False, so data should still be present
        self.assertEqual(kvtab.count_rows(), 0, 
                           "db should be new from-scratch")
        
