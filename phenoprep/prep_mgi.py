"""Prep data from MGI into a format for Phenoscoring

@author: Tomasz Konopka
"""

import csv
import re
from tools.files import open_file
from scoring.experiment import Experiment
from phenoscoring.phenotypedatum import PhenotypeDatum
from phenoscoring.entity import Entity
from phenoscoring.time import now_timestamp


# prefix used for all MGI models
mgi_prefix = "MGI_"


def mgi_model(id, category, marker_id=None, allele_id=None, 
              allele_symbol=None, background=None, zygosity=None):
    """build an Entity model object"""
    
    result = Entity(id, category, 
                    marker_id=marker_id,
                    marker_symbol="",
                    allele_id=allele_id,
                    allele_symbol=allele_symbol,
                    background=background,
                    zygosity=zygosity,
                    sex="U",
                    source="MGI",
                    neg_phenotypes=0)    
    return result


def prep_genotype_models(datapath, tprfpr, obo):
    """scan data from a file and create genotype-level models."""
    
    result = dict()
    now = now_timestamp()
    
    hit = Experiment(1, tprfpr[0], tprfpr[1])      
    with open_file(datapath, "rt") as f: 
        reader = csv.DictReader(f, delimiter="\t", quotechar="\"")
        for row in reader:
            genotype_id = row["MGI_Genotype_Accession_ID"]            
            # skip rows that are malformed or don't attribute to PubMed
            if genotype_id is None or row["PubMed_ID"] in (None, ""):
                continue                        
            # let default zygosity be homozygous, unless description has <+>
            zygosity = "hom"
            if re.search("<\+>", row["Allelic_Composition"]):
                zygosity = "het"            
            datum = PhenotypeDatum(row["Mammalian_Phenotype_ID"], hit, now)                               
            # add data genotype level
            mid = mgi_prefix + genotype_id + "_" + zygosity + "_U"
            if mid not in result:
                marker_id = row["MGI_Marker_Accession_ID"]
                background = row["Genetic_Background"]
                result[mid] = mgi_model(mid, "genotype", 
                                        marker_id = marker_id,
                                        allele_id = row["Allele_ID"],
                                        allele_symbol = row["Allele_Symbol"],
                                        background = background,
                                        zygosity = zygosity)
            result[mid].add(datum)
    
    # summarize the model entities (consensus and trimming)
    for mid in result.keys():        
        result[mid].consensus()
        result[mid].trim_ancestors(obo)

    return result


def prep_marker_models(models):
    """combine multiple genotype models into marker models."""
    
    result = dict()
    for id, model in models.items():
        marker_id = model.get("marker_id")
        zygosity = model.get("zygosity")        
        # assign a model id for the marker model and ensure it exists
        mid_marker = mgi_prefix + marker_id + "_" + zygosity + "_U"
        if mid_marker not in result:                    
            result[mid_marker] = Entity(mid_marker, "marker", 
                                        marker_id=marker_id, marker_symbol="")
            result[mid_marker].description = model.description.copy()
        # connect genotype phenotypes to the marker model
        for datum in model.data:
            result[mid_marker].add(datum)
        
    return result


def prep_MGI(datapath, tprfpr, obo):
    """scan a MGI rpt file and define models and their phenotypes.
    
    Args:            
        datapath:  path to MGI raw file    
        tprfpr:    tuple with two elements (tpr, fpr)
        obo:       Obo object for MGI mouse ontology
    
    Return:
        iterable object for models, including phenotype data
    """
        
    if datapath is None:
        return dict()
    
    # create genotypes models and marker models
    models = prep_genotype_models(datapath, tprfpr, obo)
    marker_models = prep_marker_models(models)
    
    # return both put together    
    models.update(marker_models)    
    return models
