"""A container holding a model for the Phenoscoring DB

@author: Tomasz Konopka
"""

from .time import now_timestamp


class PhenotypeDatum():
    """Container for an experiment result, value=0/1, TPR/FPR."""
    
    def __init__(self, phenotype, experiment, timestamp = None):                  
        """object holding a phenotype association
        
        Arguments:
            phenotype    string identifier for a phenotype
            experiment   object summarizing a hit/nohit, tpr, fpr
            timestamp    time associated with            
        """
        
        self.phenotype = phenotype
        self.experiment = experiment
        
        # copy additional descriptors into a dict        
        if timestamp is None:
            self.timestamp = now_timestamp()
        else:
            self.timestamp = timestamp                
    
    
    def get(self, key):
        """extract a single components from the datum."""
        
        if key == "phenotype" or key == "timestamp":
            return self.__getattribute__(key)
        elif key == "TPR" or key == "tpr":
            return self.experiment.tpr
        elif key == "FPR" or key == "fpr":
            return self.experiment.fpr
        elif key == "value":
            return self.experiment.value

    
    @property
    def value(self):
        return self.experiment.value
    
    @property
    def tpr(self):
        return self.experiment.tpr
    
    @property
    def fpr(self):
        return self.experiment.fpr

        
    def __str__(self):
        """a string with all the data in the object."""
        
        result = (str(self.phenotype),
                  str(self.experiment),
                  str(self.timestamp))
        return "PhenotypeDatum(" + ",".join(result) + ")"


    def __eq__(self, other):
        """check for equivalence, used for == comparisons."""
        if self.phenotype != other.phenotype:
            return False
        if self.experiment != other.experiment:
            return False
        return self.timestamp == other.timestamp
        

    def __lt__(self, other):
        """ordering of elements, used for sorting."""
        
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        if self.phenotype != other.phenotype:
            return self.phenotype < other.phenotype
        return self.experiment < other.experiment

    
    def __repr__(self):
        return self.__str__()
