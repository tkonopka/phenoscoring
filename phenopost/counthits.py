"""
Count hits to references
"""


from db.generator import DBGenerator
from phenoscoring.dbtables import ModelScoreTable
from phenoscoring.dbhelpers import get_ref_names


def get_highscore_pairs(dbpath, threshold):
    """get an array of pairs (model, reference) with high scores."""
    
    result = []    
    generator = DBGenerator(ModelScoreTable(dbpath))
    for row in generator.next():
        if row["general"] > threshold and row["specific"] > threshold:
            result.append((row["model"], row["reference"]))
    return result


def count_hits(dbpath, threshold1, threshold2=None):    
    """count the number of models that score against each reference
    
    Arguments:
        dbpath       path to phenoscoring db
        threshold1   minimum general and specific scores for a tier-1 hit
        threshodl2   minimum general and specific scores for a tier-2 hit
    
    Returns:
        dict mapping reference names to a 2-tuple with model counts
    """

    if threshold2 is None:
        threshold2 = threshold1
                
    refnames = get_ref_names(dbpath)
    counts_t1 = dict.fromkeys(refnames, 0)
    counts_t2 = dict.fromkeys(refnames, 0)
    
    # collect hits above first threshold, second threshold
    pairs = get_highscore_pairs(dbpath, threshold1)
    for _, refname in pairs:
        counts_t1[refname] += 1
    pairs = get_highscore_pairs(dbpath, threshold2)
    for _, refname in pairs:
        counts_t2[refname] += 1
    
    result = dict.fromkeys(refnames, None)
    for ref in refnames:
        result[ref] = (counts_t1[ref], counts_t2[ref])
        
    return result    
