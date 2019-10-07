"""
Phenoscoring.py

This is the main interface to the Phenoscoring program.

See auxiliary program phenoprep.py to aid in preparing
inputs from HPO, IMPC, and MGI.
"""


import argparse
import json
from phenoscoring.phenoscoring import Phenoscoring


# ##################################################################
# create a parser object for the phenoscoring executable

parser = argparse.ArgumentParser(description="phenoscoring")

# part of the calculation to perform
parser.add_argument("action", action="store",
                    help="Type of action to perform", 
                    choices=["build", "update", "explain",
                             "clearmodels", "remove",
                             "recompute", "export", "representations"])

# output database
parser.add_argument("--db", action="store", required=True,
                    help="Database file")

# tuning how the tools behave
parser.add_argument("--reset", action="store_true", default=False,
                    help="delete existing database")
parser.add_argument("--quiet", action="store_true", default=False,
                    help="avoid all log messages")

# inputs for building database
parser.add_argument("--obo", action="store", 
                    help="ontology for model phenotypes")
parser.add_argument("--reference_phenotypes", action="store", 
                    help="path to file with reference phenotypes")
parser.add_argument("--phenotype_frequencies", action="store",
                    help="path to file with phenotype frequencies")                   

# inputs for augmenting database with models
parser.add_argument("--model_phenotypes", action="store", 
                    help="path to file with model phenotypes")                    
parser.add_argument("--model_descriptions", action="store", 
                    help="path to file with model descriptions")                    

# inputs for calculating scores
parser.add_argument("--reference_neighbors_k", action="store",
                    type=int, default=5,
                    help="number of neighbors for defining specific phenotypes")
parser.add_argument("--reference_missing_factor", action="store",
                    type=float, default=0.5,
                    help="multiplier for unspecified phenotypes in references")
parser.add_argument("--prior", action="store", 
                    type=float, default=1e-6,
                    help="prior probability for model-reference match")
parser.add_argument("--min_inference", action="store", 
                    type=float, default=0.005,
                    help="threshold for inference score")
parser.add_argument("--min_enrichment", action="store", 
                    type=float, default=1000,
                    help="threshold for inference enrichment")
parser.add_argument("--base_tpr", action="store",
                    type=float, default=0.8,
                    help="assumed true-positive-rate for experiments")
parser.add_argument("--base_fpr", action="store",
                    type=float, default=0.05,
                    help="assumed false-positive-rate for experiments")
parser.add_argument("--fp_penalty", action="store",
                    type=float, default=0.25,
                    help="parameter for penalizing false positives matches")
parser.add_argument("--skip_compute", action="store_true",                    
                    help="when used with action update, skips score computation")


# settings for calculation/performance
parser.add_argument("--cores", action="store", 
                    type=int, default=2,
                    help="number of compute cores")
parser.add_argument("--partition_size", action="store", 
                    type=int, default=1024,
                    help="number of models to score at a time in parallel")

# inputs for explaining scores
parser.add_argument("--explain", action="store", default="general",                      
                    help="either 'general', 'specific', or 'coverage'")
parser.add_argument("--explain_nodata", action="store_true",                       
                    help="omit data field from output of explain")
parser.add_argument("--pretty", action="store_true",                       
                    help="pretty-print output of explain")
parser.add_argument("--model", action="store",                     
                    help="model for detailed calculation log")
parser.add_argument("--reference", action="store",                     
                    help="reference for detailed calculation log")


# inputs for exporting tables
parser.add_argument("--table", action="store",                     
                    help="name of table to export")


# ##################################################################
# Execute the program if module is used as an executable


if __name__ == "__main__":
        
    config = parser.parse_args()
            
    pipeline = Phenoscoring(config)
    if config.action == "build":
        # create a new sqlite database with references
        pipeline.build()
        
    if config.action == "clearmodels":
        # remove all models and model scores from the database
        pipeline.clearmodels()  
          
    if config.action == "update":
        # add new or update existing model defintions/phenotypes
        pipeline.update()
        
    if config.action == "remove":
        # remove a subset of models from the database
        pipeline.remove()
        
    if config.action == "recompute":
        # remove all scores and re-generate them from scratch
        pipeline.recompute()
        
    if config.action == "export":
        # write a database table into a tsv file
        pipeline.export()
        
    if config.action == "representations":
        # compute complete representations for references and models
        pipeline.export_representations()
                    
    if config.action == "explain":
        # provide step-by-step explanation of scoring 
        result = pipeline.explain()
        if config.pretty:
            result = json.dumps(json.loads(result), indent=2)
        print(result)                
