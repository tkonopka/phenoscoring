"""
Tests for contents of scoring/referenceset.py and referencematrix.py
"""


import gzip
import json
import unittest
from collections import OrderedDict
from os.path import join, exists
from scoring.referenceset import ReferenceSet
from scoring.referencematrix import ReferenceMatrix 
from scoring.representation import Representation
from obo.obo import MinimalObo
from tests.testhelpers import remove_if_exists


testfeatures = ["a", "b", "c", "d", "e"]

# define an ontology for these tests
testdir = join("tests", "testdata")
obofile = join(testdir, "small.obo")
obo = MinimalObo(obofile)
obodefaults = dict.fromkeys(obo.ids(), 0.0)

# another ontology Y.obo
Yfile = join(testdir, "Y.obo")
Yobo = MinimalObo(Yfile)
Ydefaults = dict.fromkeys(Yobo.ids(), 0.2)            
null_defaults = dict.fromkeys(Yobo.ids(), 0.001)


# set of features for this set of tests
defvals = dict.fromkeys(testfeatures, 0.2)
zerovals = dict.fromkeys(testfeatures, 0.0)
nanvals = dict.fromkeys(testfeatures, float("nan"))

# prefix for output files
outfile = join(testdir, "small_out")
    

class ReferenceSetTests(unittest.TestCase):
    """Test cases for class ReferenceSet."""

    def tearDown(self):
        """Perhaps remove some temporary files."""
        
        remove_if_exists(outfile+"_row_priors.json")        
        remove_if_exists(outfile+"_column_priors.json")
        remove_if_exists(outfile+"_data.tsv.gz")

    def test_empty_representation(self):
        """creating a new set of references."""  

        rs = ReferenceSet(dict(refA=0.5, refB=1), ids=obo.ids())
        num_ids = len(obo.ids())
        self.assertEqual(len(rs.data), 2, "refset should allocate memory")
        self.assertEqual(len(rs.data[0]), num_ids)
        self.assertEqual(len(rs.data[1]), num_ids)
    
    def test_add_raises(self):
        """adding an unexpected piece of data raises exceptions."""  
        
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())
        with self.assertRaises(Exception):
            rs.add(5)
        
        with self.assertRaises(Exception):
            rs.add(dict.fromkeys(["DOID:0014667", "DOID:0080015"], 0))
    
    def test_add_incrementally(self):
        """transferring values into a representation set."""  
                        
        r1 = Representation(name="refA").set("DOID:0014667", 0.4)                
        r1.impute(obo, obodefaults)        
     
        r2 = Representation(name="refB").set("DOID:0080015", 0.6)        
        r2.impute(obo, obodefaults)
        
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())        
        rs.add(r1).add(r2)        
        
        self.assertEqual(rs.get("DOID:0014667", "refA"), 0.4, 
                         "refset should contain inserted data")                         
        self.assertEqual(rs.get("DOID:0080015", "refB"), 0.6, 
                         "refset should contain inserted data")                         
        self.assertEqual(rs.get("DOID:4", "refB"), 0.6, 
                         "refset should contain imputed data")                         

    def test_get_reference(self):
        """extract one reference from a representation set."""
        
        r1 = Representation(name="refA").set("DOID:0014667", 0.4)                
        r1.impute(obo, obodefaults)                
        r2 = Representation(name="refB").set("DOID:0080015", 0.6)        
        r2.impute(obo, obodefaults)
        
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())        
        rs.add(r1).add(r2)        
        
        r3 = rs.get_representation("refA")                
        self.assertTrue(r3.equal(r1))            

    def test_fetch_names(self):
        """Can retrieve names of all references."""
        
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())
        self.assertEqual(sorted(rs.names()), ["refA", "refB"])

    def test_add_without_name_raises(self):
        """adding a representation without a name raises exceptions."""  
                                
        r1 = Representation().set("DOID:0014667", 0.4)                                 
        rs  = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())
        with self.assertRaises(Exception):            
            rs.add(r1)

    def test_add_new_reference(self):
        """adding a representation without a name raises exceptions."""  
                                
        r1 = Representation(name="refC").set("DOID:0014667", 0.4)                                     
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())
        
        with self.assertRaises(Exception):
            rs.add(r1)

    def test_learn_from_obo(self):
        """create parents_of tuples for all features"""

        r1 = Representation(name="refA").set("DOID:0014667", 0.4)
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())
        rs.add(r1)
        self.assertEqual(rs.parents, None)
        rs.learn_obo(obo)
        self.assertEqual(len(rs.parents), len(obo.ids()))

    def test_subset(self):
        """make a refset smaller by ignoring some features."""
        
        # create a reference set
        rs = ReferenceSet(OrderedDict(refA=0.5, refB=0.5), ids=testfeatures,
                          row_priors=zerovals)
        
        # add some data to the two representations
        r1 = Representation(name="refA")
        r1.set("a", 0.1).set("b", 0.2).set("c", 0.3).set("d", 0.4)                                     
        r2 = Representation(name="refB")
        r2.set("c", 0.6).set("d", 0.7).set("e", 0.8)        
        rs.add(r1).add(r2)
        # manually create arrays with the reference set data
        expected_raw_A = [0.1, 0.2, 0.3, 0.4, 0.0]
        expected_raw_B = [0.0, 0.0, 0.6, 0.7, 0.8]
        self.assertTrue(list(rs.data[0]), expected_raw_A)
        self.assertTrue(list(rs.data[1]), expected_raw_B)
        # subset to a smaller number of features
        # myids - here c is repeated twice, z is not in the original features
        myids = ["e", "c", "a", "z", "c"]
        rs = ReferenceMatrix(rs, myids)        
        # check new shape (three features and two references)
        self.assertEqual(len(rs.rows), 3)
        self.assertEqual(len(rs.row_names), 3)
        self.assertEqual(rs.data.shape, (3,2))
        # check that the relevant rows are present
        result = set(rs.rows.keys())
        expected = set(myids)
        expected.remove("z")
        self.assertEqual(result, expected)
        # check data subset in output
        output_A = [0.1, 0.3, 0.0]
        output_B = [0.0, 0.6, 0.8]
        self.assertEqual(sum(rs.data[:,0]), sum(output_A))
        self.assertEqual(sum(rs.data[:,1]), sum(output_B))       

    def test_scores_bad_input(self):
        """inference function should raise with bad input."""
        
        # model is empty
        rs  = ReferenceSet(dict(refA=0.5, refB=0.5), ids=obo.ids())
        with self.assertRaises(Exception):
            rs.inference("refA")

    def test_prep_row_priors(self):
        """prepare row priors."""
        
        # let ref universe have two annotations and one null
        refA = Representation(data=dict(a=1), name="refA")
        refA.defaults(zerovals)
        refB = Representation(data=dict(a=1, b=0.8), name="refB")
        refB.defaults(zerovals)
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=zerovals.keys())
        rs.add(refA).add(refB)
        # compute feature priors
        rs.prep()            
        # row_priors should gain key/values for all features
        expected_features = set(zerovals.keys())        
        self.assertEqual(set(rs.row_names), expected_features)
        # features declared in representations should get reasonable priors
        a_index = rs.rows["a"]
        b_index = rs.rows["b"]
        d_index = rs.rows["d"]
        self.assertEqual(rs.row_priors[a_index], 1, "refA and refB both have a")
        self.assertEqual(rs.row_priors[b_index], 0.4, "only refB has b, so 0.8/2")
        self.assertEqual(rs.row_priors[d_index], 0.2, "value is 1/num features")


