"""Utilities to extract summaries from obo ontology files.

Usage: python3 obotools.py command --obo INFILE

@author: Tomasz Konopka
"""


import argparse
from obo.obo import Obo, minimal_obo


# ##################################################################
# create a parser object for the phenoscoring executable

parser = argparse.ArgumentParser(description="obotools")

parser.add_argument("command", action="store",
                    help="Name of utility to execute",
                    choices=["alts", "ancestors", "names", "parents",
                             "obsolete", "minimize"])
parser.add_argument("--obo", action="store", help="ontology")


# ##################################################################
# Execute the program if module is used as an executable


if __name__ == "__main__":
    
    config = parser.parse_args()    

    obo = Obo(config.obo)

    if config.command == "alts":
        # extract alternate ids
        print("id\talt_id")
        for term in obo.ids(True):
            if not obo.valid(term):
                continue
            for a in obo.alts(term):
                print(term + "\t" + a)

    elif config.command == "ancestors":
        # extract a table of term ancestors
        print("id\tancestors")
        for term in obo.ids():
            ancestors = obo.ancestors(term)
            print(term + "\t" + ";".join(ancestors))

    elif config.command == "names":
        # extract a table of term titles
        print("id\tname")
        for term in obo.ids():
            print(term + "\t" + obo.name(term))

    elif config.command == "parents":
        # extract parents of ontology terms
        print("id\tparent")
        for term in obo.ids():
            for p in obo.parents(term):
                print(term + "\t" + p)

    elif config.command == "minimize":
        # write out a new obo-like file, but with minimal content
        minimal_obo(config.obo)

    elif config.command == "obsolete":
        # extract obsolete terms and their replacements
        print("id\treplaced_by")
        for term in obo.ids(True):
            if obo.valid(term):
                continue
            replaced_by = obo.replaced_by(term)
            replaced_by = "" if replaced_by is None else replaced_by
            print(term + "\t" + replaced_by)
