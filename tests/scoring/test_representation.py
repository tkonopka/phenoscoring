'''
Tests for contents of scoring/representation.py
'''


import os.path
import unittest
from scoring.representation import Representation
from obo.obo import MinimalObo


class RepresentationTests(unittest.TestCase):
    """Test cases for class Representation."""
    
    defaults = dict(abc=0.1, xyz=0.1)    
    
    # file with a small obo-formatted ontology
    obofile = os.path.join("tests", "testdata", "small.obo")
    
    def setUp(self):
        """For setup, load a small ontology."""
        self.obo = MinimalObo(self.obofile)
        self.obodef = dict.fromkeys(self.obo.ids(), 0.2)        
        
    def test_empty_representation(self):
        """setting and getting from a generic representation."""  
                
        rr = Representation()
        self.assertEqual(len(rr.data), 0, "representation should be empty")                                  
        self.assertEqual(rr.name, None, "representation should not have a name")
    
    def test_named_representation(self):
        """setting and getting from a generic representation."""  
                
        rr = Representation(dict(abc=1), name="rr")                                        
        self.assertEqual(rr.name, "rr", "rep should have a name")
    
    def test_str(self):
        """setting and getting from a generic representation."""  
                
        ss = str(Representation(name="ABC XYZ"))        
        self.assertRegex(ss, "XYZ", "representation string should have name")                                  

    def test_set_feature(self):
        """can set and retrieve values"""

        rr = Representation()
        rr.set("abc", 0.2)
        self.assertEqual(rr.get("abc"), 0.2)

    def test_set_feature_float(self):
        """can set and retrieve values"""

        rr = Representation()
        rr.set("abc", 1)
        self.assertEqual(rr.get("abc"), 1.0)
        self.assertTrue(type(rr.get("abc")) is float)

    def test_init_float(self):
        """initializing with a dict ensure float values"""

        rr = Representation(dict(abc=1), name="rr")
        self.assertEqual(rr.get("abc"), 1.0)
        self.assertTrue(type(rr.get("abc")) is float)

    def test_general_representation_get(self):
        """setting and getting from a generic representation."""  
                
        rr = Representation(dict(xyz=0.2))
        rr.set("bob", 0.4)
        rr.set("xyz", 0.3)
        rr.defaults(self.defaults)        
        self.assertEqual(rr.get("bob"), 0.4, 
                         "value should come from manual input")
        self.assertEqual(rr.get("abc"), 0.1, 
                         "value should come from defaults dict")
        self.assertEqual(rr.get("xyz"), 0.3, 
                         "value should come from manual override")
           
    def test_keys(self):
        """setting and getting from a generic representation."""  
                
        rr = Representation(dict(xyz=0.2))
        rr.set("bob", 0.4)
        rr.set("xyz", 0.3)
        rr.defaults(self.defaults)        
        self.assertEqual(rr.keys(), ["abc", "xyz", "bob"], 
                         "keys should have defaults and non-defaults")
            
    def test_has(self):
        """querying whether a value has been set."""  
                
        rr = Representation(dict(xyz=0.2))
        rr.set("bob", 0.4)        
        self.assertTrue(rr.has("xyz"), "set in constructor")
        self.assertTrue(rr.has("bob"), "set manually")
        self.assertFalse(rr.has("alice"), "not set")
    
    def test_equality(self):
        """checking content of representations."""  
                
        r1 = Representation(self.defaults, name="hello")
        r2 = Representation(self.defaults, name="hello")
        r3 = Representation(self.defaults, name="bye")
        r4 = Representation(self.defaults, name="hello")
        r4.set("abc", 100)
        r5 = Representation()
        r6 = Representation(self.defaults, name="hello")
        r6.set("qqq", 20)
        
        self.assertTrue(r1.equal(r2), "all is the same")
        self.assertFalse(r1.equal(5), "argument is not a Representation")
        self.assertFalse(r1.equal(r3), "same content, but different name")
        self.assertFalse(r1.equal(r4), "same name, but different content")
        self.assertFalse(r1.equal(r5), "r5 is empty")
        self.assertFalse(r1.equal(r6), "r6 has more keys")
        self.assertFalse(r1.equal(range(4)), "must compare to Representation")
    
    def test_general_representation_get2(self):
        """setting and getting from a generic representation."""  
        
        ## Similar to previous, but setting defaults before the specifics        
        rr = Representation(dict(abc=0.1, xyz=0.2))
        rr.defaults(self.defaults)
        rr.set("bob", 0.4)
        rr.set("xyz", 0.3)        
        self.assertEqual(rr.get("bob"), 0.4, 
                         "value should come from manual input")
        self.assertEqual(rr.get("abc"), 0.1, 
                         "value should come from defaults dict")
        self.assertEqual(rr.get("xyz"), 0.3, 
                         "value should come from manual override")
          
    def test_impute_up(self):
        """updating values in representation via positive evidence."""  
                
        rr = Representation(dict())
        rr.set("unrelated", 0.8)             
        rr.set("DOID:0014667", 0.4)            
        rr.impute(self.obo, self.obodef)        
        
        self.assertEqual(rr.get("unrelated"), 0.8, 
                               msg="out-of-ontology terms remain")        
        self.assertEqual(rr.get("DOID:0014667"), 0.4, 
                               msg="set value should remain")
        self.assertGreater(rr.get("DOID:4"), 0.4, 
                           msg="ancestors should receive greater score")
        self.assertEqual(rr.get("DOID:0080015"), 0.2, 
                               msg="unrelated terms get default")        
        self.assertEqual(rr.get("DOID:655"), 0.2, 
                               msg="children are unaffected")  
    
    def test_impute_up_always_increases(self):
        """updating values in representation via positive evidence."""  
                
        rr = Representation(dict())                    
        rr.set("DOID:3650", 0.25)
        defaults = self.obodef.copy()
        defaults["DOID:0014667"] = 0.5
        defaults["DOID:4"] = 1        
        rr.impute(self.obo, defaults)                
          
        self.assertEqual(rr.get("DOID:3650"), 0.25, 
                         "set value should remain")
        self.assertGreater(rr.get("DOID:0060158"), 0.25, 
                           "ancestors should receive greater score")
        self.assertEqual(rr.get("DOID:655"), 0.2, 
                         "unrelated should stay at default")
        ## ancestor that has already a higher score than what is propagated
        self.assertGreater(rr.get("DOID:0014667"), 0.5, 
                           "ancestor should receive score greater than its prior")
    
    def test_impute_up_avoid_doubles(self):
        """updating values in representation via positive evidence in DAG"""  
                
        rr = Representation(dict())
        ## DOID:11044 in test ontology has two paths to root (DOID:4)
        ## one is direct (a shortcut)
        ## another path is through 0080015
        rr.set("DOID:11044", 0.4)        
        rr.impute(self.obo, self.obodef)                
        
        self.assertGreater(rr.get("DOID:0080015"), 0.2, "ancestor should increase")
        self.assertAlmostEqual(rr.get("DOID:0080015"), rr.get("DOID:4"), 
                         msg="4 should get bumped once, despite two paths from 11044")
        
    def test_impute_down(self):
        """updating values in representation via negative evidence."""  
                
        rr = Representation(dict())
        rr.set("unrelated", 0.8)             
        rr.set("DOID:0014667", 0.05)        
        rr.impute(self.obo, self.obodef)        
                
        self.assertAlmostEqual(rr.get("unrelated"), 0.8, 
                         "out-of-ontology terms remain")
        self.assertAlmostEqual(rr.get("DOID:0014667"), 0.05, 
                         "set value should remain")
        self.assertAlmostEqual(rr.get("DOID:4"), 0.2, 
                         "ancestors should remain")
        self.assertAlmostEqual(rr.get("DOID:0080015"), 0.2, 
                         "unrelated terms get default")     
        self.assertAlmostEqual(rr.get("DOID:655"), 0.05, 
                         "children are unaffected")    
        
    def test_impute_down_ordering(self):
        """updating values in representation via negative evidence."""  
                
        r1 = Representation(dict())
        r1.set("DOID:3650", 0.01).set("DOID:0014667", 0.05)        
        r2 = Representation(dict())
        r2.set("DOID:3650", 0.01).set("DOID:0014667", 0.05)
        ## imputation down should not depend on order of the seeds
        r1.impute(self.obo, self.obodef, seeds=["DOID:3650", "DOID:0014667"])
        r2.impute(self.obo, self.obodef, seeds=["DOID:0014667", "DOID:3650"])        
                        
        self.assertEqual(r1.data, r2.data, "all values the same")
           
    def test_impute_fromseeds_highfirst(self):
        """imputing values from manually-specified seeds."""  
                
        rr = Representation(dict())        
        ## specify data for two children, DOID:4 is higher in tree, so should gain 
        rr.set("DOID:0014667", 0.4)
        rr.set("DOID:0080015", 0.3)
                
        rr.impute(self.obo, self.obodef, 
                  seeds=["DOID:0014667", "DOID:0080015"])
                                      
        self.assertAlmostEqual(rr.get("DOID:0014667"), 0.4, 
                               msg="should remain")
        self.assertAlmostEqual(rr.get("DOID:0080015"), 0.3, 
                               msg="should remain")
        self.assertAlmostEqual(rr.get("DOID:4"), 1-((1-0.4)*(1-0.3)*(1-0.2)), 
                           msg="ancestor gains from two children (and prior)")            
        self.assertAlmostEqual(rr.get("DOID:655"), 0.2, 
                               msg="remain; new DOID:4")  

    def test_impute_fromseeds_lowfirst(self):
        """imputing values from manually-specified seeds."""  
                
        rr = Representation(dict())
        ## specify an inconsistent set of values, DOID:4 is higher in tree, so cannot
        ## have a lower value than DOID:0014667 
        rr.set("DOID:0014667", 0.4).set("DOID:4", 0.1)
        rr.impute(self.obo, self.obodef, seeds=["DOID:4", "DOID:0014667"])                                
        self.assertEqual(rr.get("DOID:0080015"), 0.1, "child of DOID:4")        
        self.assertEqual(rr.get("DOID:655"), 0.1, "child of DOID:4")  

    def test_impute_fromseeds_auto(self):
        """imputing values from automatically-ordered seeds."""  
                
        ## specify an inconsistent set of values, DOID:4 is higher in tree, so cannot
        ## have a lower value than DOID:0014667
        ## However, low DOID:4 can impact on other branches                 
        rr1 = Representation(dict())
        rr1.set("DOID:0014667", 0.4).set("DOID:4", 0.1)
        rr1.impute(self.obo, self.obodef)        
        
        ## auto seeds
        rr2 = Representation(dict())
        rr2.set("DOID:0014667", 0.4).set("DOID:4", 0.1)
        rr2.impute(self.obo, self.obodef)
        
        ## auto seeds, different initial ordering
        rr3 = Representation(dict())
        rr3.set("DOID:4", 0.1).set("DOID:0014667", 0.4)
        rr3.impute(self.obo, self.obodef)
                                    
        self.assertTrue(rr1.data == rr2.data, 
                        "auto and manual should have same data")
        self.assertTrue(rr2.data == rr3.data, 
                        "should be = regardless of input order")
        
        self.assertGreater(rr1.data["DOID:0014667"], 0.2,
                         "DOID:0014667 increase by direct evidence")        
        self.assertGreater(rr1.data["DOID:4"], 0.2, 
                           "DOID:4 increases driven by 0014667")
        self.assertEqual(rr1.data["DOID:11044"], 0.1,
                         "low raw DOID:4 propagates down")
           
    def test_sum_with_impute(self):
        """sum of values associated with the representation."""  
                
        rr = Representation(dict())                     
        rr.set("DOID:0014667", 1)
        sum1 = rr.sum()        
        rr.impute(self.obo, self.obodef)
        sum2 = rr.sum()        
                
        self.assertEqual(sum1, 1, "value of one phenotype")
        self.assertGreater(sum2, 2, 
                           msg="value for one phenotype+ancestors+defaults")
       
    def test_copy(self):
        """can copy a representation into a new object."""
        
        
        r1 = Representation(self.defaults, name="hello")
        r1.set("abc", 0.5)        
        result = r1.copy()
        
        self.assertEqual(r1.name, result.name)
        self.assertEqual(r1.get("abc"), result.get("abc"))
        result.set("abc", 0.75)
        self.assertEqual(r1.get("abc"), 0.5)
        self.assertEqual(result.get("abc"), 0.75)

