"""
Prep data from phenotypetab into a format for Phenoscoring

This module contains several functions which are meant for internal use.
To use this from outside, see function prep_refs()
"""

import csv
from copy import deepcopy
from tools.files import open_file
from phenoscoring.phenotypedatum import PhenotypeDatum
from phenoscoring.entity import Entity
from scoring.experiment import Experiment
from phenoscoring.time import now_timestamp
from phenoscoring.update import get_file_models, get_file_phenotypes


# ###########################################################################
# Functions relevant to parsing disease/reference phenotypes


def get_emapa_map(emap_path, obo):
    """read a file definition of emap to mp mappings"""

    # get all the mapping from the raw file
    raw = dict()    
    with open_file(emap_path, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="'")
        for row in reader:
            emapa = str(row["EMAPA_ID"])
            mp = str(row["MP_ID"])
            if not obo.has(mp):
                print("Skipping mp term: " + mp)
                continue            
            ancestors = obo.ancestors(mp)
            if emapa not in raw:
                raw[emapa] = []
            raw[emapa].append((len(ancestors), mp))
    
    # extract the best hits
    result = dict()
    for k, hits in raw.items():
        hits.sort()
        best_value = hits[0][0]
        result[k] = [mp for _,mp in hits if _==best_value]
        
    return result
            

gxd_strength = dict()
gxd_strength["Absent"] = 1
gxd_strength["Moderate"] = 0.5
gxd_strength["Present"] = 0.25
gxd_strength["Strong"] = 0.75
gxd_strength["Very strong"] = 1

def get_gxd(gxd_path, emp_map, tprfpr):
    """read a file with marker-emapa associationss
    
    Arguments:
        gxd_path   file with columns ....
        emp_map      dict mapping EMAPA ids to other ids
        tprfpr     2-tuple with (tpr, fpr)
    
    Returns:
        dict mapping markers to phenotypes terms
    """
    
    tpr = tprfpr[0]
    fpr = tprfpr[1]
    
    # get all the mapping from the raw file
    result = dict()
    with open_file(gxd_path, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="'")
        for row in reader:
            feature = row["feature.primaryIdentifier"]
            emapa = row["structure.identifier"]
            strength = row["strength"]
            
            if feature not in result:                
                modelid = "GXD_"+feature                        
                result[feature] = Entity(modelid, "expression", marker_id=feature)
                result[feature].set_description("expression", 1)
                result[feature].set_description("source", "GXD")
            
            if emapa not in emp_map:
                continue
            if strength not in gxd_strength:
                continue
            
            # determine whether to add a positive or negative phenotype
            strength_factor = gxd_strength[strength]            
            row_exp = Experiment(1, fpr + (tpr-fpr)*strength_factor, fpr)            
            if strength == "Absent":
                row_exp.value = 0                        
            for mp in emp_map[emapa]:                
                result[feature].add(PhenotypeDatum(mp, row_exp))
    
    # get a concensus value
    for id in result:
        result[id].consensus()        
    
    return result 
    

def make_expression_model_stubs(models):
    """create distinct new models with new ids for expression phenotypes
    
    Arguments:
        models:    dict of Entity objects
    
    Returns:
        a new dict with Entity objects with new ids and marked with expression 
    """
        
    result = dict()
    for _, model in models.items():
        desc = model.description
        if desc["sex"] != "U":
            continue
        newmodel = deepcopy(model)            
        newmodel.id = model.id+"E"        
        newmodel.set_description("expression_phenotypes", 1)
        result[newmodel.id] = newmodel
    return result


def prep_GXD(desc_file, phen_file, gxd):
    """Augment existing models with expression phenotypes
    
    Arguments:
        desc_file    file path to model descriptions
        phen_file    file path to model phenotypes
        gxd          dict from markers to Entities with expression phenotypes
        
    Returns:        
        dict with Entity objects with merged phenotypes        
    """
    
    now = now_timestamp()
    
    # read original models 
    raw_models = get_file_models(desc_file, now)
    phenotypes = get_file_phenotypes(phen_file, now)
    for key, data in phenotypes.items():
        for datum in data:
            raw_models[key].add(datum)
                
    # get gxd marker to phenotype mappings        
    models = make_expression_model_stubs(raw_models)
    
    for id, model in models.items():
        if not model.has("marker_id"):
            continue
        marker = model.get("marker_id")        
        if marker not in gxd:            
            continue
        marker_data = deepcopy(gxd[marker].data)
        for datum in marker_data:
            model.add(datum)
    
    return models