class ReferenceSetInferenceGeneralTests(unittest.TestCase):
    """Test cases for class ReferenceSet - computing inference"""

    def tearDown(self):
        """Perhaps remove some temporary files."""

        remove_if_exists(outfile+"_row_priors.json")
        remove_if_exists(outfile+"_column_priors.json")
        remove_if_exists(outfile+"_data.tsv.gz")

    def test_inference_chain(self):
        """compute an inference chain."""
                
        # create a reference set 
        refA = Representation(name="refA")
        refA.set("Y:002", 1).impute(Yobo, Ydefaults)
        refB = Representation(name="refB")
        refB.set("Y:001", 1).impute(Yobo, Ydefaults)
        rs = ReferenceSet(dict(refA=0.5, refB=0.5), ids=Yobo.ids(),
                          row_priors=Ydefaults)
        rs.add(refA).add(refB)
        rs.learn_obo(Yobo)
                    
        # compute a chain object explaining scoring steps
        chain = rs.inference_chain(refA, "refB", verbose=True)        
        self.assertEqual(chain.__dict__["model"], "refA")
        self.assertEqual(chain.__dict__["reference"], "refB")
        self.assertGreater(len(chain.data), 2, 
                           "data chain should describe multiple features")
        self.assertTrue("background" in chain.data[0].__dict__, 
                        "chain data have comparison information")
        self.assertTrue("result" in chain.data[0].__dict__, 
                        "chain data have TP/FP/etc codes")

    def test_positive_parent(self):
        """fetching a parent term that has a positive value."""
        
        rs = ReferenceSet(dict(refA=0.5), ids=Yobo.ids(),
                           row_priors=Ydefaults)
        refA = Representation(name="refA")
        refA.set("Y:002", 0.5).set("Y:005", 1).impute(Yobo, Ydefaults)        
        rs.add(refA)
        rs.learn_obo(Yobo)

        refAindex = rs.columns["refA"]        
        self.assertEqual(rs._positive_ancestor(refAindex, rs.rows["Y:002"]), 
                         rs.rows["Y:002"],
                         "Y2 is itself is positive")        
        self.assertEqual(rs._positive_ancestor(refAindex, rs.rows["Y:007"]), 
                         rs.rows["Y:002"],
                         "Y2 is immediate parent of Y7")
        self.assertEqual(rs._positive_ancestor(refAindex, rs.rows["Y:006"]), 
                         rs.rows["Y:005"],
                         "Y5 is immediate parent of Y6")

    def test_positive_parent_multi(self):
        """fetching a parent term when terms have multiple parents."""
        
        # load an ontology in which Y7 is connected to both Y2 and Y1
        Yfile = join(testdir, "Ymulti.obo")
        Yobo = MinimalObo(Yfile)
        Ydefaults = dict.fromkeys(Yobo.ids(), 0.0001)
        Ydefaults["Y:003"] = 0.0002
        Ydefaults["Y:005"] = 0.0002
        # make slight variations of representations            
        rs  = ReferenceSet(dict(refA=0.5, refB=0.5), ids=Yobo.ids(),
                           row_priors=Ydefaults)
        refA = Representation(name="refA")
        refA.set("Y:002", 0.5).set("Y:005", 1).impute(Yobo, Ydefaults)
        refB = Representation(name="refB")
        refB.set("Y:001", 0.5).impute(Yobo, Ydefaults)
        rs.add(refA).add(refB)
        rs.learn_obo(Yobo)

        self.assertEqual(rs._positive_ancestor(rs.columns["refA"], rs.rows["Y:007"]), 
                         rs.rows["Y:002"],
                         "Y2 is a positive ancestor")
        self.assertEqual(rs._positive_ancestor(rs.columns["refB"], rs.rows["Y:007"]), 
                         rs.rows["Y:001"],
                         "Y1 is a positive immediate parent")

    def test_str(self):
        """getting a quick string with the content."""
        
        rs = ReferenceSet(dict(null=0.7, refA=0.15, refB=0.15), 
                          ids=zerovals.keys())        
        result = str(rs)
        self.assertTrue("refA" in result)
        self.assertFalse("hello" in result)
         

