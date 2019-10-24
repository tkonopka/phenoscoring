"""
Functions used during build of a Phenoscoring database.
"""

import csv
from db.generator import DBGenerator
from .dbtables import ReferenceConcisePhenotypeTable
from .dbtables import PhenotypeFrequencyTable
from .dbtables import ReferencePriorsTable
from .dbtables import ReferenceNeighborsTable
from .dbhelpers import get_phenotype_priors
from .runner import run_packets
from scoring.representation import Representation
from scoring.referenceset import ReferenceSet
from scoring.referencematrix import ReferenceMatrix
from tools.files import open_file
from .specificity import SpecificityPacket


def make_ref_priors(dbpath, prior=0.01):
    """Create a dict with prior probabilities for all references."""
    
    # scan a db table to identify reference names, assign each a prior value
    result = dict()    
    generator = DBGenerator(ReferenceConcisePhenotypeTable(dbpath))
    for row in generator.next():
        result[row["id"]] = prior        
    result["null"] = max(prior, 1-sum(result.values()))
    return result
    

def fill_ref_priors(dbpath, priors):
    """Fill a table in the db with prior probabilities for references."""
    
    model = ReferencePriorsTable(dbpath)
    for key, value in priors.items():            
        model.add(key, value)
    model.save()
   

def get_reference_neighbors(dbpath, k):
    """create mappings to nearest neighrbors"""

    result = dict()
    refgenerator = DBGenerator(ReferenceNeighborsTable(dbpath))
    for row in refgenerator.next():
        rowid = row["id"]
        if rowid not in result:
            result[rowid] = [""]*k
        rowrank = int(row["rank"])
        if rowrank <= k:
            result[rowid][rowrank-1] = row["neighbor"]
    return result


def get_concise_refdict(dbpath):
    """transfer information on concise reference phenotypes into a dict."""
    
    refdict = dict()
    refdict["null"] = Representation(name="null")
    refgenerator = DBGenerator(ReferenceConcisePhenotypeTable(dbpath))
    for row in refgenerator.next():
        rowid = row["id"]
        if rowid not in refdict:
            refdict[rowid] = Representation(name=rowid)
        refdict[rowid].set(row["phenotype"], row["value"])    
    return refdict
    

def prep_refdict(dbpath, obo, missing_factor):
    """prepare a dictionary of complete reference representations.
    including the null representation.
    """
        
    # read data on reference and phenotypes from the database
    refdict = get_concise_refdict(dbpath)    
    phen_priors = get_phenotype_priors(dbpath)
    missing_factor = min(1, missing_factor)
                
    # impute and adjust values using the ontology     
    for id in refdict.keys():         
        refdict[id].impute(obo, phen_priors)
        # penalize items that were not set to anything explicitly
        for k,v in phen_priors.items():
            if refdict[id].get(k) == v and (v < 1 or id == "null"):
                refdict[id].set(k, v*missing_factor)
        
    return refdict


def dict2referenceset(repdict, feature_ids, priors):
    """create a representation set, using imputation

    :param repdict: a dictionary of Representation objects
    :param feature_ids: list with all features
    :param priors: dict linking name to a prior probability
    :return: ReferenceSet object
    """
    
    result = ReferenceSet(priors, feature_ids)    
    for id, representation in repdict.items():        
        result.add(representation)
    return result
    

def prep_refset(dbpath, obo, ref_priors, missing_factor):
    """read concise references, impute, and compile a refset.

    :param dbpath: path to sqlite db
    :param obo: object of class Obo
    :param ref_priors: dictionary linking references to numbers
    :param missing_factor: number, used to set reference values that are
        not explicitly define
    :return: ReferenceSet object
    """
    
    # read phenotypes from the database    
    refdict = prep_refdict(dbpath, obo, missing_factor)    
    return dict2referenceset(refdict, obo.ids(), ref_priors)


def fill_phenotype_frequency_table(dbpath, datapath):
    """Transfer phenotype frequencies from a file into the database."""
    
    freqtable = PhenotypeFrequencyTable(dbpath)
    with open_file(datapath, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="\"")
        for row in reader:
            freqtable.add(row["phenotype"], float(row["value"]))
    freqtable.save()


def slim_refset(refmatrix):
    """create a smaller refset by eliminating features that are
    equal across all the references."""
    
    keep_features = set()
    for feature in refmatrix.row_names:
        min_val, max_val = refmatrix.range(feature)
        if max_val - min_val > 1e-16:
            keep_features.add(feature)
    return ReferenceMatrix(refmatrix, keep_features)


# ###########################################################################
# Functions called from Phenoscoring.build()

def fill_concise_reference_table(dbpath, datapath):
    """transfer phenotypes from a data file into the database."""
    
    model = ReferenceConcisePhenotypeTable(dbpath)
    with open_file(datapath, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="\"")
        for row in reader:            
            model.add(row["id"], row["phenotype"], float(row["value"]))
    model.save()


def fill_complete_reference_table(dbpath, obo, config):
    """Read raw and create complete and specific representations."""
    
    ref_priors = make_ref_priors(dbpath, config.prior)    
    fill_ref_priors(dbpath, ref_priors) 
           
    missing_factor = config.reference_missing_factor    
    refset = prep_refset(dbpath, obo, ref_priors, missing_factor)        
    k = config.reference_neighbors_k        
    # create a specificity packet for the null model
    refset = ReferenceMatrix(refset, refset.row_names)
    packet_null = SpecificityPacket(dbpath, refset, k)    
    packet_null.add("null")    
    packet_null.run()
    del packet_null
    
    # after recording the null model, perform other computations with
    # a subset of features - slimmed-down version of refset
    refset = slim_refset(refset)    

    # create an array of packets, each containing some references
    n = 1 if refset.n_references() < 64 else config.cores
    packets = [SpecificityPacket(dbpath, refset, k) for _ in range(n)]
    for i, refname in enumerate(refset.columns.keys()):
        if refname == "null":
            continue
        packets[i%n].add(refname)
    run_packets(packets, config.cores)

