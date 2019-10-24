"""
Tests for contents of ontologies/obo.py
"""

from os.path import join
import tempfile
import unittest
from obo.obo import Obo, MinimalObo
from obo.obo import print_minimal_obo


testdir = join("tests", "testdata")

# an example of a proper ontology file
smallfile = join(testdir, "small.obo")
# all ids appearing in the file
allids = ["DOID:4", "DOID:3653", "DOID:0014667", "DOID:0080015",
          "DOID:11044", "DOID:655", "DOID:0060158", "DOID:3650"]
curids = ["DOID:4", "DOID:0014667", "DOID:0080015",
          "DOID:11044", "DOID:655", "DOID:0060158", "DOID:3650"]
 
# ontology file with alternate ids, obsolete ids
alts_file = join(testdir, "alts.obo")
obsolete_file = join(testdir, "obsolete.obo")

# examples of formating with errors
bad1 = join(testdir, "incomplete_terms.obo")
bad2 = join(testdir, "invalid_is.obo")


class OboBadTests(unittest.TestCase):
    """Test cases for class Obo with with badly formatted obo files"""

    def test_catch_invalid_terms(self):
        """raise exception if a term is not complete."""

        with self.assertRaises(Exception) as e:
            Obo(bad1)
        self.assertTrue("Incomplete" in str(e.exception))

    def test_parse_invalid_relations(self):
        """allow invalid relations during parsing"""

        # bad2 defines two terms, but links to a third that is not defined
        obj = Obo(bad2)
        self.assertEqual(len(obj.terms), 2)
        self.assertEqual(obj.parents("ABC:2"), ())


