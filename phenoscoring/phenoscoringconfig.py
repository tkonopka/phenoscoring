"""A configuration object for class Phenoscoring()

@author: Tomasz Konopka
"""

from .time import now_timestamp


class PhenoscoringConfig():
    """class that objects interpreted by Phenoscoring()."""
    
    action = "compute"
    explain = "general"  
    db = None    
    reset = False
    quiet = True     
    # the following filename are for indication only.
    # must replace with a real filesnames
    oomap = "owlsim.txt"
    phenotype_frequencies = "prep-MGI-priors.tsv"    
    obo = "Y.obo"   
    # suggested defaults
    pretty = False
    skip_compute = False
    explain_nodata = False 
    reference_neighbors_k = 5
    fp_weight = 0.8
    prior = 0.001
    min_inference = 0.001
    min_enrichment = 100    
    cores = 1
    partition_size = 512
    stamp = now_timestamp()  
