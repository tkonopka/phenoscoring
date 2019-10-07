"""
Phenojoin.py

Joining data from IMPC and MGI into JOINT models
"""


import argparse
from phenoprep.write import write_models
from phenoscoring.update import get_file_models, get_file_phenotypes
from tools.files import check_file
from phenoscoring.time import now_timestamp


# ##################################################################
# create a parser object for the phenoscoring executable

parser = argparse.ArgumentParser(description="phenoscoring-join")

# location of input and output data files
parser.add_argument("--impc_desc", action="store", required=True,
                    help="impc model descriptions")
parser.add_argument("--impc_phen", action="store", required=True,
                    help="impc model phenotypes")
parser.add_argument("--mgi_desc", action="store", required=True,
                    help="mgi model descriptions")
parser.add_argument("--mgi_phen", action="store", required=True,
                    help="mgi model phenotypes")

parser.add_argument("--output", action="store", required=True,
                    help="prefix for output files")


# ##################################################################
# Execute the program if module is used as an executable


if __name__ == "__main__":    
        
    config = parser.parse_args()            
    config.impc_desc = check_file(config.impc_desc, required="impc_desc")
    config.impc_phen = check_file(config.impc_phen, required="impc_phen")
    config.mgi_desc = check_file(config.mgi_desc, required="mgi_desc")
    config.mgi_phen = check_file(config.mgi_phen, required="mgi_phen")
    timestamp = now_timestamp()
    
    # load impc and mgi models into memory
    impc_models = get_file_models(config.impc_desc, timestamp)
    impc_phenotypes = get_file_phenotypes(config.impc_phen, timestamp)
    mgi_models = get_file_models(config.mgi_desc, timestamp)
    mgi_phenotypes = get_file_phenotypes(config.mgi_phen, timestamp)
    
    # get all allele_ids from impc and mgi
    def model_alleles(models):
        """scan a set of models and get a set of allele_id"""
        result = set()
        for model_id, entity in models.items():
            if entity.category != "allele" and entity.category != "genotype":
                continue
            result.add(entity.get("allele_id"))
        return result
    impc_alleles = model_alleles(impc_models)
    mgi_alleles = model_alleles(mgi_models)
    common_alleles = impc_alleles.intersection(mgi_alleles)
    
    
    def az(entity):
        """get a string with allele_id and zygosity."""
        return entity.get("allele_id") + "_" + entity.get("zygosity")
    
    
    # create a set of models with joint data
    az2id = dict()
    out_models = dict()
    for id, entity in impc_models.items():
        if entity.get("allele_id") not in common_alleles:
            continue
        if entity.get("category") != "allele":
            continue
        entity.id = entity.id.replace("IMPC", "JOINT")
        entity.category = "joint"
        entity.set_description("background", "NA")
        entity.set_description("source", "JOINT")
        out_models[entity.id] = entity
        entity_az = az(entity)
        if entity_az not in az2id:
            az2id[entity_az] = set()
        az2id[entity_az].add(entity.id)

    # create a mapping from mgi model id to joint model ids
    mgi2id = dict()
    for id, entity in mgi_models.items():
        entity_az = az(entity)
        if entity_az not in az2id:
            continue
        mgi2id[id] = az2id[entity_az]
    
    # transfer IMPC phenotypes 
    for id, phenotypes in impc_phenotypes.items():
        newid = id.replace("IMPC", "JOINT")
        if newid not in out_models:
            continue
        for datum in phenotypes:
            out_models[newid].add(datum)
    # transfer MGI phenotypes
    for id, phenotypes in mgi_phenotypes.items():
        if id not in mgi2id:
            continue
        for joint_id in  mgi2id[id]:
            for datum in phenotypes:
                out_models[joint_id].add(datum)
    
    # write the final result into a file
    write_models(out_models, config.output)

