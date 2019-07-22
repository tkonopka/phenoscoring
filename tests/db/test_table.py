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


class DBTableTests(unittest.TestCase):
    """Test cases for class DBTable."""
    
    
    def setUp(self):
        """For setup, ensure db does not exist."""
        
        setup_db(dbfile, tables=[DBTableExample])
        self.kvtab = DBTableExample(dbfile)
                
       
    def tearDown(self):
        """At end, ensure test db is deleted."""
        
        remove_if_exists(dbfile)                
        
    
    def test_db_bad_schema_1(self):
        """Catch errors when creating tables with bad schemas."""
        
        class DBTableNoName(DBTable):
            """An example subclass of DBTable that is not valid."""                
            textfields = ["key"]
            realfields = ["value"]
   
        with self.assertRaises(Exception) as e:
            instance = DBTableNoName(dbfile)
        
   
    def test_db_bad_schema_2(self):
        """Catch errors when creating tables with bad schemas."""
        
        class DBTableNoFields(DBTable):
            """An example subclass of DBTable that is not valid."""                
            tabname = "bad_table"
   
        with self.assertRaises(Exception) as e:
            instance = DBTableNoFields(dbfile)
   
   
    def test_db_bad_dbpath(self):
        """Catch errors when creating tables from bad db paths."""
                
        with self.assertRaises(Exception) as e:
            instance = DBTableExample(dbfile+"bad")
   
    
    def test_table_addone(self):
        """Can add record into table"""
                
        self.kvtab.add("one", 4)
        self.kvtab.save(True)
        self.assertGreater(self.kvtab.count_rows(), 0, 
                           "should have at least one row after add")
    
    
    def test_table_empty(self):
        """Can add file"""
                        
        self.kvtab.add("one", 4)
        self.kvtab.save(True)
        self.assertGreater(self.kvtab.count_rows(), 0, 
                        "should have at least one record after save")    
        self.kvtab.empty()
        self.assertEqual(self.kvtab.count_rows(), 0, 
                        "should have nothing after empty")
    
    
    def test_table_unique(self):
        """Can quickly identify all values in a field"""
                
        self.kvtab.add("one", 4)
        self.kvtab.add("two", 4)
        self.kvtab.add("two", 5)
        self.kvtab.save(True)
        self.assertEqual(self.kvtab.count_rows(), 3)
        result = self.kvtab.unique("key")
        self.assertEqual(set(result), set(["one", "two"]))
    
    
    def test_table_avoidsave(self):
        """Avoid doing work in save if nothing has been staged"""
                
        self.kvtab.empty()
        self.kvtab.add("one", 4)
        self.kvtab.save(True)
        self.assertEqual(self.kvtab.count_rows(), 1, 
                        "should have nothing after empty")        
        ## next save without add should do nothing
        self.kvtab.save(True)
        self.assertEqual(self.kvtab.count_rows(), 1, 
                        "should have nothing after empty")        
        
    
    def test_table_addwait(self):
        """Can defer sending data to db in save() command"""
                
        self.kvtab.empty()
        self.kvtab.add("one", 4)
        self.kvtab.save(False)        
        self.assertEqual(self.kvtab.count_rows(), 0, 
                        "should have nothing because save is delayed")        
        self.kvtab.save(True)        
        self.assertEqual(self.kvtab.count_rows(), 1, 
                        "should have one because save is forced")        
            
                        
    def test_table_content(self):
        """Can extract content as a string"""
                
        self.kvtab.empty()
        self.kvtab.add("one", 4)
        self.kvtab.save(True)
        content = self.kvtab.content()      
        self.assertTrue("one" in content, 
                        "output string should contain inserted row")        
        
    
    def test_table_update(self):
        """can change existing rows"""
                                
        self.kvtab.add("A", 4)
        self.kvtab.add("B", 5)
        self.kvtab.save()
        self.kvtab.update(dict(value=10), dict(key="A"))
        content = self.kvtab.content()        
        self.assertTrue("10" in content)
        
    
    def test_table_update_raises(self):
        """update checks for field names"""
                                
        self.kvtab.add("A", 4)
        self.kvtab.add("B", 5)
        self.kvtab.save()
        with self.assertRaises(Exception) as e1:
            self.kvtab.update(dict(val=10), dict(key="A"))
        with self.assertRaises(Exception) as e2:
            self.kvtab.update(dict(value=10), dict(k="A"))
            
    
    def test_table_delete_raises(self):
        """delete check field names"""
    
        self.kvtab.add("A", 4)
        self.kvtab.save()
        # this should raise because 'val' is not a column name
        with self.assertRaises(Exception) as e0:
            self.kvtab.delete("val", ["A"])
    
    
    def test_table_delete(self):
        """can change existing rows"""
                                
        self.kvtab.add("A", 4)
        self.kvtab.add("B", 5)
        self.kvtab.add("C", 5)
        self.kvtab.add("D", 10)
        self.kvtab.save()
        # delete two rows (one id is irrelevant)
        self.kvtab.delete("key", ["A", "C", "ZZZ"])
        self.assertEqual(self.kvtab.count_rows(), 2)
        # check content of the table
        content = self.kvtab.content()
        self.assertFalse("A" in content)
        self.assertTrue("B" in content)        
        self.assertFalse("C" in content)
        self.assertTrue("D" in content)

