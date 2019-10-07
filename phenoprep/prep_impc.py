"""
Prep data from IMPC into a format for Phenoscoring
"""

import csv
import pkg_resources
from tools.files import open_file
from scoring.experiment import Experiment
from phenoscoring.phenotypedatum import PhenotypeDatum
from phenoscoring.entity import Entity
from phenoscoring.time import now_timestamp


# fetch a dictionary of term redefinitions for MP:0002169 (no abnormal phenotype detected)
redef = dict()
redef_file = pkg_resources.resource_filename(__name__, "impc.2169.tsv")
with open_file(redef_file, "rt") as f:
    reader = csv.DictReader(f, delimiter="\t", quotechar="\"")        
    for row in reader:
        rowkey = row["original_id"] + " " + row["parameter_name"]
        redef[rowkey] = row["redefined_id"]


# ###########################################################################
# Functions relevant to prep_IMPC


def is_float(x):
    """an ad-hoc way to determine if a string encodes a pvalue.""" 
    
    try:
        float(x)
    except:
        return False
    return True
        

def get_p_value(x):
    """convert a raw string into a p value."""
        
    if is_float(x):
        return float(x)
    return 1
    

def sex_code(s):
    """transform a string like 'female,male' into a one-letter F/M/B/U"""
    
    result = s.replace("female", "F").replace("male", "M")
    if "F" in result and "M" in result:
        return "B"
    if "F" in result:
        return "F"
    elif "M" in result:
        return "M"
    # code for unknown/unspecified
    return "U"
    

def negative_code(s):
    """transform a suffix like 'MA' or 'M' into 0/1 indicating if negative 
    phenotypes will be included in the model data."""
    
    return 0 + ("A" in s)


def impc_model(id, category, row, zygosity):
    """build a model object using row dict from IMPC data"""
    
    result = Entity(id, category, 
                    marker_id=row["marker_accession_id"], 
                    marker_symbol=row["marker_symbol"],
                    allele_id=row["allele_accession_id"],
                    allele_symbol=row["allele_symbol"],
                    background=row["strain_name"],
                    imputed_phenotypes=0,
                    zygosity=zygosity,
                    source="IMPC")        
    return result


def get_value(row, pthreshold):
    """get 0/1 signaling if a row is significant."""
    
    p_value = get_p_value(row["p_value"])
    phenotype = row["mp_term_id"].strip()                
    if p_value < pthreshold:
        val = 1
    else:
        if row["significant"] == "true":
            val = 0 if phenotype == "MP:0002169" else 1
        else:
            val = 0
    return val


def get_IMPC_hits_summary(datapath, pthreshold):
    """get an object (parameter)+(MP term), to marker ids (tested, hits)"""
    
    tested, hits = dict(), dict()
    if datapath is None:
        return tested, hits
    
    with open_file(datapath, "rt") as f: 
        reader = csv.DictReader(f, delimiter=",", quotechar="\"")        
        for row in reader:
            # skip over bad data rows
            if row["status"] != "Success":
                continue
            # identify id, phenotype, whether a hit or not
            parameter = row["parameter_name"].strip()
            phenotype = row["mp_term_id"].strip()
            marker = row["marker_accession_id"]
            if phenotype == "":
                continue
            
            key = parameter+"\t"+phenotype
            if key not in tested:
                tested[key] = set()
                hits[key] = set()

            tested[key].add(marker)
            if get_value(row, pthreshold):
                hits[key].add(marker)

    return tested, hits


def prep_IMPC(datapath, tprfpr, pthreshold, simplify="average"):
    """parse IMPC statistical results and assemble a set of models.
    
    Args:
        datapath:    path to MGI raw file            
        tprfpr:      list with two elements (tpr, fpr)
        pthreshold:  float, minimum threshold for significance
        simplify:    string, method for simplifying multiple data type
                    (use 'none', 'average', or 'consensus')
    """
                
    models = dict()        
    if datapath is None:
        return models
    
    now = now_timestamp()
    base_tpr, base_fpr = tprfpr[0], tprfpr[1]            
    male = set(["M", "B", "U"])
    female = set(["F", "B", "U"])
        
    def create_models(id, category, zygosity, row):
        """Create a family of model definitions, for sex=FMU, neg_phen=01"""
        
        prefix = "IMPC_" + id + "_" + zygosity + "_"
        for suffix in ["F", "FA", "M", "MA", "U", "UA"]:
            id = prefix + suffix
            if id not in models:
                models[id] = impc_model(id, category, row, zygosity)
                models[id].set_description("sex", sex_code(suffix))
                with_negative = negative_code(suffix)
                models[id].set_description("neg_phenotypes", with_negative)
    
    def add_to_model(datum, id, zygosity, suffix):
        """add a datum into an existing model definition.
        
        Arguments:
            datum      phenotype and experiment result
            id, zygosity, suffix
                       characterization of model
        """            
        id = "IMPC_" + id + "_" + zygosity + "_" + suffix        
        models[id].add(datum)
    
    def add_set_to_models(datum, row, val, sex):
        """helper to add a set of models, for alleles, markers
        
        Arguments:
            datum     phenotype and experiment result
            row       dict
            val       value of phenotype (0/1)
            sex       one-letter code
        """        
        zygosity = (row["zygosity"])[:3]
        zygosity = "hom" if zygosity == "hem" else zygosity            
        marker = row["marker_accession_id"]
        allele = row["allele_accession_id"]
        # perhaps create model definitions
        create_models(marker, "marker", zygosity, row)
        create_models(allele, "allele", zygosity, row)
        # record phenotypes into the models
        if val == 1:
            add_to_model(datum, marker, zygosity, sex)
            add_to_model(datum, allele, zygosity, sex)
        add_to_model(datum, marker, zygosity, sex+"A")
        add_to_model(datum, allele, zygosity, sex+"A")
    
    with open_file(datapath, "rt") as f: 
        reader = csv.DictReader(f, delimiter=",", quotechar="\"")        
        for row in reader:
            # skip over bad data rows
            if row["status"] != "Success": continue
            if row["allele_symbol"] == "": continue                                             
            phenotype = row["mp_term_id"].strip()
            if phenotype == "": continue
            
            # redefine some phenotypes
            parameter = row["parameter_name"].strip()
            if phenotype+" "+parameter in redef:
                phenotype = redef[phenotype+" "+parameter]
            if phenotype == "MP:0002169": continue
            
            sex = sex_code(row["phenotype_sex"])
            
            # identify whether this is a positive or a negative phenotype
            value = get_value(row, pthreshold)
            
            # add data at marker level, allele level, by gender
            hit = Experiment(value, base_tpr, base_fpr)                     
            datum = PhenotypeDatum(phenotype, hit, now)                            
            add_set_to_models(datum, row, value, "U")
            if sex in male:
                add_set_to_models(datum, row, value, "M")
            if sex in female:
                add_set_to_models(datum, row, value, "F")            

    # some models may have redundant rows (e.g. a phenotype recorded twice)
    # so collapse into a consensus here
    if simplify == "consensus":
        for id in models:
            models[id].consensus()            
    elif simplify == "average":
        for id in models:
            models[id].average()            
    return models
