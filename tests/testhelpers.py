'''Helper functions used in several test modules.

@author: Tomasz Konopka
'''

import os.path
from phenoscoring.phenoscoringconfig import PhenoscoringConfig


# ###########################################################################
# Helper functions to clean up after tests


def remove_if_exists(filepath):
    """remove a single file if it exists."""
    
    if os.path.exists(filepath):
        os.remove(filepath)


def remove_db(dbpath):
    """remove sqlite, json, and tsv files."""
    
    remove_if_exists(dbpath)
    remove_dbaux(dbpath)    
    

def remove_dbaux(dbpath):
    """remove auxiliary files associated with a db."""
    
    prefix = dbpath[:-7]
    remove_if_exists(prefix+"-references_column_priors.json")
    remove_if_exists(prefix+"-references_row_priors.json")
    remove_if_exists(prefix+"-references_pairwise_excess.tsv.gz")
    remove_if_exists(prefix+"-references_data.tsv.gz")
    remove_if_exists(prefix+"-references_hitcounts.tsv.gz")
    remove_if_exists(prefix+"-models-0_data.tsv.gz")
    remove_if_exists(prefix+"-models-1_data.tsv.gz")
    remove_if_exists(prefix+"-models-2_data.tsv.gz")
    remove_if_exists(prefix+"-models_column_priors.json")
    remove_if_exists(prefix+"-models_row_priors.json")
    remove_if_exists(prefix+"-models_data.tsv.gz")
    remove_if_exists(prefix+"-models-complete-sums.tsv.gz")    
    

# ###########################################################################
# Configurations for various build types


class CompleteTestConfig(PhenoscoringConfig):
    """A complete configuration, as if from argparse."""
        
    action = "build"
    db = os.path.join("tests", "testdata", "phenoscoring-testdata.sqlite")    
    reset = True
    quiet = True
    simplify = "average"
    oomap = "owlsim-small.txt"    
    reference_phenotypes = "prep-phenotab-phenotypes.tsv"
    model_descriptions = None
    model_phenotypes = None
    scale_oo_scores = False
    reference_neighbors_k = 4
    reference_missing_factor = 0.5
    dark_count = 2
    base_tpr = 0.8
    base_fpr = 0.05
    fp_penalty = 0.25
    modelp = 0.01    
    obo = "Y.obo"
    prior = 0.01
    min_inference = 0.001
    min_enrichment = 100
    fp_penalty = 0.25
    cores = 1
    partition_size = 4    
    table = None


class IMPCTestConfig(CompleteTestConfig):
    """A configuration for updating with IMPC models"""
        
    model_descriptions = "prep-IMPC-descriptions.tsv"
    model_phenotypes = "prep-IMPC-phenotypes.tsv"
    partition_size = 1024
    

class MGITestConfig(CompleteTestConfig):
    """A configuration for updating with MGI models"""
    
    model_descriptions = "prep-MGI-descriptions.tsv"
    model_phenotypes = "prep-MGI-phenotypes.tsv"