class ReferenceMatrixTests(unittest.TestCase):
    """Test cases for computing average representation of neighbors"""

    def setUp(self):
        """prepare a reference set with a few references."""

        self.refnull = Representation(data=null_defaults, name="null")
        self.refA = Representation(data=Ydefaults, name="refA")
        self.refA.set("Y:004", 1)        
        self.refB = Representation(data=Ydefaults, name="refB")
        self.refB.set("Y:004", 1).set("Y:001", 0.6).set("Y:003", 0.5)        
        self.refC = Representation(data=Ydefaults, name="refC")
        self.refC.set("Y:004", 1).set("Y:001", 0.5)        
        self.refD = Representation(data=Ydefaults, name="refD")
        self.refD.set("Y:004", 0.1) 
        ref_priors = dict(null=0.1, refA=0.1, refB=0.1, refC=0.1, refD=0.1)       
        rs = ReferenceSet(ref_priors, ids=Ydefaults.keys())
        rs.add(self.refnull)
        rs.add(self.refA).add(self.refB)
        rs.add(self.refC).add(self.refD)        
        self.rm = ReferenceMatrix(rs, list(Ydefaults.keys()))

    def test_neighbors_cosine(self):
        """identify neighboring/similar references."""

        indexes = dict()
        for _ in ["refA", "refB", "refC", "refD"]:
            indexes[_] = self.rm.columns[_]

        result = self.rm.nearest_neighbors("refC", 2)
        expected = ["refB", "refA"]
        self.assertEqual(result, expected)

    def test_average(self):
        """compute an average of several representations."""
        
        result = self.rm.get_average(["refB", "refC"])
        self.assertAlmostEqual(result.get("Y:004"), 1.0)
        self.assertAlmostEqual(result.get("Y:001"), 0.55)
        self.assertAlmostEqual(result.get("Y:007"), Ydefaults["Y:007"])