class OboCoreTests(unittest.TestCase):
    """Test cases for class Obo - core capabilities with minimal data parsing"""

    # load file with small ontology, skip non-essential fields
    obo = MinimalObo(smallfile)

    def test_obo_ids(self):
        """identify ids in a small ontology"""

        self.assertEqual(self.obo.ids(True), allids,
                         "parsing should identify all ids in file")
        self.assertEqual(self.obo.ids(), curids,
                         "parsing should identify all ids in file")

    def test_obo_dealing_with_none(self):
        """object None is handled gracefully via has and valid"""
        
        self.assertFalse(self.obo.has(None))
        self.assertFalse(self.obo.valid(None))     
    
    def test_obo_has(self):
        """Extracting term ids from obo."""

        # test a few keys that are present
        self.assertTrue(self.obo.has("DOID:4"))
        self.assertTrue(self.obo.has("DOID:0014667"))
        self.assertTrue(self.obo.has("DOID:3653"))
        # test a few keys that are not present
        self.assertFalse(self.obo.has("wrongkey"))

    def test_obo_valid(self):
        """Extracting term ids from obo."""

        # test a few keys that are present
        self.assertTrue(self.obo.valid("DOID:4"))
        self.assertTrue(self.obo.valid("DOID:0014667"))
        # test a few keys that are not present
        self.assertFalse(self.obo.valid("wrongkey"))
        # test an item that is present but is obsolete
        self.assertFalse(self.obo.valid("DOID:3653"))

    def test_obo_parents_of_root(self):
        """Getting parent structure."""

        self.assertEqual(self.obo.parents("DOID:4"), (),
                         "root has no parents")

    def test_obo_parents_valid(self):
        """Getting parent structure requires valid term"""

        with self.assertRaises(Exception) as e:
            self.obo.parents("bad_id")
        self.assertTrue("not present" in str(e.exception))

    def test_obo_parents_of_nonroot_nodes(self):
        """Getting parent structure."""

        self.assertEqual(self.obo.parents("DOID:0014667"), ("DOID:4",),
                         "parent is root")
        self.assertEqual(self.obo.parents("DOID:3650"), ("DOID:0060158",),
                         "parent is some other node")

    def test_obo_ancestors(self):
        """Getting ancestors structure."""

        self.assertEqual(sorted(self.obo.ancestors("DOID:3650")),
                         ["DOID:0014667", "DOID:0060158", "DOID:4"],
                         "ancestor traversal to root")

    def test_obo_parents_of_obsolete(self):
        """Getting parent structure."""

        self.assertEqual(self.obo.parents("DOID:3653"), (),
                         "obsolete term here has no parent")

    def test_obo_children_of_root(self):
        """Getting inferred children."""

        self.assertEqual(sorted(self.obo.children("DOID:4")),
                         ["DOID:0014667", "DOID:0080015", "DOID:11044"],
                         "root has two direct children and one indirect")

    def test_obo_children_of_leaf(self):
        """Getting parent structure."""

        self.assertEqual(self.obo.children("DOID:3650"), (), "no children")

    def test_obo_descendants(self):
        """Getting parent structure."""

        self.assertEqual(sorted(self.obo.descendants("DOID:0014667")),
                         ["DOID:0060158", "DOID:3650", "DOID:655"],
                         "descendant traversal to leaves")

    def test_siblings_only_child(self):
        """Getting siblings from root or single child should be empty set."""

        self.assertEqual(self.obo.siblings("DOID:4"), ())
        self.assertEqual(self.obo.siblings("DOID:3650"), ())

    def test_siblings(self):
        """Getting siblings from node with siblings."""

        self.assertEqual(self.obo.siblings("DOID:655"), ("DOID:0060158",))
        self.assertEqual(self.obo.siblings("DOID:0060158"), ("DOID:655",))
        # for the next two, siblings also include nodes using shortcuts to a parent
        self.assertEqual(sorted(self.obo.siblings("DOID:0014667")),
                         ["DOID:0080015", "DOID:11044"])
        self.assertEqual(sorted(self.obo.siblings("DOID:0080015")),
                         ["DOID:0014667", "DOID:11044"])

    def test_sim_simple(self):
        """computing similarity of two terms using ancestors."""

        sim1 = self.obo.sim_jaccard("DOID:0014667", "DOID:0080015")
        self.assertEqual(sim1, 1/3, "both terms are direct children on DOID:4")
        sim2 = self.obo.sim_jaccard("DOID:655", "DOID:0060158")
        self.assertGreater(sim2, sim1, "second set of terms is more specific")
        self.assertLess(sim2, 1, "terms are not identical so <1")

    def test_sim_self(self):
        """computing similarity a term with itself."""

        sim = self.obo.sim_jaccard("DOID:3650", "DOID:3650")
        self.assertEqual(sim, 1, "should be 1 by definition")

    def test_sim_distant(self):
        """computing similarity a term with another distant term."""

        sim = self.obo.sim_jaccard("DOID:3650", "DOID:11044")
        self.assertLess(sim, 0.2, "only root is shared")

    def test_obo_replaced_by_none(self):
        """Getting parent structure."""

        self.assertEqual(self.obo.replaced_by("DOID:4"), None,
                         "active term is not replaced by anything")


class OboMinimalTests(OboCoreTests):
    """Test cases for class Obo, specifically with minimal parsing"""

    def test_minimal_def(self):
        """optional fields do not exist"""

        with self.assertRaises(Exception) as e:
            self.obo.terms["DOID:4"].data
        self.assertTrue("no attribute" in str(e.exception))

    def test_minimal_names(self):
        """Extracting term names from obo."""

        # none of the terms should have ids
        with self.assertRaises(Exception) as e:
            self.obo.name("DOID:4")
        self.assertTrue("no attribute" in str(e.exception))


