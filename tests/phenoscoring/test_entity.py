'''
Tests for contents of phenoscoring/entity.py
'''

import json
import unittest
from os.path import join
from scoring.experiment import Experiment
from phenoscoring.phenotypedatum import PhenotypeDatum
from phenoscoring.entity import Entity, filter_entities, filter_entities_cat
from obo.obo import MinimalObo


class PhenoscoringEntityTests(unittest.TestCase):
    """Test cases for handling phenoscoring entity objects"""

    def test_init(self):
        """init of basic object"""
                
        m = Entity("abc", "genes", marker_id="X:001", marker_symbol="x001")
        self.assertEqual(m.id, "abc")
        self.assertEqual(m.category, "genes")
        self.assertEqual(m.get("marker_id"), "X:001")
        self.assertEqual(m.get("marker_symbol"), "x001")

    def test_keywords(self):
        """initialize with keywords"""
                
        m = Entity("abc", "genes", background="mouse")
        self.assertTrue("background" in m.description)

    def test_get_description_string(self):
        """multiple descriptors set and encoded"""
                        
        m = Entity("abc", "genes", background="mouse")
        m.set_description("allele", "aaa")
        desc_str = m.get("description")
        desc = json.loads(desc_str)
        self.assertEqual(len(desc), 2, "should have background, allele")
        self.assertEqual(desc["background"], "mouse")
        self.assertEqual(desc["allele"], "aaa")

    def test_str(self):
        """object can create a string summary"""
        
        m = Entity("abc", "genes")
        mstr = str(m)        
        self.assertTrue("abc" in mstr)        
     
    def test_has(self):
        """object can identify what keys it has stored"""
        
        m = Entity("abc", "genes", x=0)            
        self.assertTrue(m.has("id"))        
        self.assertTrue(m.has("description"))
        self.assertTrue(m.has("x"))
        self.assertFalse(m.has("y"))
 
    def test_cannot_add_corrupt_data(self):
        """cannot add corrupt data"""
        
        # cannot add a tuple
        with self.assertRaises(Exception):
            self.m.add((1,0.8,0.4))
        # cannot add a plain phenotype
        with self.assertRaises(Exception):
            self.m.add("MP:001")
    
    def test_add_wrong_type(self):
        """cannot add data of wrong class"""
        
        m = Entity("abc", "genes")
        with self.assertRaises(Exception):
            m.add("bob")
    
    def test_add_phenotype_data(self):
        """cannot add corrupt data"""
        
        m = Entity("abc", "genes", marker_id="X:001", marker_symbol="x001")
        self.assertEqual(len(m.data), 0, "initial model has no pheontypes")
        d1 = PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.0555))
        m.add(d1)
        d2 = PhenotypeDatum("MP:007", Experiment(1, 0.456, 0.0234))
        m.add(d2)
        self.assertEqual(len(m.data), 2, "just added two phenotypes")
        # check content of each datum
        pheno_str_0 = str(m.data[0])
        pheno_str_1 = str(m.data[1])
        self.assertTrue("002" in pheno_str_0)
        self.assertTrue("555" in pheno_str_0)
        self.assertTrue("234" in pheno_str_1)                

    def test_equivalent_simple(self):
        """compare entities without description fields."""
        
        m1 = Entity("A", "X", marker_id="m")
        m2 = Entity("A", "X", marker_id="m")
        self.assertTrue(m1.equivalent(m1))
        self.assertTrue(m1.equivalent(m2))
        self.assertTrue(m2.equivalent(m1))

    def test_equivalent_up_to_timestamp(self):
        """compare entities with different timestamps."""
        
        m1 = Entity("A", "X", marker_id="m", timestamp="2017")
        m2 = Entity("A", "X", marker_id="m", timestamp="2018")
        self.assertTrue(m1.equivalent(m2))

    def test_equivalent_different_core_fields(self):
        """compare entities when core fields are different."""
    
        m1 = Entity("A", "X", marker_id="m")
        m2 = Entity("A", "X", marker_id="m", marker_symbol="m")
        self.assertFalse(m1.equivalent(m2))
        self.assertFalse(m2.equivalent(m1))

    def test_equivalent_different_descriptions(self):
        """compare entities with differences in the descriptions object."""
        
        m1, m2 = Entity("A", "X"), Entity("A", "X")
        m2.set_description("background", "Q")
        self.assertFalse(m1.equivalent(m2))
        self.assertFalse(m2.equivalent(m1))

    def test_equivalent_phenotypes(self):
        """entities with different phenotypes cannot be the same."""
        
        m1, m2 = Entity("A", "X"), Entity("A", "X")        
        m1.add(PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05)))
        self.assertFalse(m1.equivalent(m2))
        self.assertFalse(m2.equivalent(m1))

    def test_equivalent_same_phenotypes(self):
        """entities with the same phenotypes are equivalent"""
        
        m1, m2 = Entity("A", "X"), Entity("A", "X")        
        m1.add(PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05)))
        m1.add(PhenotypeDatum("MP:005", Experiment(1, 0.8, 0.05)))
        m2.add(PhenotypeDatum("MP:005", Experiment(1, 0.8, 0.05)))
        m2.add(PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05)))
        self.assertTrue(m1.equivalent(m2))
        self.assertTrue(m2.equivalent(m1))    

    def test_equivalent_different_phenotypes(self):
        """entities with the same phenotypes are equivalent"""
        
        m1, m2 = Entity("A", "X"), Entity("A", "X")        
        # add phenotypes, but two
        m1.add(PhenotypeDatum("MP:001", Experiment(1, 0.8, 0.05)))
        m1.add(PhenotypeDatum("MP:005", Experiment(1, 0.8, 0.05)))
        m2.add(PhenotypeDatum("MP:005", Experiment(1, 0.8, 0.05)))
        m2.add(PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05)))
        self.assertFalse(m1.equivalent(m2))
        self.assertFalse(m2.equivalent(m1))    


