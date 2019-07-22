"""Prep data from phenotypetab into a format for Phenoscoring

This module contains several functions which are meant for internal use.
To use this from outside, see function prep_refs()

@author: Tomasz Konopka
"""

import csv
import random
import re
from numpy import median as median
from numpy import tanh as tanh
from tools.files import open_file
from scoring.representation import Representation
from scoring.experiment import Experiment
from phenoscoring.phenotypedatum import PhenotypeDatum
from phenoscoring.entity import Entity
from phenoscoring.time import now_timestamp


# helper to convert HP frequency codes to numeric values
tofreq = dict()
tofreq[""] = 1
tofreq["."] = 1
tofreq["HP:0040280"] = 1
tofreq["HP:0040281"] = 0.9
tofreq["HP:0040282"] = 0.6
tofreq["HP:0040283"] = 0.2
tofreq["HP:0040284"] = 0.02
tofreq["HP:0040285"] = 0 


# ###########################################################################
# Functions relevant to parsing disease/reference phenotypes


def valid_reference_id(ref):
    """check if a string denoting a reference is acceptable.
    i.e. OMIM:123 or ORPHA:123 etc.
    """
    
    # ref code must match a prefix
    if not re.match("OMIM|ORPH|DECI|DISEASE|PMID", ref):
        return False
    # ref must have only two components
    parts = ref.split(":")
    if len(parts)>2:
        return False
    # each component must be non-empty
    if min([len(_) for _ in parts])<1:
        return False
    
    return True


def get_oo_map(oopath):
    """read a file mapping ontology terms to another set of terms.
    
    Args:
        oopath       path to text file with term1, term2, score
    
    Return:
        dict mapping term1 -> [(term2, score)]
    """
    
    result = dict()
    with open_file(oopath, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="\"")       
        for row in reader:
            term1 = row["term1"]
            score = float(row["score"])
            if term1 not in result:
                result[term1] = []                            
            for term2 in row["term2"].split(";"):
                result[term1].append((term2, score))
    return result


def get_oo_scores(oomap):
    """Get a vector with all ontology-ontology scores."""
    
    result = []    
    for key,values in oomap.items():
        for x in values:
            result.append(x[1])        
    return result


def get_raw_references(datapath, phenotype_set):
    """Parse a phenotype file and collect descriptions and raw phenotypes  
    
    raw phenotypes are phenotypes in the original ontology
    
    Args:
        datapath       path to phenotab file
        phenotype_set  set of acceptable phenotypes
    
    Returns:
        two objects
        - dict mapping reference codes to reference descriptions and phenotypes
        - set of phenotypes that could not be mapped
    """
    
    badphenotypes = set()
    references = dict()
    with open_file(datapath, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="\"")
        for row in reader:                        
            if not valid_reference_id(row["Reference"]):
                continue
            phenotype = row["Phenotype"]           
            if phenotype not in phenotype_set:
                badphenotypes.add(phenotype)
                continue
            rowval = tofreq[row["Frequency"]]
            id = row["Source"]+":"+row["Disease_number"]
            if id not in references:                
                references[id] = Representation(name=id)
                references[id].title = row["Disease_title"]
            references[id].set(phenotype, rowval)        
                
    return references, badphenotypes


def get_ref_priors(references, null_prior=0.99):
    """Create a dict with prior probs for all references, plus a null."""
                                    
    numrefs = float(len(references))    
    result = dict(null=null_prior)
    for oneref in references:
        result[oneref] = (1.0-null_prior)/numrefs        
    return result


def make_target_reference(reference, oomap, oo_median = None):
    """convert a single representation from one ontology to another."""
    
    result = Representation(name=reference.name)
    result.title = reference.title
    
    for phenotype, value in reference.data.items():
        for oo_phenotype, oo_score in oomap[phenotype]:
            # perhaps compute a rescaled oo value
            newvalue = value
            if oo_median is not None:
                newvalue = value*tanh(oo_score/oo_median)
            # always take the larger value if previously set
            if result.has(oo_phenotype):
                newvalue = max(newvalue, result.get(oo_phenotype))
            result.set(oo_phenotype, newvalue)

    return result


