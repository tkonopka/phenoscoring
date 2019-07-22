"""use phenotype imputation to prepare augment IMPC models for Phenoscoring

@author: Tomasz Konopka
"""

import numpy as np
from copy import deepcopy
from scoring.experiment import Experiment
from phenoscoring.phenotypedatum import PhenotypeDatum


def get_UA_models(models, category):
    """get a subset of models of universal sex with negative phens."""
    
    result = dict()            
    for key, model in models.items():
        if model.category != category:
            continue
        desc = model.description
        if desc["sex"]=="U" and desc["neg_phenotypes"]:
            result[key] = model
    return result


def get_phenotype_universe(models):
    """get a set with all phenotypes measured in models."""
    
    result = set()
    for key, model in models.items():
        for d in model.data:
            result.add(d.phenotype)
    return result        
    

def get_models_by_phenotype(models, min_value=0):
    """get a mapping from phenotype to models
    
    Arguments:
        models     dict with model Entity data
        min_value  numeric, minimum value of value 
           (use 0 for all phenotypes, use 1 for just significant phenotypes)
    
    Returns:
        dictionary mapping from phenotype to a set of model ids
    """

    allphens = get_phenotype_universe(models)    
    result = dict()
    for phen in allphens:
        result[phen] = set()
    for key, model in models.items():
        for x in model.data:
            if x.value >= min_value:    
                result[x.phenotype].add(key)
    return result
    

def make_index(keys):    
    """create a mapping from string to sequential integers."""
    result = dict()
    for _ in sorted(keys):
        result[_] = len(result)
    return result


def ji(a, b):
    """get a jaccard index between two sets."""
    return len(a.intersection(b)) / len(a.union(b))


def cooc_full(m1, m2, a1, a2):
    """compute a co-occurance metric.
    
    Arguments:
        m1   list of models with first phenotype
        m2   list of models with second phenotype
        a1   list of ancestors of first phenotype
        a2   list of ancestors of second phenotype
    
    Returns:
        numeric value
    """
    return ji(m1, m2)*(1-ji(a1, a2))


def cooc_freq(m1, m2, a1, a2):
    """Similar to cooc_full, but only uses m1, m2."""
    return ji(m1, m2)


def cooc_simJ(m1, m2, a1, a2):
    """Similar to cooc_simJ, but only uses a1, a2."""
    return ji(a1, a2)


def make_scaled_cooc(phen2ids, obo, penalty, type="full"):
    """create a square matrix of co-occurance
    
    Arguments:
        phen2ids   dict mapping phenotypes to model ids
        obo        Obo object, used for scaling
        penalty    numeric, a multiplier used for final scaling
        type       string, use "full", "freq", "simJ" 
    
    Returns:
        square numpy array and a phenotype index
    """

    # determine the cooc scaling function from argument type
    if type == "full":
        cooc = cooc_full
    elif type == "freq":
        cooc = cooc_freq
    elif type == "simJ":
        cooc = cooc_simJ
    else:
        raise Exception("invalid cooc type")
    
    phenindex = make_index(phen2ids.keys())
    phenotypes = list(phenindex.keys())
    
    # get a simple multiplicative factor for scaling in range [0,1]
    penalty_factor = 1-max(0, min(1, penalty))
    
    # precompute phenotype ancestors
    ancestors = dict()
    for p in phenotypes:
        ancestors[p] = set(obo.ancestors(p))
        ancestors[p].add(p)
            
    # create a matrix of scaled co-occurances
    numphen = len(phenindex)
    result = np.zeros((numphen,numphen))    
    for p1, i1 in phenindex.items():
        m1, a1 = phen2ids[p1], ancestors[p1]                
        if len(m1) == 0 or len(a1) == 0:
            continue
        for p2, i2 in phenindex.items():
            m2, a2 = phen2ids[p2], ancestors[p2]                        
            if len(m2) == 0 or len(a2) == 0:
                continue
            result[i1, i2] = cooc(m1, m2, a1, a2)*penalty_factor
            
    return result, phenindex
            

def make_imputed_model_stubs(models):
    """create distinct new models with new ids for imputed phenotypes
    
    Arguments:
        models:    dict of Entity objects
    
    Returns:
        a new dict with Entity objects with new ids and marked for imputation
    """
        
    result = dict()
    for _, model in models.items():
        newmodel = deepcopy(model)        
        newmodel.id = "_".join(model.id.split("_")[:-1])+"_IA"        
        newmodel.set_description("imputed_phenotypes", 1)
        result[newmodel.id] = newmodel
    return result
    
    
def impute_one_model(model, measured, observed, cooc, phenindex):
    """add phenotypes to one Entity object
    
    Arguments:
        model       Entity object
        measured    dict mapping phenotypes to a set of model ids
        observed    dict mapping phenotypes to a set of model ids
        cooc        nummpy array with a weight matrix
        phenindex   dict mapping phenotypes to indexes in the cooc matrix
        
    Returns:
        a modified model object with additional phenotypes
    """
    
    # set of suggested imputed phenotypes
    suggestions = []
    
    # helper to append PhenotypeDatum objects to the suggestions   
    def add_suggestions(datum):
        """add a set of datums to suggestions."""
        
        seed = datum.phenotype
        i = phenindex[seed]
        for target, j in phenindex.items():            
            if i == j:
                continue
            # avoid imputing experimentally-determined phenotypes
            if model.id in measured[target]:
                continue
            e = Experiment(0.5, datum.tpr*cooc[i,j], datum.fpr)
            if e.tpr < e.fpr:
                continue
            d = PhenotypeDatum(target, e, datum.timestamp)            
            suggestions.append(d)            
        
    # create suggestions by imputing from positive phenotypes
    for datum in model.data:        
        if datum.value == 0:
            continue
        add_suggestions(datum)        
        
    # add suggestions into the model, finish by summarizing phenotypes
    for x in suggestions:
        model.add(x)            
    return model.consensus()


def impute_IMPC(models, obo, penalty):
    """prepare a new set of IMPC models with imputed phenotypes
    
    Arguments:
        models     dict with relevant IMPC models         
        obo        Obo object
        penalty    numeric in range [0,1]; use high numbers to give less
                   weight to imputed phenotypes
    """
        
    # make a set of models that will eventually contain imputed
    result = make_imputed_model_stubs(models)
    # get mapping from phenotypes to
    measured = get_models_by_phenotype(result, 0)
    observed = get_models_by_phenotype(result, 1)
    
    # get a co-occurance matrix
    cooc, phenindex = make_scaled_cooc(observed, obo, penalty)
    
    # impute phenotypes, one model at a time
    for key, model in result.items():
        original_phenotypes = set([_.phenotype for _ in model.data])            
        result[key] = impute_one_model(model, measured, observed, 
                                       cooc, phenindex)
        result[key].trim_ancestors(obo, keep=original_phenotypes)
    
    return result

