"""A helper function to write a ReferenceSet to disk

@author: Tomasz Konopka
"""


import gzip
import json

    
def write_refset(refset, fileprefix, first_colname=""):
    """Dump contents of ReferenceSet to a set of files.
    
    Args:
        refset:      object of class ReferenceSet
        fileprefix:  full path to output, 
                     individual files will have suffixes
    """
    
    data_file = fileprefix+"_data.tsv.gz"
    column_file = fileprefix+"_column_priors.json"
    row_file = fileprefix+"_row_priors.json"
    
    nrow = len(refset.rows)
    ncol = len(refset.columns)

    row_priors = dict()
    for index, name in enumerate(refset.row_names):
        row_priors[name] = refset.row_priors[index]
    with open(row_file, "w") as f:
        f.write(json.dumps(row_priors, indent=2))

    column_priors = dict()
    for index, name in enumerate(refset.column_names):
        column_priors[name] = refset.column_priors[index]
    with open(column_file, "w") as f:
        f.write(json.dumps(column_priors, indent=2))
        
    with gzip.open(data_file, "w") as f:
        outstr= first_colname + "\t" + "\t".join(refset.column_names)+"\n"
        f.write(outstr.encode("utf-8"))
        for i in range(nrow):
            iname = refset.row_names[i]
            idata = [str(refset.data[_][i]) for _ in range(ncol)]
            outstr = iname+ "\t"+ "\t".join(idata)+"\n" 
            f.write(outstr.encode("utf-8"))

