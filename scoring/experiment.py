"""
Class holding details of an experiment: hit/non-hit, tpr, fpr
"""


class Experiment():
        
    def __init__(self, value=1, tpr=0.8, fpr=0.05):
        """Create new experiment object.
        
        Args:
            value:    logical, set True if experiment gave significant result
            tpr:    true positive rate of test
            fpr:    false positive rate of test
        """
        
        self.value = value
        self.tpr = tpr
        self.fpr = fpr        

    def update(self, p):
        """Update a probability p given evidence from this test."""
        
        if self.tpr==self.fpr:
            return p

        if self.value:
            tau = self.tpr
            phi = self.fpr
        else:
            tau = 1-self.tpr
            phi = 1-self.fpr
                            
        return (tau*p)/(((tau-phi)*p) + phi)

    def __str__(self):
        """provide a string summarizing the experiment."""
        
        temp = "Experiment("
        return temp+str(self.value)+", "+str(self.tpr)+", "+str(self.fpr)+")"                    

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __lt__(self, other):
        """ordering, used for sorting."""
        
        if self.value != other.value:
            return self.value < other.value
        if self.tpr != other.tpr:
            return self.tpr < other.tpr
        return self.fpr < other.fpr


class PositiveExperiment(Experiment):
    """A special case of Experiment with positive outcome (value>0)."""
    
    def __init__(self, tpr=0.8, fpr=0.05):
        super().__init__(1, tpr, fpr)


class NegativeExperiment(Experiment):
    """A special case of Experiment with negative outcome (value=0)."""
    
    def __init__(self, tpr=0.8, fpr=0.05):
        super().__init__(0, tpr, fpr)