class ReferenceSetWriteTests(unittest.TestCase):
    """Test cases for class ReferenceSet."""

    def setUp(self):
        """prepare a reference set with some data."""
        
        # let ref universe have two annotations and one null
        refA = Representation(data=dict(a=1, b=0.8), name="refA")
        refA.defaults(zerovals)
        refB = Representation(data=dict(a=1, d=0.2), name="refB")
        refB.defaults(zerovals)
        self.rs = ReferenceSet(dict(null=0.7, refA=0.15, refB=0.15), 
                          ids=zerovals.keys())
        self.rs.add(refA).add(refB)        
        self.rs.prep()

    def tearDown(self):
        """Perhaps remove some temporary files."""
        
        remove_if_exists(outfile+"_row_priors.json")        
        remove_if_exists(outfile+"_column_priors.json")
        remove_if_exists(outfile+"_data.tsv.gz")

    def test_write(self):
        """Writing a summary of the data to disk files"""  

        self.rs.save(outfile)

        row_file = join(outfile+"_row_priors.json")
        col_file = join(outfile+"_column_priors.json")
        data_file = join(outfile+"_data.tsv.gz")
        self.assertTrue(exists(row_file))
        self.assertTrue(exists(col_file))
        self.assertTrue(exists(data_file))
        
        # load files and check expected structure
        with open(row_file, "r") as f:
            row_content = json.load(f)
        with open(col_file, "r") as f:
            col_content = json.load(f)
        with gzip.open(data_file, "rt") as f:
            data_content = f.readlines()
                
        self.assertEqual(len(row_content), len(zerovals))
        self.assertEqual(len(col_content), 3, "null, refA, refB")
        self.assertEqual(len(data_content), len(zerovals)+1)
        self.assertEqual(data_content[0], "\tnull\trefA\trefB\n")

    def test_write_header(self):
        """Writing a data matrix with first column name"""  
        
        # perform a save with a name in the first column
        self.rs.save(outfile, "phenotype")
        
        data_file = join(outfile+"_data.tsv.gz")
        self.assertTrue(exists(data_file))
        
        with gzip.open(data_file, "rt") as f:
            data_content = f.readlines()
        
        self.assertEqual(len(data_content), len(zerovals)+1)
        self.assertEqual(data_content[0], "phenotype\tnull\trefA\trefB\n")