class PhenoscoringEntityConsensusTests(unittest.TestCase):
    """Test cases for creating consensus phenotype sets in entity objects"""

    def test_consensus(self):
        """summarize multiple rows of phenotypes using a consensus."""
        
        # first add several pieces of evidence into an entity object
        m = Entity("abc", "genes")
        d1 = PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("MP:007", Experiment(0, 0.4, 0.05))
        d3 = PhenotypeDatum("MP:002", Experiment(1, 0.6, 0.05))
        d4 = PhenotypeDatum("MP:007", Experiment(0, 0.4, 0.15))
        d5 = PhenotypeDatum("MP:009", Experiment(1, 0.6, 0.05))        
        m.add(d1).add(d2).add(d3)
        m.add(d4).add(d5)        
        self.assertEqual(len(m.data), 5)
        
        # check that the consensus contains the input phenotypes
        m.consensus()
        self.assertEqual(len(m.data), 3)
        expected_tpr = {"MP:002": 0.7, "MP:007": 0.4, "MP:009": 0.6}
        expected_fpr = {"MP:002": 0.05, "MP:007": 0.1, "MP:009": 0.05}
        expected_val = {"MP:002": 1, "MP:007": 0, "MP:009": 1}
        for i in range(3):            
            iphen = m.data[i].phenotype
            iexp = m.data[i].experiment
            self.assertEqual(iexp.value, expected_val[iphen])
            self.assertEqual(iexp.tpr, expected_tpr[iphen])
            self.assertEqual(iexp.fpr, expected_fpr[iphen])

    def test_consensus_2(self):
        """summarize multiple rows of phenotypes using a consensus with some discordance."""
        
        # first add several pieces of evidence into an entity object
        m = Entity("abc", "genes")
        d1 = PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("MP:002", Experiment(0, 0.4, 0.05))
        d3 = PhenotypeDatum("MP:002", Experiment(1, 0.6, 0.05))
        m.add(d1).add(d2).add(d3)            
        self.assertEqual(len(m.data), 3)
                
        # check that the consensus matches the inputs
        m.consensus()
        self.assertEqual(len(m.data), 1)
        c1 = m.data[0]                
        iphen = m.data[0].phenotype
        iexp = m.data[0].experiment
        self.assertEqual(iexp.value, 1)
        # the tpr will be lower than (0.6+0.8)/2
        # it should be (0.7*2/3)
        self.assertEqual(iexp.tpr, 0.7*(2/3))
        self.assertEqual(iexp.fpr, 0.05)

    def test_consensus_imputed(self):
        """summarize multiple rows of phenotypes using a consensus, with imputed values"""
        
        # first add several pieces of evidence into an entity object
        m = Entity("abc", "genes")
        d1 = PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05))
        # here add with value between 0 and 1
        d2 = PhenotypeDatum("MP:007", Experiment(0.6, 0.4, 0.05))        
        d3 = PhenotypeDatum("MP:007", Experiment(0.4, 0.6, 0.05))            
        m.add(d1).add(d2).add(d3)            
        self.assertEqual(len(m.data), 3)
        
        # check that the consensus matches the inputs
        m.consensus()
        self.assertEqual(len(m.data), 2)
        c1 = m.data[0]
        c2 = m.data[1]        
        expected_tpr = {"MP:002": 0.8, "MP:007": 0.5}
        expected_fpr = {"MP:002": 0.05, "MP:007": 0.05}
        expected_val = {"MP:002": 1, "MP:007": 0.5}
        for i in range(2):                        
            iphen = m.data[i].phenotype
            iexp = m.data[i].experiment
            self.assertEqual(iexp.value, expected_val[iphen])
            self.assertEqual(iexp.tpr, expected_tpr[iphen])
            self.assertEqual(iexp.fpr, expected_fpr[iphen])

    def test_average(self):
        """summarize phenotypes using an average (consistent values)."""

        # first add several pieces of evidence into an entity object
        m = Entity("abc", "genes")
        d1 = PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("MP:007", Experiment(0, 0.4, 0.05))
        d3 = PhenotypeDatum("MP:002", Experiment(1, 0.6, 0.05))
        d4 = PhenotypeDatum("MP:007", Experiment(0, 0.4, 0.15))
        d5 = PhenotypeDatum("MP:009", Experiment(1, 0.6, 0.05))
        m.add(d1).add(d2).add(d3)
        m.add(d4).add(d5)
        self.assertEqual(len(m.data), 5)

        # check that the average contains all phenotypes
        m.average()
        self.assertEqual(len(m.data), 3)
        expected_tpr = {"MP:002": 0.7, "MP:007": 0.4, "MP:009": 0.6}
        expected_fpr = {"MP:002": 0.05, "MP:007": 0.1, "MP:009": 0.05}
        expected_val = {"MP:002": 1, "MP:007": 0, "MP:009": 1}
        for i in range(3):
            iphen = m.data[i].phenotype
            iexp = m.data[i].experiment
            self.assertEqual(iexp.value, expected_val[iphen])
            self.assertEqual(iexp.tpr, expected_tpr[iphen])
            self.assertEqual(iexp.fpr, expected_fpr[iphen])

    def test_average_2(self):
        """summarize phenotypes using an average (discordant values)."""

        # first add several pieces of evidence into an entity object
        m = Entity("abc", "genes")
        d1 = PhenotypeDatum("MP:002", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("MP:002", Experiment(0, 0.4, 0.05))
        d3 = PhenotypeDatum("MP:002", Experiment(1, 0.6, 0.05))
        m.add(d1).add(d2).add(d3)
        self.assertEqual(len(m.data), 3)

        # check that the consensus matches the inputs
        m.average()
        self.assertEqual(len(m.data), 1)
        self.assertEqual(m.data[0].phenotype, "MP:002")
        iexp = m.data[0].experiment
        self.assertGreater(iexp.value, 0)
        self.assertAlmostEqual(iexp.tpr, (0.8+0.0+0.6)/3)
        self.assertAlmostEqual(iexp.fpr, 0.05)


class PhenoscoringEntityTrimmingTests(unittest.TestCase):
    """Test cases for trimming phenotypes out of entity objects"""

    obofile = join("tests", "testdata", "small.obo")
    obo = MinimalObo(obofile)
        
    def test_trim_nothing(self):
        """trimming does nothing if there is nothing to do."""
        
        m = Entity("abc", "genes")        
        d1 = PhenotypeDatum("DOID:3650", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("DOID:11044", Experiment(1, 0.8, 0.05))
        m.add(d1).add(d2)
        
        self.assertEqual(len(m.data), 2)
        m.trim_ancestors(self.obo)
        self.assertEqual(len(m.data), 2)
        
    def test_trim_easy(self):
        """trimming eliminates root node."""
        
        m = Entity("abc", "genes")        
        d1 = PhenotypeDatum("DOID:4", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("DOID:11044", Experiment(1, 0.8, 0.05))
        m.add(d1).add(d2)
        
        self.assertEqual(len(m.data), 2)
        m.trim_ancestors(self.obo)
        self.assertEqual(len(m.data), 1)
        self.assertEqual(m.data[0].phenotype, "DOID:11044")

    def test_trim_easy_keep(self):
        """trimming does not eliminate node if ask to keep."""
        
        m = Entity("abc", "genes")        
        d1 = PhenotypeDatum("DOID:4", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("DOID:11044", Experiment(1, 0.8, 0.05))
        m.add(d1).add(d2)
        
        self.assertEqual(len(m.data), 2)
        m.trim_ancestors(self.obo, set(["DOID:4"]))
        self.assertEqual(len(m.data), 2)

    def test_trim_medium(self):
        """trimming eliminates when when there are several leafs."""
        
        m = Entity("abc", "genes")        
        d1 = PhenotypeDatum("DOID:4", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("DOID:11044", Experiment(1, 0.8, 0.05))
        d3 = PhenotypeDatum("DOID:0080015", Experiment(1, 0.8, 0.05))
        d4 = PhenotypeDatum("DOID:655", Experiment(1, 0.8, 0.05))
        m.add(d1).add(d2).add(d3).add(d4)
        
        self.assertEqual(len(m.data), 4)
        m.trim_ancestors(self.obo)
        self.assertEqual(len(m.data), 2)
        result = set([_.phenotype for _ in m.data])
        self.assertEqual(result, set(["DOID:11044", "DOID:655"]))

    def test_trim_leave_highvalue(self):
        """trimming eliminates when when there are several leafs."""
        
        m = Entity("abc", "genes")        
        d1 = PhenotypeDatum("DOID:4", Experiment(1, 0.8, 0.05))
        d2 = PhenotypeDatum("DOID:11044", Experiment(0.5, 0.8, 0.05))
        d3 = PhenotypeDatum("DOID:0080015", Experiment(1, 0.8, 0.05))
        d4 = PhenotypeDatum("DOID:655", Experiment(1, 0.8, 0.05))
        m.add(d1).add(d2).add(d3).add(d4)
        
        self.assertEqual(len(m.data), 4)
        m.trim_ancestors(self.obo)
        self.assertEqual(len(m.data), 3)
        result = set([_.phenotype for _ in m.data])
        self.assertEqual(result, set(["DOID:11044", "DOID:655", "DOID:0080015"]))


class PhenoscoringEntityFilterTests(unittest.TestCase):
    """Test cases for filtering phenoscoring entity objects"""
    
    def test_filter_none(self):
        
        source = []            
        source.append(Entity("o1", "X"))
        source.append(Entity("o2", "Y"))
        result = filter_entities(source, None)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "o1")
        
    def test_filter_category_none(self):
        
        source = []            
        source.append(Entity("o1", "X"))
        source.append(Entity("o2", "Y"))
        source.append(Entity("o3", "X"))
        source.append(Entity("o4", "Z"))
        result = filter_entities_cat(source, None)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].id, "o1")
        
    def test_filter_category(self):
        
        source = []            
        source.append(Entity("o1", "X"))
        source.append(Entity("o2", "Y"))
        source.append(Entity("o3", "X"))
        source.append(Entity("o4", "Z"))
        result = filter_entities_cat(source, set(["X", "Z"]))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].id, "o1")
        
    def test_filter_from_dict(self):
        
        source = dict()            
        source["o1"] = Entity("o1", "X")
        source["o2"] = Entity("o2", "Y")
        source["o3"] = Entity("o3", "X")
        source["o4"] = Entity("o4", "Z")
        result = filter_entities_cat(source, set(["X", "Z"]))
        self.assertEqual(len(result), 3)
        self.assertEqual(result["o1"].id, "o1")
