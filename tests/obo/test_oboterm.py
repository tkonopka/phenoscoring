'''
Tests for definitions of obo terms
'''


import unittest
from obo.oboterm import MinimalOboTerm, OboTerm


class MinmalOboTermTests(unittest.TestCase):
    """Test cases for class MinimalOboTerm."""
    
    def test_str(self):
        """str summarizes content of object"""  
        
        term = MinimalOboTerm()
        term.parse("id: ABC:002")
        term.parse("")
        term.parse("name: child_A")
        result = str(term)
        # the object can be stringified, but does not contain the name
        self.assertTrue("ABC" in result)
        self.assertFalse("child_A" in result)


class OboTermTests(unittest.TestCase):
    """Test cases for class OboTerm."""
        
    def test_new_term(self):
        """New terms are blank."""  
        
        term = OboTerm()
        self.assertEqual(term.id, None, "id is None by default")
        self.assertEqual(term.name, None, "name is None by default")
        self.assertFalse(term.valid(), "not valid when empty")

    def test_parse_idterm(self):
        """Parsing id and name."""  
        
        term = OboTerm()
        term.parse("id: ABC:001")
        term.parse("name: root node")
        self.assertEqual(term.id, "ABC:001", "id is set")
        self.assertEqual(term.name, "root node", "name is set")
        self.assertTrue(term.valid(), "valid because non-empty")
        self.assertFalse(term.obsolete, "not obsolete is default")

    def test_str(self):
        """str summarizes content of object"""  
        
        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("name: child_A")
        result = str(term)
        self.assertTrue("child_A" in result)
        self.assertTrue("ABC" in result)

    def test_parse_synonyms(self):
        """Parsing a synonym."""  
        
        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("name: child A")
        term.parse("synonym: child a")
        self.assertEqual(term.synonyms, set(["child a"]))        

    def test_parse_synonyms_requires_name(self):
        """a synonym cannot be assigned before a name"""  
        
        term = OboTerm()
        term.parse("id: ABC:002")        
        with self.assertRaises(Exception) as e:            
            term.parse("synonym: abc")
        self.assertTrue("name" in str(e.exception))     

    def test_parse_synonyms_avoid_self_pointers(self):
        """a synonym cannot be the same as the name"""  
        
        term = OboTerm()
        term.parse("id: ABC:002") 
        term.parse("name: abc")
        term.parse("synonym: abc")
        self.assertEqual(term.synonyms, set())

    def test_parse_extrafield(self):
        """Parsing an arbitrary field."""

        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("name: child A")
        self.assertEqual(term.data, None, "data should have nothing")
        term.parse("somefield: somevalue")
        self.assertEqual(len(term.data), 1, "data should have one field")

    def test_parse_emptylines(self):
        """can skip over parsing empty lines."""  
        
        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("")
        term.parse("name: child_A")        
        self.assertTrue("child_A" in str(term))

    def test_parse_obsolete(self):
        """identifies obsolete."""  
        
        term = OboTerm()
        term.parse("id: ABC:002")        
        term.parse("name: abc")
        term.parse("is_obsolete: true")
        self.assertTrue(term.valid(), "valid because non-empty")
        self.assertTrue(term.obsolete, "is obsolete")

    def test_parse_obsolete_strict(self):
        """is strict about values in is_obsolete line"""  
        
        term = OboTerm()
        term.parse("id: ABC:002")        
        term.parse("name: abc")
        with self.assertRaises(Exception) as e1:            
            term.parse("is_obsolete: True") 
        self.assertTrue("obsolete" in str(e1.exception))
                   
        with self.assertRaises(Exception) as e2:
            term.parse("is_obsolete: false")
        self.assertTrue("obsolete" in str(e1.exception))

    def test_parse_replaced_nonobsolete(self):
        """replaced_by relation cannot be used on non-obsolete terms"""

        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("name: abc")
        with self.assertRaises(Exception) as e1:
            term.parse("replaced_by: ABC:003")
        self.assertTrue("obsolete" in str(e1.exception))

    def test_parse_obsolete_replaced(self):
        """obsolete terms can record an alternative id"""

        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("name: abc")
        self.assertEqual(len(term.relations), 0, "no relations at start")
        term.parse("is_obsolete: true")
        self.assertTrue(term.obsolete, "is obsolete")
        self.assertEqual(len(term.relations), 0, "still not replaced")
        term.parse("replaced_by: ABC:003")
        relations = term.relations
        self.assertEqual(len(term.relations), 1, "now has one relation")
        self.assertEqual(relations[0], ("replaced_by", "ABC:003"))

    def test_parse_alt_id(self):
        """alternative id are recorded in a set"""

        term = OboTerm()
        term.parse("id: ABC:002")
        term.parse("name: abc")
        self.assertEqual(len(term.alts), 0)
        term.parse("alt_id: ABC:2")
        term.parse("alt_id: ABC:02")
        self.assertEqual(len(term.alts), 2)
        self.assertTrue("ABC:2" in term.alts)