class ReferenceSetInferencePositivesTests(unittest.TestCase):
    """Test cases for computing inference scores using ReferenceSet."""
    
    @classmethod
    def setUpClass(cls):        
        # set some phenotype priors that are nonzero
        cls.priors = dict()
        cls.priors["Y:004"] = 0.66
        cls.priors["Y:005"] = cls.priors["Y:006"] = 0.25
        cls.priors["Y:003"] = 0.66
        cls.priors["Y:001"] = cls.priors["Y:002"] = 0.33
        cls.priors["Y:007"] = cls.priors["Y:008"] = 0.25
        # create reference set with some strong phenotypes
        cls.refnull = Representation(name="null")
        cls.refA = Representation(name="refA")
        cls.refB = Representation(name="refB")
        cls.refA.set("Y:002", 1).impute(Yobo, cls.priors)
        cls.refB = Representation(name="refB")
        cls.refB.set("Y:001", 1).impute(Yobo, cls.priors)
        # reset missing phenotypes to smaller-than-prior 
        for k,v in cls.priors.items():
            if cls.refA.get(k) == v:
                cls.refA.set(k, v/2)
            if cls.refB.get(k) == v:
                cls.refB.set(k, v/2)            
        cls.rs = ReferenceSet(dict(null=0.3, refA=0.3, refB=0.3),
                              ids=Yobo.ids(), row_priors=cls.priors)
        cls.rs.add(cls.refnull).add(cls.refA).add(cls.refB)
        cls.rs.learn_obo(Yobo)
    
    def test_bg_verbose(self):
        """compute with background value leaves score the same."""
        
        neutral = Representation(name="TP")
        neutral.set("Y:004", self.priors["Y:004"])
        chain = self.rs.inference_chain(neutral, "refA", verbose=True)                        
        chain.evaluate()
        self.assertEqual(chain.posterior, chain.prior) 
    
    def test_bg_nonverbose(self):
        """compute with background value leaves score the same."""

        neutral = Representation(name="TP")
        neutral.set("Y:004", self.priors["Y:004"])
        chain = self.rs.inference_chain(neutral, "refA", verbose=False)                        
        chain.evaluate()
        self.assertEqual(chain.posterior, chain.prior) 
    
    def test_TP(self):
        """update based on TP phenotype increases score"""

        # create a model that matches a phenotype TP
        TP = Representation(name="TP").set("Y:002", 1)
                
        # construct an inference chain explaining        
        chain = self.rs.inference_chain(TP, "refA", verbose=True)                
        self.assertEqual(len(chain.data), 1, "one phenotype to compare")
        
        # calculate probabilities
        chain.evaluate()
        self.assertGreater(chain.posterior, chain.prior, 
                           "TP should increase overall prob")            
    
    def test_FP3_with_null(self):        
        """FP3 is phenotype with a fairly high prior."""
                
        FP3 = Representation(name="model").set("Y:003", 0.9)        
        chain3 = self.rs.inference_chain(FP3, "null", verbose=True)       
        chain3.evaluate()        
        self.assertLessEqual(chain3.posterior, chain3.prior)        
    
    def test_FP2_with_null(self):        
        """FP2 is phenotype with a moderate high prior."""
                
        FP2 = Representation(name="model").set("Y:002", 0.9)                         
        chain2 = self.rs.inference_chain(FP2, "null")       
        chain2.evaluate()
        self.assertLessEqual(chain2.posterior, chain2.prior)

    def test_FP7_with_null(self):        
        """FP7 is phenotype with a low prior."""
                
        FP7 = Representation(name="model").set("Y:007", 0.9)
        chain7 = self.rs.inference_chain(FP7, "null", verbose=True)       
        chain7.evaluate()
        self.assertLess(chain7.posterior, chain7.prior,
                        "must be strictly lower")

    def test_FP_same_parent(self):
        """various FPs to same parent score the same"""
                
        # both models are FP using children of a refA phenotype
        FP_close = Representation(name="close").set("Y:007", 0.9)
        FP_far = Representation(name="far").set("Y:008", 0.9)
        chain_close = self.rs.inference_chain(FP_close, "refA", verbose=True)
        chain_far = self.rs.inference_chain(FP_far, "refA", verbose=True)
        chain_close.evaluate()
        chain_far.evaluate()
        self.assertEqual(chain_close.posterior, chain_far.posterior)                           

    def test_FP_close_vs_null(self):
        """various FP to a nontrivial phenotype is better than with null"""
                
        FP = Representation(name="model").set("Y:007", 0.3)        
        chain_null = self.rs.inference_chain(FP, "null", verbose=True, fp_penalty=0.2)
        chain_null.evaluate_inference()
        chain_ref = self.rs.inference_chain(FP, "refA", verbose=True, fp_penalty=0.2)
        chain_ref.evaluate_inference()
        self.assertGreater(chain_ref.posterior, chain_null.posterior)

    def test_FP_can_increase(self):
        """FP can in principle yield greater score"""
                        
        # make a new reference set with different priors
        priors2 = self.priors.copy()
        priors2["Y:002"] = 0.1 
        rs2 = ReferenceSet(dict(null=0.4, refA=0.3, refB=0.3),
                           ids=Yobo.ids(), row_priors=priors2)
        rs2.add(self.refnull).add(self.refA).add(self.refB)
        rs2.learn_obo(Yobo)

        FP = Representation(name="model").set("Y:002", 0.2)                
        chain = rs2.inference_chain(FP, "refB", verbose=True, fp_penalty=1)
        chain.evaluate_inference()
        self.assertGreater(chain.posterior, chain.prior)
    
    def test_FP_with_fp_penalty(self):
        """FP increases more with lower fp_penalty"""
                        
        # make a new reference set with different priors
        priors2 = self.priors.copy()
        priors2["Y:003"] = 0.4
        priors2["Y:002"] = 0.15
        priors2["Y:007"] = 0.1
        rs2 = ReferenceSet(dict(null=0.4, ref=0.3),
                           ids=Yobo.ids(), row_priors=priors2)
        ref = Representation(name="ref")
        ref.set("Y:001", 1).impute(Yobo, priors2)
        ref.set("Y:007", priors2["Y:007"]/2)            
        rs2.add(self.refnull).add(ref)
        rs2.learn_obo(Yobo)
        
        FP = Representation(name="model").set("Y:007", 0.35)                
        chain1 = rs2.inference_chain(FP, "ref", verbose=True, fp_penalty=0.1)        
        chain1.evaluate_inference()        
        self.assertGreater(chain1.posterior, chain1.prior)            
        chain2 = rs2.inference_chain(FP, "ref", verbose=True, fp_penalty=1)        
        chain2.evaluate_inference()        
        self.assertLess(chain2.posterior, chain1.posterior)
    
    def test_FP_different_parent(self):
        """FPs to closer parents score better than farther parents"""
                
        # Y:007 is one away from refA and two steps away 
        FP = Representation(name="close").set("Y:007", 0.9)
        chain_close = self.rs.inference_chain(FP, "refA", verbose=True)
        chain_close.evaluate_inference()        
        chain_far = self.rs.inference_chain(FP, "refB", verbose=True)                
        chain_far.evaluate_inference()        
        self.assertGreater(chain_close.posterior, chain_far.posterior)
    
    def test_TP_scores_better_than_FP(self):
        """FPs must score lower than TPs"""
                
        # make a new reference set with different (lower) priors 
        priors2 = self.priors.copy()
        priors2["Y:002"] = 0.55
        priors2["Y:007"] = 0.15
        rs2 = ReferenceSet(dict(null=0.4, refA=0.3, refB=0.3),
                           ids=Yobo.ids(), row_priors=priors2)
        rs2.add(self.refnull).add(self.refA).add(self.refB)
        rs2.learn_obo(Yobo)
        
        # compare with refA, which has Y:002 equal to 1
        FP = Representation(name="FP").set("Y:007", 1)
        chain_FP = rs2.inference_chain(FP, "refA", verbose=True, fp_penalty=2)
        chain_FP.evaluate_inference()
        TP = Representation(name="TP").set("Y:002", 1)
        chain_TP = rs2.inference_chain(TP, "refA", verbose=True)        
        chain_TP.evaluate_inference()
        
        self.assertGreaterEqual(chain_TP.posterior, chain_FP.posterior)


