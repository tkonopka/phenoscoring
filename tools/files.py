"""Helper functions for working with files

@author: Tomasz Konopka
"""

import csv
import gzip
from os.path import exists, basename, dirname, join
from contextlib import contextmanager
 

def check_file(filepath, fallbackdir=None, required=None, allow_none=False):   
    """Try to find a file, either as-is or in a fallback directory
    
    Arguments:
        filepath       complete path to a file resources
        fallbackdir    path to a directory, 
            if file is not present at specified location, look here
        required        string, set to non-None to raise exception
        allow_none     boolean
    """
    
    if allow_none and filepath is None:
        return filepath
    
    if required is not None and filepath is None:
        raise Exception("Missing: " + required)
        
    if exists(filepath):
        return filepath
    
    if fallbackdir is not None:
        fallbackdir = dirname(fallbackdir)
        filepath = join(fallbackdir, basename(filepath))
    
    if exists(filepath):
        return filepath

    raise Exception("Cannot find file: "+filepath)


@contextmanager
def open_file(path, mode="rt"):
    """work with an open file using plain text or gzip"""
    
    open_fn = open
    if path.endswith(".gz"):
        open_fn = gzip.open
        
    file = open_fn(path, mode)
    yield file
    file.close()


def write_dict(data, filename, colnames=["id", "value"]):
    """Write a simple table file based on a dictionary"""
    
    if not filename.endswith(".gz"):
        filename += ".gz"
    
    header = "\t".join(colnames) + "\n"
    with gzip.open(filename, "w") as f:
        f.write(header.encode("utf-8"))
        for k,v in data.items():
            try:
                v_str = "\t".join([str(_) for _ in v])
            except TypeError:
                v_str = str(v)
            line = str(k)+"\t"+v_str+"\n"
            f.write(line.encode("utf-8"))


def values_in_column(filepath, column):
    """scan a file and get values from a given column"""
        
    result = []
    with open_file(filepath, "rt") as f:    
        reader = csv.DictReader(f, delimiter="\t", quotechar="'")
        for row in reader:
            result.append(row[column])
    return result

