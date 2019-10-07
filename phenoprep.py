"""
Phenoprep.py

Phenoscoring-prep is a utility that parses certain raw data files and
prepares data into a format ready to consume by Phenoscoring.py. 

This is an auxiliary program to phenoscoring.py
"""


import argparse
from obo.obo import MinimalObo
from phenoprep.prep_impc import prep_IMPC, get_IMPC_hits_summary
from phenoprep.prep_imputation import get_UA_models, make_scaled_cooc
from phenoprep.prep_imputation import impute_IMPC, get_models_by_phenotype
from phenoprep.prep_mgi import prep_MGI
from phenoprep.prep_refs import prep_refs, prep_tech_models
from phenoprep.prep_oo import prep_oo
from phenoprep.prep_gxd import get_emapa_map, get_gxd, prep_GXD
from phenoprep.priors import get_priors_from_models, get_priors_from_reps
from phenoprep.write import write_models, write_references, write_priors
from phenoprep.write import write_hits_summary, write_phenotype_cooc
from phenoprep.write import write_oo
from phenoscoring.entity import filter_entities, filter_entities_cat
from tools.files import check_file


# ##################################################################
# create a parser object for the phenoscoring executable

parser = argparse.ArgumentParser(description="phenoscoring-prep")

# choice of data preparation pipeline
parser.add_argument("action", action="store",
                    help="Type of data to prep", 
                    choices=["MGI", "IMPC", "IMPCimputed", 
                             "phenotypetab", "oomap", "GXD"])

# location of input and output data files
parser.add_argument("--input", action="store",
                    help="primary input file")
parser.add_argument("--output", action="store", required=True,
                    help="prefix for output files")

# additional inputs (may be required for some prep pipelines)
parser.add_argument("--tpr", action="store", type=float, default=0.8, 
                    help="default true positive rate")
parser.add_argument("--fpr", action="store", type=float, default=0.05, 
                    help="default false positive rate")
parser.add_argument("--obo", action="store", 
                    help="path to ontology obo file")
parser.add_argument("--oomap", action="store", 
                    help="path to file with ontology-ontology mapping")                    
parser.add_argument("--threshold", action="store", type=float, default=1e-4,
                    help="threshold for p values")
parser.add_argument("--priors", action="store", default="marker",
                    help="set of model categories to use in prior calculation")
parser.add_argument("--imputation_penalty", action="store", type=float, default=0,
                    help="factor used during phenotype imputation")
parser.add_argument("--seed", action="store", type=int, default=0,
                    help="seed for random number generation (tech controls)")
parser.add_argument("--dark_count", action="store", type=int, default=2,
                    help="dark count for prior estimation")
parser.add_argument("--simplify", action="store",
                    choices=["none", "consensus", "average"])


# for augmenting models with expression data
parser.add_argument("--phenotypes", action="store", 
                    help="file with model phenotypes (output from phenoprep)")
parser.add_argument("--gxd", action="store",
                    help="file with marker expression data")
parser.add_argument("--emapa", action="store",
                    help="file with EMAP to MP translation")

 

# ##################################################################
# Execute the program if module is used as an executable