class ReferenceSetInferenceNegativesTests(unittest.TestCase):
    """Test cases for computing inference scores using ReferenceSet."""

    @classmethod
    def setUpClass(cls):        
        # create with sibling diseases Y:002 and Y:001 are siblings
        # set some phenotype priors that are nonzero
        cls.priors = dict()
        cls.priors["Y:004"] = 0.66
        cls.priors["Y:005"] = cls.priors["Y:006"] = 0.25
        cls.priors["Y:003"] = 0.66
        cls.priors["Y:001"] = cls.priors["Y:002"] = 0.33
        cls.priors["Y:007"] = cls.priors["Y:008"] = 0.25
                
        cls.refnull = Representation(name="null")
        # refA has a negative phenotype
        cls.refA = Representation(name="refA")
        cls.refA.set("Y:002", 0.1).impute(Yobo, cls.priors)
        # refB has a negative and positive phenotypes
        cls.refB = Representation(name="refB")
        cls.refB.set("Y:001", 0.01).set("Y:006", 0.8).impute(Yobo, cls.priors)
        # refB2 has a weaker positive phenotype
        cls.refB2 = Representation(name="refB2")
        cls.refB2.set("Y:001", 0.1).set("Y:006", 0.5).impute(Yobo, cls.priors)
        cls.rs = ReferenceSet(dict(null=0.4, refA=0.3, refB=0.3, refB2=0.3), 
                              ids=Yobo.ids(), row_priors=cls.priors)
        cls.rs.add(cls.refnull).add(cls.refA).add(cls.refB).add(cls.refB2)
        cls.rs.learn_obo(Yobo)

    def test_TN(self):
        """TN should increase overall score"""
        
        TN = Representation(name="model").set("Y:007", 0.01)        
                
        # construct an inference chain         
        chain = self.rs.inference_chain(TN, "refA", verbose=True)
        self.assertEqual(len(chain.data), 1, "one phenotype to compare")            
        
        # calculate probabilities
        chain.evaluate_inference()
        self.assertGreater(chain.posterior, chain.prior)

    def test_TN_strong_ref(self):
        """TN against strong negative ref should increase overall score"""

        # create two models that matches ref phenotypes TN
        TNA = Representation(name="model").set("Y:002", 0.01)        
        TNB = Representation(name="model").set("Y:001", 0.01)
        
        # construct inference chain that give TNs         
        chainA = self.rs.inference_chain(TNA, "refA", verbose=True)
        chainA.evaluate_inference()        
        chainB = self.rs.inference_chain(TNB, "refB", verbose=True)
        chainB.evaluate_inference()        
        
        # both comparisons should lead to higher scores                    
        self.assertGreater(chainA.posterior, chainA.prior)
        self.assertGreater(chainB.posterior, chainB.prior)
        # second comparison should end higher because refB is more strong negative
        self.assertGreater(chainB.posterior, chainA.posterior)

    def test_TN_strong_model(self):
        """TN against strong negative ref should increase overall score"""

        # create two models that matches ref phenotypes TN
        TNA = Representation(name="model").set("Y:002", 0.01)        
        TNB = Representation(name="model").set("Y:002", 0.001)
        
        # construct inference chains that give TNs         
        chainA = self.rs.inference_chain(TNA, "refA", verbose=True)
        chainA.evaluate_inference()            
        chainB = self.rs.inference_chain(TNB, "refA", verbose=True)
        chainB.evaluate_inference()        
        
        # both comparisons should lead to higher scores                    
        self.assertGreater(chainA.posterior, chainA.prior)
        self.assertGreater(chainB.posterior, chainB.prior)
        # second comparison should end higher because refB is more strong negative
        self.assertGreater(chainB.posterior, chainA.posterior)

    def test_AN_leaves_score_unchanged(self):
        """negative compared to prior leaves score unchanged """
                
        AN = Representation(name="FN").set("Y:005", 0.01)
        chain_AN = self.rs.inference_chain(AN, "refA", verbose=True)
        chain_AN.evaluate_inference()        
        self.assertAlmostEqual(chain_AN.posterior, chain_AN.prior)

    def test_FN_can_decrease_score(self):
        """negative compared to positive decreases score"""
                
        FN = Representation(name="FN").set("Y:005", 0.01)
        chain_FN = self.rs.inference_chain(FN, "refB", verbose=True)
        chain_FN.evaluate_inference()        
        self.assertLess(chain_FN.posterior, chain_FN.prior)

    def test_FN_decrease_scales_with_model(self):
        """negative compared to positive decreases score"""
                
        FN1 = Representation(name="FN").set("Y:005", 0.01)
        FN2 = Representation(name="FN").set("Y:005", 0.001)
        chain_FN1 = self.rs.inference_chain(FN1, "refB", verbose=True)
        chain_FN1.evaluate_inference()        
        chain_FN2 = self.rs.inference_chain(FN2, "refB", verbose=True)
        chain_FN2.evaluate_inference()
                
        # both models should decrease score
        self.assertLess(chain_FN1.posterior, chain_FN1.prior)
        self.assertLess(chain_FN2.posterior, chain_FN2.prior)
        # second model should decrease more
        self.assertLess(chain_FN2.posterior, chain_FN1.posterior)

    def test_FN_decrease_scaled_with_ref(self):
        """negative compared to positive decreases score"""
                
        FN1 = Representation(name="FN1").set("Y:005", 0.01)
        chain_FN1 = self.rs.inference_chain(FN1, "refB", verbose=True)
        chain_FN1.evaluate_inference()        
        FN2 = Representation(name="FN2").set("Y:005", 0.01)
        chain_FN2 = self.rs.inference_chain(FN2, "refB2", verbose=True)
        chain_FN2.evaluate_inference()
        
        # both cases should lead to decrease in score        
        self.assertLess(chain_FN1.posterior, chain_FN1.prior)
        self.assertLess(chain_FN2.posterior, chain_FN2.prior)
        # the decrease should be steeper in FN1 because refB positive is stronger
        self.assertLess(chain_FN1.posterior, chain_FN2.posterior)

