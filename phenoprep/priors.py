"""
Functions to compute phenotype frequencies (priors) from sets of Entities.
"""
   
from phenoscoring.entity import filter_entities_cat   
from scoring.representation import Representation
from copy import deepcopy


def counts_p(freqcounts, n, dark):
    """convert a dictionary of counts into probabilities [0,1]
    
    Arguments:
        freqcounts  dictionary linking ids to counts (can be real numbers)
        n           number of entities used to inform freqcounts
        dark        a dark count

    Returns:
        dict of same length as freqcounts, normalized to n+dark
    """

    # convert counts into proportions
    result = dict()
    n = float(n)
    for phenotype, count in freqcounts.items():
        result[phenotype] = min(1, count / (dark + n))
    return result    
    

def get_priors_from_models(models, categories, obo, dark=1):
    """Compute cohort-wide phenotype frequencies
    
    Arguments:
        models        dictionary of Entity objects
        categories    set, determines what models to use in the calculation
        obo           object of class Obo
        dark          integer, dark count for phenotype normalization
        
    Returns:
        dict mapping phenotypes (from obo) to values [0,1]
        integer, number of models used to inform the prior
    """
    
    # get a subset of the models that satisfy the criteria 
    all = [obj for _, obj in models.items()]
    hits = filter_entities_cat(all, categories)
    
    # transfer phenotypes into representations
    obodefaults = dict.fromkeys(obo.ids(), 0)
    freqcounts = dict.fromkeys(list(obo.ids()), dark)
    for entity in hits:
        # prepare concise representations
        rep = Representation(name=entity.id)
        for datum in entity.data:
           rep.set(datum.phenotype, datum.value)
        # convert to complete representation
        rep.impute(obo, obodefaults)
        # count phenotypes
        for phenotype in obo.ids():
            freqcounts[phenotype] += rep.data[phenotype]        
    
    # convert counts into frequencies
    result = counts_p(freqcounts, len(hits), dark)
    return result, len(hits)


def get_priors_from_reps(reps, obo, dark=1, impute=True):
    """Compute cohort-wide phenotype frequencies
    
    Arguments:
        reps        dictionary of Entity objects        
        obo         object of class Obo
        dark        integer, dark count for phenotype normalization
        impute      logical, whether to impute from a concise repre
        
    Returns:
        dict mapping phenotypes (from obo) to values [0,1]
        integer, number of models used to inform the prior
    """
    
    # transfer phenotypes into representations
    obodefaults = dict.fromkeys(obo.ids(), 0)
    freqcounts = dict.fromkeys(list(obo.ids()), dark)
    for _, rep in reps.items():
        # prepare a full representation
        thisrep = rep
        if impute:
            thisrep = deepcopy(rep)
            thisrep.impute(obo, obodefaults)        
        # count phenotypes
        for phenotype in obo.ids():
            freqcounts[phenotype] += thisrep.data[phenotype]        
    
    # convert counts into frequencies
    result = counts_p(freqcounts, len(reps), dark)    
    return result, len(reps)

