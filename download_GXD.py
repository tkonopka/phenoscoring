"""
Utility to download mouse expression data from GXD

Usage: python3 download_GXD.py --ids ids.txt --output out_file
"""


import argparse
from intermine.webservice import Service
from time import sleep
from tools.files import open_file
from tools.files import values_in_column


# ##################################################################
# create a parser object

parser = argparse.ArgumentParser(description="download_GXD")

# for downloading data from GXD
parser.add_argument("--input", action="store", required=True,
                    help="file with column 'marker_id'")
parser.add_argument("--output", action="store", required=True, 
                    help="path to output file")
parser.add_argument("--sleep", action="store", default=0.02, 
                    help="interval between GXD requests")
parser.add_argument("--group_size", action="store", default=64, 
                    help="number of ids to query at a time")


# ##################################################################
# Helper to download expression data from mousemine


def mousemine_row(row):
    """convert a dictionary row into an array (in order of mousemine views)"""
    return [row[_] for _ in mousemine_views]


def download_mousemine(ids):
    """download data from mousemine (code adapted from intermine)
    
    Arguments:
        ids    iterable with ids to query
    """
    ids = ",".join(ids)
    query = mousemine.new_query("GXDExpression")
    query.add_view(" ".join(mousemine_views))    
    query.add_constraint("feature.organism.taxonId", "=", "10090", code = "B")
    query.add_constraint("feature", "LOOKUP", ids, "M. musculus", code = "A")
    return [mousemine_row(_) for _ in query.rows()]


# ##################################################################
# Execute the program if module is used as an executable

if __name__ == "__main__":
    config = parser.parse_args()    
    
    mousemine = Service("http://www.mousemine.org/mousemine/service")
    mousemine_views = ["assayType", "feature.symbol", "feature.primaryIdentifier",
                       "stage", "age", "structure.name", "strength", "pattern",
                       "genotype.symbol", "assayId", "probe", "image",
                       "publication.mgiJnum", "emaps", "structure.identifier"]
    
    # fetch all markers
    markers = set()    
    for filename in config.input.split(","):    
        markers.update(values_in_column(filename, "marker_id"))
    print("Working with "+str(len(markers))+" markers")
    
    # fetch data from mousemine
    markers = list(markers)    
    result = []
    for i in range(0, len(markers), config.group_size):
        imarkers = markers[i:(i+config.group_size)]
        print("querying: " + str(i) + " of " + str(len(markers)))       
        result.extend(download_mousemine(imarkers))
        sleep(config.sleep)
    print("done")

    # write expression data to disk
    with open_file(config.output, "wt") as f:
        f.write("\t".join(mousemine_views)+"\n")
        for row in result:
            f.write("\t".join([str(_) for _ in row]) + "\n")