class OboTests(OboCoreTests):
    """Test cases for class Obo, specifically with non-minimal parsing"""
    
    # load file with small ontology (do not use minimal parsing)
    obo = Obo(smallfile)

    def test_obo_names(self):
        """Extracting term names from obo."""

        self.assertEqual(self.obo.name("DOID:4"), "disease")
        self.assertEqual(self.obo.name("DOID:0014667"),
                         "disease of metabolism")
        self.assertEqual(self.obo.name("DOID:3650"),
                         "lactic acidosis")
        self.assertEqual(self.obo.name("DOID:3653"),
                         "laboratory infectious disease")
        self.assertEqual(self.obo.name("DOID:xxxx"), None)

    def test_obo_def(self):
        """recording def field"""

        val = self.obo.terms["DOID:4"].data["def"]
        self.assertTrue("pathological" in str(val), "definition field exists")

    def test_obo_alts(self):
        """Extracting alternate ids from obo."""

        alts = self.obo.alts("DOID:4")
        self.assertTrue(type(alts) is set)
        self.assertEqual(len(alts), 0)


class OboAltsTests(unittest.TestCase):
    """Testing alternative ids"""
    
    def test_obo_canonical(self):
        """official ids are canonical ids."""

        obo = Obo(alts_file)
        self.assertEqual(obo.canonical("AA:1"), "AA:1")
        self.assertEqual(obo.canonical("AA:2"), "AA:2")
        minobo = MinimalObo(alts_file)
        self.assertEqual(minobo.canonical("AA:1"), "AA:1")
        self.assertEqual(minobo.canonical("AA:2"), "AA:2")

    def test_obo_converts_alts(self):
        """object converts alt_id into canonical ids."""

        obo = Obo(alts_file)
        # the next three ids are defined in the obo
        self.assertEqual(obo.canonical("AA:02"), "AA:2")
        self.assertEqual(obo.canonical("AA:03"), "AA:3")
        self.assertEqual(obo.canonical("AA:003"), "AA:3")
        # second time should use cache
        self.assertEqual(obo.canonical("AA:003"), "AA:3")
        # the next few are not in the obo
        self.assertEqual(obo.canonical("AA:000"), None)
        self.assertEqual(obo.canonical("AA:002"), None)

    def test_minimal_obo_converts_alts(self):
        """converts alt ids into canonical ids - using MinimalObo class."""

        obo = MinimalObo(alts_file)
        # the next three ids are defined in the obo
        self.assertEqual(obo.canonical("AA:02"), "AA:2")
        self.assertEqual(obo.canonical("AA:03"), "AA:3")
        self.assertEqual(obo.canonical("AA:003"), "AA:3")
        # second time should use cache
        self.assertEqual(obo.canonical("AA:003"), "AA:3")
        # the next few are not in the obo
        self.assertEqual(obo.canonical("AA:000"), None)
        self.assertEqual(obo.canonical("AA:002"), None)


class OboObsoleteTests(unittest.TestCase):
    """Testing replacing obsolete ids with canonical ids"""

    obo = Obo(obsolete_file)

    def test_obo_obsolete_detected(self):
        """has() accepts all declared terms, including obsolete"""

        self.assertTrue(self.obo.has("SMALL:3"))
        self.assertTrue(self.obo.valid("SMALL:3"))
        self.assertTrue(self.obo.has("SMALL:5"), "obsolete term is in the obo object")
        self.assertFalse(self.obo.valid("SMALL:5"), "obsolete term is not valid")

    def test_obo_encodes_replacement(self):
        """obsolete terms can have replacements"""

        self.assertEqual(self.obo.replaced_by("SMALL:5"), "SMALL:3")
        self.assertEqual(self.obo.replaced_by("SMALL:3"), None,
                         "valid terms don't have replacements")

    def test_obo_canonical_of_obsolete(self):
        """obsolete ids are canonical ids"""

        self.assertEqual(self.obo.canonical("SMALL:5"), "SMALL:5")


class OboMinimizeTests(unittest.TestCase):
    """Minimizing content of an obo file"""

    def test_minimize_obo(self):
        """output contains a remark line"""
        
        with tempfile.NamedTemporaryFile("wt") as tt:
            with open(tt.name, "wt") as tt_stream:
                print_minimal_obo(smallfile, tt_stream)
            with open(tt.name, "rt") as tt_stream:
                tt_out = tt_stream.readlines()
        self.assertTrue("remark" in str(tt_out))