def get_target_references(references, oomap, scale_oo_scores=True):
    """convert raw reference phenotypes to a another ontology
    
    Arguments:
        references:        dict with raw representations
        oomap:             dict with cross-ontology mappings
        scale_oo_scores:   logical, determines whether or not to
                apply tanh() transform to scale oo mapping
    
    Returns:
        dictionary of (concise) Representation objects
    """
    
    # learn about the distribution of translation scores
    oo_scores = get_oo_scores(oomap)
    oo_median, oo_max = median(oo_scores), max(oo_scores)    
        
    # reset oo_median (avoid scaling) if explicit or irrelevant
    if not scale_oo_scores or oo_max==oo_median:
        oo_median = None
            
    # convert all the reference into the target ontology
    result = dict()    
    for id, refrep in references.items():
        result[id] = make_target_reference(refrep, oomap, oo_median)
        result[id].title = refrep.title        
        
    return result


def prep_refs(datapath, oopath):
    """scan a phenotypetab file and convert disease phenotypes
    
    Args:            
        datapath   path to phenotab file    
        oopath     path to cross-ontology mapping        
    
    Return:
        iterable object with Representation objects
        iterable with unmatchned/unrecognized phenotypes
    """
    
    oomap = get_oo_map(oopath)
    # extract raw phenotypes in original ontology
    raw, badphenotypes = get_raw_references(datapath, set(oomap.keys()))
    # convert the phenotypes into the target ontology
    references = get_target_references(raw, oomap)
    
    return references, badphenotypes


# ###########################################################################
# Functions relevant to preparing technical control models


def tech_model(id, control_type="match"):
    """create an Entity object with some description fields."""
    
    result = Entity(id, "control", 
                    allele_id="",
                    allele_symbol="",
                    background="",
                    imputed_phenotypes=0,
                    control_type=control_type)                         
    return result


class TechModelFactory():
    """a class for creating technical controls (models)."""
    
    def __init__(self, tprfpr, timestamp, obo=None):
        self.tpr = tprfpr[0]
        self.fpr = tprfpr[1]
        self.timestamp = timestamp
        self.obo = obo        
    
    
    def _pick_sibling(self, seed):
        """pick a sibling of seed, weighted by similar number of ancestors."""
        
        candidates = self.obo.siblings(seed)        
        if len(candidates) == 0:
            candidates = self.obo.parents(seed)
        if len(candidates) == 0:
            candidates = set([seed])
        candidates = list(candidates)
        
        # get counts of ancestors 
        # (fewer ancestors, means more general term, means lower score)
        seed_ancestors = len(self.obo.ancestors(seed))
        weights = [None] * len(candidates)
        for i in range(len(candidates)):
            weights[i] = len(self.obo.ancestors(candidates[i]))
        weights = [1+max(seed_ancestors, _) for _ in weights]
        
        return random.choices(candidates, weights=weights, k=1)[0]
    
        
    def control0(self, refname, refrep):
        """create a model with the same phenotypes as a representation. """
                
        model = tech_model(refname+"_match", "match")
        model.set_description("control_for", refname)
        timestamp = self.timestamp
        for phen in refrep.keys():
            phen_value = refrep.get(phen)
            phen_exp = Experiment(1, self.tpr, self.fpr)            
            model.add(PhenotypeDatum(phen, phen_exp, timestamp))            
        return model.trim_ancestors(self.obo)
        
    def control1(self, refname, entity):
        """create a model with sibling phenotypes to a given model"""
                        
        model = tech_model(refname+"_siblings", "siblings")
        model.set_description("control_for", refname)
        timestamp = self.timestamp        
        for datum in entity.data:
            phen = datum.phenotype
            newphen = self._pick_sibling(phen)
            model.add(PhenotypeDatum(newphen, datum.experiment, timestamp))
        return model.trim_ancestors(self.obo)
        
     
def prep_tech_models(references, tprfpr, obo, seed=0):
    """create a set of Entity objects with technical control models. """
    
    # prepare a factory class for control models
    now = now_timestamp()    
    random.seed(seed)
    factory = TechModelFactory(tprfpr, now, obo)
       
    result_0, result_1 = dict(), dict()        
    for _, refrep in references.items():
        c0 = factory.control0(refrep.name, refrep)
        c1 = factory.control1(refrep.name, c0)
        result_0[c0.id] = c0
        result_1[c1.id] = c1                
    return result_0, result_1

