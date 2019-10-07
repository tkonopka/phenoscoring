"""
Write prepared model description and model phenotype files to disk.
"""

from tools.files import open_file
from phenoscoring.dbtables import ModelDescriptionTable
from phenoscoring.dbtables import ModelPhenotypeTable


def fwrite(f, msg, eol="\n"):
    """write a message into an open connection in utf8"""
    
    f.write((msg+eol))


def format_line(object, colnames, sep="\t", ndigits=5):
    """extract a series of components from object (musthave .get())"""
    
    result = []
    for key in colnames:
        data = object.get(key)
        if type(data) is float:
            datastr = str(round(data, ndigits))
        else:
            datastr = str(data)
        result.append(datastr)                
    return sep.join(result)


def write_descriptions(models, outfile, exclude=["timestamp"]):
    """ write a table with model descriptions."""
    
    colnames = ModelDescriptionTable.textfields
    colnames = [_ for _ in colnames if _ not in set(exclude)]
    with open_file(outfile, "wt") as f:        
        fwrite(f, "\t".join(colnames))
        for _, model in models.items():
            fwrite(f, format_line(model, colnames))
    
    
def get_colnames(TableClass, exclude):
    """get a list of column names from a table class"""
    
    # get all column names (except id, which will be entered separately)
    result = [_ for _ in TableClass.textfields]    
    result.extend(TableClass.realfields)    
    result = [_ for _ in result if _ not in set(exclude)]    
    return result


def write_model_phenotypes(models, outfile, exclude=["id", "timestamp"]):
    """write a table with phenotypes
    
    Arguments:
        models    dict with Model models
        outfile    path to output file
        exclude    set of columns to omit in output
    
    Returns:
        nothing, writes data into output file
    """
    
    # get all column names (except id, which will be entered separately)
    colnames = get_colnames(ModelPhenotypeTable, exclude)    
        
    with open_file(outfile, "wt") as f:        
        fwrite(f, "id\t"+ "\t".join(colnames))
        for key, object in models.items():            
            for d in object.data:
                fwrite(f, object.id + "\t" + format_line(d, colnames))


def write_models(models, outprefix):
    """write data from a set of models into output files"""
            
    write_descriptions(models, 
                       outprefix + "-models.tsv.gz")
    write_model_phenotypes(models, 
                           outprefix + "-phenotypes.tsv.gz")


def write_references(references, outprefix):
    """write phenotypes for a set of references into output files."""
            
    outfile = outprefix +"-phenotypes.tsv.gz"
    colnames = ["id", "phenotype", "value"]        
    with open_file(outfile, "wt") as f:        
        fwrite(f, "\t".join(colnames))
        for key, object in references.items():
            for phenotype, value in object.data.items():
                fwrite(f, "\t".join([key, phenotype, str(value)]))


def write_priors(priors, outprefix):
    """write phenotype priors to an output files."""
            
    outfile = outprefix + "-priors.tsv.gz"
    with open_file(outfile, "wt") as f:
        fwrite(f, "\t".join(["phenotype", "value"]))
        for phenotype, value in priors.items():
            fwrite(f, phenotype+"\t"+str(value))
    

def write_hits_summary(tested, hits, outprefix):
    """write a table linking parameters, MP, to number of markers."""
    
    header = ["parameter", "MP_term", 
              "markers_tested", "markers_significant"]
    
    outfile = outprefix+"-hits-summary.tsv.gz"
    with open_file(outfile, "wt") as f:
        fwrite(f, "\t".join(header))
        for key in tested:            
            num_tested = str(len(tested[key]))
            num_hits = str(len(hits[key]))
            fwrite(f, key+"\t"+num_tested+"\t"+num_hits)


def write_phenotype_cooc(cooc, phenindex, outprefix):
    """write a table summarizing co-occurance of phenotypes."""    
    
    header = ["A", "B", "value"]
    
    outfile = outprefix+"-cooc.tsv.gz"        
    with open_file(outfile, "wt") as f:
        fwrite(f, "\t".join(header))
        for p1, i1 in phenindex.items():            
            for p2, i2 in phenindex.items():                
                if cooc[i1,i2] == 0:
                    continue
                line = [p1, p2, str(cooc[i1, i2])]
                fwrite(f, "\t".join(line))                    


def write_oo(ooarray, outprefix):
    """write a table summarizing ontology-ontology mapping."""
    
    header = ["term1", "term2", "score"]
    outfile = outprefix + "-oomap.tsv.gz"
    with open_file(outfile, "wt") as f:
        fwrite(f, "\t".join(header))
        for data in ooarray:
            fwrite(f, "\t".join([str(_) for _ in data]))

