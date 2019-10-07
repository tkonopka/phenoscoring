"""
Helpers used extracting common components from the phenoscoring db.
"""

from db.generator import DBGenerator
from scoring.referenceset import ReferenceSet
from scoring.representation import Representation
from .dbtables import PhenotypeFrequencyTable, ReferencePriorsTable
from .dbtables import ModelDescriptionTable, ModelScoreTable
from .dbtables import ModelPhenotypeTable
from .dbtables import ReferenceCompletePhenotypeTable


def get_phenotype_priors(dbpath):
    """Create a dict with prior probabilities for all phenotypes."""
                    
    generator = DBGenerator(PhenotypeFrequencyTable(dbpath))    
    result = dict()
    for row in generator.next():
        result[row["phenotype"]] = float(row["frequency"])
        
    return result


def get_model_names(dbpath):
    """Get a list with all model names."""
    
    return ModelDescriptionTable(dbpath).unique("id")    
 

def get_ref_names(dbpath):
    """Get a list with all reference names."""
    
    return ReferencePriorsTable(dbpath).unique("id")    


def get_ref_priors(dbpath, references=None):
    """Create a dict with prior probabilities for references
    
    Args:
        dbpath      path to db
        references  set with reference names to include
                    (or None to get the entire table)
    
    Returns:
        dictionary mapping references to prior probabilities
    """
                        
    generator = DBGenerator(ReferencePriorsTable(dbpath))    
    result = dict()
    for row in generator.next():
        if references is None or row["id"] in references:
            result[row["id"]] = float(row["value"])        
    return result


def delete_model_scores(dbpath, modelnames):
    """drop certain rows from the model scores."""
        
    model = ModelScoreTable(dbpath)        
    current = model.unique("model")
    to_delete = set(modelnames).intersection(current)    
    model.delete("model", list(to_delete))    


def delete_models(dbpath, modelnames):
    """drop all data pertaining to certain models"""
        
    modelnames = list(modelnames)
    ModelDescriptionTable(dbpath).delete("id", modelnames)
    ModelPhenotypeTable(dbpath).delete("id", modelnames)
    delete_model_scores(dbpath, modelnames)
    

def get_complete_null(dbpath):
    """create a complete representation for the null reference"""
    
    result = Representation(name="null")
    tab = ReferenceCompletePhenotypeTable(dbpath)
    generator = DBGenerator(tab, where=dict(id="null"))    
    for row in generator.next():
        result.set(row["phenotype"], row["value"])    
    return result
     

def get_refsets(dbpath, ref_priors=None, phenotype_priors=None):
    """Create ReferenceSets objects with general and specific phenotypes 
    
    Arguments:
        dbpath            path to phenoscoring db
        ref_priors        dictionary with priors for references
                          (if None, fetched from db)
        phenotype_priors  dictionary with priors for all featurs
                          (if None, fetched from db)

    Returns:
        two ReferenceSets objects    
    """
    
    ## at first create just a dictionary of representations
    general_dict, specific_dict = dict(), dict()    
    
    if phenotype_priors is None:
        phenotype_priors = get_phenotype_priors(dbpath)
    if ref_priors is None:
        ref_priors = get_ref_priors(dbpath)
    
    ## create empty Representations for each reference    
    nullrep = get_complete_null(dbpath)
    phenotypes = nullrep.keys()
    for id in ref_priors.keys():
        general_dict[id] = nullrep.copy(name=id)
        specific_dict[id] = nullrep.copy(name=id)
    
    ## fill the representations with values
    phentab = ReferenceCompletePhenotypeTable(dbpath)
    if len(ref_priors) == 1:
        refname = list(ref_priors.keys())[0]
        generator = DBGenerator(phentab, where=dict(id=refname))
    else:        
        generator = DBGenerator(phentab)
    for row in generator.next():
        id, phen = row["id"], row["phenotype"]
        if id in ref_priors:
            general_dict[id].set(phen, row["value"])
            specific_dict[id].set(phen, row["specific_value"])        
        
    # transfer representations into ReferenceSets
    general = ReferenceSet(ref_priors, phenotypes, phenotype_priors)    
    specific = ReferenceSet(ref_priors, phenotypes, phenotype_priors)
    for refid in general_dict.keys():
        general.add(general_dict[refid])
        specific.add(specific_dict[refid])             
    
    return general, specific


def get_rootpath(dbpath):
    """get a string with a path+prefix from a sqlite filepath."""    
    return dbpath[:-7]
    