if __name__ == "__main__":
        
    config = parser.parse_args()                
    tprfpr = (config.tpr, config.fpr)
    fe = filter_entities
    fe_cat = filter_entities_cat
    threshold = config.threshold

    if config.action == "MGI":
        # action to parse mouse phenotype models from MGI
        
        check_file(config.input, required="input")
        check_file(config.obo)        
        obo = MinimalObo(config.obo)
        models = prep_MGI(config.input, tprfpr, obo)
        # write out all models and subsets
        genotype_models = fe_cat(models, set(["genotype"]))
        marker_models = fe_cat(models, set(["marker"]))
        write_models(genotype_models, config.output+"-genotype-universal")
        write_models(marker_models, config.output+"-marker-universal")
        # compute and write priors based on certain types of models
        categories = set(config.priors.split(","))
        priors, num_models = get_priors_from_models(models, categories, obo,
                                                    dark=config.dark_count)        
        print("Number of models used to inform prior: "+str(num_models))
        write_priors(priors, config.output)

    if config.action == "IMPC":
        # action to parse mouse model annotations from IMPC
                
        check_file(config.input, required="input")        
        check_file(config.obo)        
        models = prep_IMPC(config.input, tprfpr, threshold,
                           simplify=config.simplify)
        
        # filter functions
        def f_U_allele(x):
            return x.category == "allele" and x.description["sex"] == "U"
        def f_S_allele(x):
            return x.category == "allele" and x.description["sex"] != "U"
        def f_U_marker(x):
            return x.category == "marker" and x.description["sex"] == "U"
        def f_S_marker(x):
            return x.category == "marker" and x.description["sex"] != "U"
        
        # apply each filter and save the models
        prefix = config.output
        write_models(fe(models, f_U_allele), prefix+"-allele-universal")
        write_models(fe(models, f_S_allele), prefix+"-allele-sex")
        write_models(fe(models, f_U_marker), prefix+"-marker-universal")
        write_models(fe(models, f_S_marker), prefix+"-marker-sex")
        
        # create models without consensus
        fullmodels = prep_IMPC(config.input, tprfpr, threshold, simplify="none")        
        write_models(fe(fullmodels, f_U_allele), prefix+"-allele-universal-full")
                
        # get a summary of IMPC hits
        tested, hits = get_IMPC_hits_summary(config.input, threshold)
        write_hits_summary(tested, hits, config.output)

    if config.action == "IMPCimputed":
        # action to parse IMPC mouse models, create models with imputed data        
        
        check_file(config.input, required="input")
        check_file(config.obo)        
        models = prep_IMPC(config.input, tprfpr, threshold,
                           simplify=config.simplify)
        
        # create models with imputed phenotypes
        obo = MinimalObo(config.obo)
        penalty = config.imputation_penalty
        models_UA = get_UA_models(models, "allele")
        # create and save various co-occurance matrices
        observed = get_models_by_phenotype(models_UA, 1)
        for type in ["full", "freq", "simJ"]:        
            cooc, phenindex = make_scaled_cooc(observed, obo, penalty, type)
            write_phenotype_cooc(cooc, phenindex, config.output+"-"+type)
            del cooc, phenindex
        
        imputed_models = impute_IMPC(models_UA, obo, penalty)
        write_models(imputed_models, config.output+"-imputed")

    if config.action == "phenotypetab":
        # action to parse HPO annotations for diseases.
        
        check_file(config.input, required="input")
        check_file(config.oomap, required="oomap")        
        check_file(config.obo)        
        obo = MinimalObo(config.obo)
        
        # read reference data from the input file
        references, badphens = prep_refs(config.input, config.oomap)        
        if len(badphens) > 0:
            print("Encountered "+str(len(badphens))+" unknown phenotypes:")
            print(str(badphens))
        write_references(references, config.output)
        
        # create technical controls        
        ctrls_0, ctrls_1 = prep_tech_models(references, tprfpr, 
                                            obo, config.seed)
        write_models(ctrls_0, config.output+"-controls-match")
        write_models(ctrls_1, config.output+"-controls-siblings")
        
        # estimate priors
        priors, num_models = get_priors_from_reps(references, obo, 
                                                  dark=config.dark_count)
        write_priors(priors, config.output)

    if config.action == "oomap":
        # action to perform ontology-ontology mappings from owltools
        
        check_file(config.input, required="input")
        check_file(config.obo)
        obo = MinimalObo(config.obo)
        oo = prep_oo(config.input, obo)
        write_oo(oo, config.output)

    if config.action == "GXD":
        # action to augment models with expression data
        
        check_file(config.obo)        
        check_file(config.emapa)     
        check_file(config.gxd)
        
        # load ontology, emapa, and expression mappings
        obo = MinimalObo(config.obo)
        emp_map = get_emapa_map(config.emapa, obo)        
        gxd = get_gxd(config.gxd, emp_map, tprfpr)
        
        if config.input is None:
            # just print out parsed GXD data
            write_models(gxd, config.output)
        else:
            # augment exisitng models with gxd data
            check_file(config.input, required="input")
            check_file(config.phenotypes, required="phenotypes")
            models = prep_GXD(config.input, config.phenotypes, gxd)
            write_models(models, config.output)
