"""
Functions used during update of a Phenoscoring database.
"""

import csv
import json
from db.generator import DBGenerator
from scoring.experiment import Experiment
from tools.files import open_file
from .dbtables import ModelDescriptionTable, ModelPhenotypeTable
from .dbhelpers import get_model_names
from .phenotypedatum import PhenotypeDatum
from .entity import Entity


# ###########################################################################
# Helpers to parse model data from files/db into memory objects

def make_model(row, stamp=None):
    """create one model entity using a dict-like structure
    
    Arguments:
        row    a dict-like object with components marker_id, etc.
        stamp  timestamp, must be provided in the function call or        
               be available in the input object.
               
    Returns:
        an Entity object with a model definition
    """
    
    id = row["id"]
    if stamp is None:
        stamp = row["timestamp"]
    result = Entity(id, row["category"], timestamp=stamp)                    
    result.set_description_full(json.loads(row["description"]))
    return result
    

def get_db_models(dbpath):
    """get descriptions of all models currently in database.
    
    Returns:
        dict with Entities carrying model descriptions
        All entities are without phenotypes!
    """
                        
    # scan references table and get reference names
    generator = DBGenerator(ModelDescriptionTable(dbpath))    
    result = dict()
    for row in generator.next():        
        result[row["id"]] = make_model(row)
    return result
  

def get_file_models(filepath, timestamp):
    """get model descriptions defined in a file."""

    result = dict()
    if filepath is None:
        return result   
    with open_file(filepath, "rt") as f:    
        reader = csv.DictReader(f, delimiter="\t", quotechar="'")
        for row in reader:
            result[row["id"]] = make_model(row, timestamp)
    return result


def get_file_phenotypes(filepath, timestamp):
    """get model phenotypes from a file."""
        
    result = dict()
    if filepath is None:
        return result       
    with open_file(filepath, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="'")
        for row in reader:
            experiment = Experiment(row["value"], row["TPR"], row["FPR"])
            datum = PhenotypeDatum(row["phenotype"], experiment, timestamp)
            id = row["id"]
            if id not in result:
                result[id] = []
            result[id].append(datum)
    return result


# ###########################################################################
# Helpers for book-keeping on models

def insert_descriptions(dbpath, entities):
    """add model descriptions into the db."""
    
    table = ModelDescriptionTable(dbpath)
    for _, m in entities.items():
        table.add(id=m.id, category=m.category,
                    description=m.description_str(),
                    timestamp=m.timestamp)
    table.save()


def new_entities(current, proposed):
    """compare a current set of entities with a proposed set.
    
    Arguments:
        current    dict with Entity objects
        proposed    dict with Entity objects
    
    Returns:
        a subset of proposed that are not in current.
    """
    
    result = dict()
    for key, value in proposed.items():
        if key not in current:
            result[key] = value
    return result
    

def change_descriptions(dbpath, entities):
    """alter existing db records"""
    
    model = ModelDescriptionTable(dbpath)
    
    for key, entity in entities.items():
        where = dict(id=key)
        data = dict(id=key, 
                    category=entity.category, 
                    description=entity.description_str(),
                    timestamp=entity.timestamp)
        model.update(data, where)        


def changed_entities(current, proposed):
    """compare a current set of entities with a proposed set.
    
    Arguments:
        current     dict with Entity objects
        proposed    dict with Entity objects
    
    Returns:
        a subset of proposed that are present in current, but their 
        content is different.
    """
    
    result = dict()
    for key, value in proposed.items():
        if key not in current:
            continue
        if not current[key].equivalent(proposed[key]):
            result[key] = proposed[key]
    
    return result


def insert_phenotypes(dbpath, phenotypes):
    """insert phenotype entries in the db."""
    
    model = ModelPhenotypeTable(dbpath)
    # transfer entries into the db
    for key, phenlist in phenotypes.items():        
        for datum in phenlist:
            model.add(id=key, phenotype=datum.phenotype, 
                      timestamp=datum.timestamp,
                      value=datum.value, TPR=datum.tpr, FPR=datum.fpr)
    model.save()
    

# ###########################################################################
# Main function to call from phenoscoring.py

def update_model_descriptions(dbpath, descpath, timestamp):
    """update the databse with new model definitions"""
    
    # load data from the db and from the files
    current = get_db_models(dbpath)    
    descriptions = get_file_models(descpath, timestamp)
    
    # update model definitions
    new_descriptions = new_entities(current, descriptions)
    changed_descriptions = changed_entities(current, descriptions)
    insert_descriptions(dbpath, new_descriptions)
    change_descriptions(dbpath, changed_descriptions)
    # assemble a summary of all actions and exit
    summary = dict()
    summary["new_descriptions"] = list(new_descriptions.keys())
    summary["changed_descriptions"] = list(changed_descriptions.keys())    
    return summary


def add_model_phenotypes(dbpath, phenpath, timestamp):
    """add new model phenotypes to the db"""
    
    # load data from the db and from the files
    modelnames = get_model_names(dbpath)    
    phenotypes = get_file_phenotypes(phenpath, timestamp)
    
    summary = dict()
    
    # make sure all the models referred to in the phenotypes exist
    abnormal = []
    for id in phenotypes:
        if id not in modelnames:
            abnormal.append(id)
    summary["incorrect_ids"] = abnormal
    if len(abnormal)>0:
        return summary        
    
    # send the phenotypes into the database
    insert_phenotypes(dbpath, phenotypes)
    summary["new_phenotypes"] = list(phenotypes.keys())
    return summary

