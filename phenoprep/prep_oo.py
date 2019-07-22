"""Prep data from owlsim ontology-ontology mapping

@author: Tomasz Konopka
"""

from tools.files import open_file


class OOset:
    """collect and manage ontology-ontology mappings."""
    
    def __init__(self, term1=None):
        self.term1 = term1
        self.data = []
            
    def add(self, term2, score, digits=6):
        self.data.append((self.term1, term2, round(score, digits)))
            
    def best_score(self):
        """find the numeric best score in self.data"""
        
        result = -float("inf")
        for d in self.data:
            result = max(result, d[2])
        return result                
    
    def best_terms(self):
        
        result = set()
        best_score = self.best_score()
        for d in self.data:
            if d[2] == best_score:
                result.add(d[1])
        return result, best_score
    
    def hits(self, obo=None, siblings=True):
        """output an array of best mappings
        If siblings is True, also output siblings of best hits."""
                
        best_terms, best_score = self.best_terms()
        
        # define a set of hit terms (perhaps siblings of hits)
        use_terms = best_terms.copy()
        if siblings:
            for t in best_terms:
                use_terms.update(obo.siblings(t))        
        
        # construct a subset of the results
        result = []
        for d in self.data:
            if d[1] in use_terms:
                result.append(d)        
        return result    


def prep_oo(owlfile, obo, siblings=False):
    """Scans one file and identify best 1-to-1 ontology mappings."""
    
    okterms = set(obo.ids())
        
    result = []
     
    # scan file, collect lines into an OOset, then remember best hits
    with open_file(owlfile, "rt") as f:
        state = OOset()        
        for line in f:                
            tokens = line.split("\t")
            tokens[0] = tokens[0].replace("_", ":")
            tokens[1] = tokens[1].replace("_", ":")
            # skip over mapping to terms that are not in the ontology
            if tokens[1] not in okterms:
                continue            
            # perhaps reset the OOset
            if tokens[0] != state.term1:
                if state.term1 is not None:
                    result.extend(state.hits(obo, siblings=siblings))
                state = OOset(tokens[0])    
            # add the mapping into the current store
            state.add(tokens[1], float(tokens[2])*float(tokens[3]))            
        if state.term1 != "":
            result.extend(state.hits(obo, siblings=siblings))
                
    return result
