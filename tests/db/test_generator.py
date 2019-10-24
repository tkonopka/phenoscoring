'''
Tests for contents of db/generator.py
'''

import unittest
from os.path import join
from db.db import setup_db 
from db.table import DBTableExample
from db.generator import DBGenerator
from ..testhelpers import remove_if_exists

# location of test database
dbfile = join("tests", "testdata", "testdb.sqlite")


class DBGeneratorTests(unittest.TestCase):
    """Test cases for basic manipulatino of dbs."""

    @classmethod
    def setUpClass(cls):
        """For setup, create and fill db with a small amount of data."""
        
        setup_db(dbfile, tables=[DBTableExample])
        cls.kvtab = DBTableExample(dbfile)
        cls.kvtab.add("one", 1)
        cls.kvtab.add("two", 2)
        cls.kvtab.add("three", 3)
        cls.kvtab.add("four", 4)
        cls.kvtab.save(True)

    @classmethod
    def tearDownClass(cls):
        """At end, ensure test db is deleted."""
        
        remove_if_exists(dbfile)       

    def test_read_from_table(self):
        """Read rows from database"""
        
        reader = DBGenerator(self.kvtab)
        values = [row["value"] for row in reader.next()]
        self.assertEqual(len(values), 4, "setup added 4 rows")

    def test_read_bad_class(self):
        """generator constructor fails with wrong input."""
                
        with self.assertRaises(Exception) as e:            
            DBGenerator(5)

    def test_read_where_invalid(self):
        """fails when where referes to inexistent field."""
        
        with self.assertRaises(Exception) as e:
            DBGenerator(self.kvtab, where=dict(id="aaa"))

    def test_read_where_key_one(self):
        """generator can fetch a subset of rows."""
        
        reader = DBGenerator(self.kvtab, where=dict(key="one"))
        values = [x["value"] for x in reader.next()]
        self.assertEqual(values, [1])

    def test_read_where_key_two(self):
        """generator can fetch a subset of rows."""
        
        reader = DBGenerator(self.kvtab, where=dict(key="two"))
        values = [x["value"] for x in reader.next()]
        self.assertEqual(values, [2])

    def test_subset_fields(self):
        """generator can extract a subset of columns/fieldnames."""
        
        reader = DBGenerator(self.kvtab, fieldnames=["value"])
        values = []
        for x in reader.next():
            self.assertEqual(len(x), 1, "only one field in output")
            values.append(x["value"])
        self.assertEqual(sorted(values), [1, 2, 3, 4])

    def test_invalid_fields(self):
        """fails when reqest for inexistent fieldnames."""
        
        with self.assertRaises(Exception) as e:
            DBGenerator(self.kvtab, fieldnames=["val"])

