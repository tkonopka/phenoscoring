"""Class holding details of an experiment: hit/non-hit, tpr, fpr

@author: Tomasz Konopka
"""

from math import log2
import copy
import json
import jsonpickle


def update_single(p, tpr, fpr):
    """a single p update."""
    
    if tpr == fpr:
        return p
    return (tpr*p)/(((tpr-fpr)*p) + fpr) 


def update_single_ratio(p, fpr_tpr):
    """a single p update using a ratio of fpr/tpr"""
    
    if fpr_tpr == 1:
        return p
    return p / (((1-fpr_tpr)*p) + fpr_tpr) 


def reglog2(p, reg_lower=-32, reg_upper=32):
    """regularized logarithm"""
    
    try:
        plog = log2(p)
    except ValueError:
        if p < pow(2, reg_lower):
            plog = reg_lower
        elif p > pow(2, reg_upper):
            plog = reg_upper
    return plog


def evidence_update(p, tpr_list, fpr_list, reg_lower=-512, reg_upper=512):
    """Update a probability p given (tpr, fpr) evidence.
    
    This implementation uses sums of logarithms for long lists
    
    Args: 
        p:         float
        tpr_list:  list of true-positive values
        fpr_list:  list of false-positive values
        reg_lower  regularization, 
          fpr/tpr < 2^(reg_lower) will be adjusted
        reg_upper  regularization number,
          fpt/tpr > 2^(reg_upper) will be adjusted       
    """
            
    fpr_logprod = tpr_logprod = 0.0
    for tpr, fpr in zip(tpr_list, fpr_list):
        if tpr == fpr:
            continue
        tpr_logprod += reglog2(tpr, reg_lower, reg_upper)
        fpr_logprod += reglog2(fpr, reg_lower, reg_upper)                
        
    expodiff = max(reg_lower, min(reg_upper, fpr_logprod-tpr_logprod))        
    return update_single_ratio(p, pow(2, expodiff))
  

def estimate_update_ratio(prior, posterior):
    """estimate a fpr/tpr ratio based on prior and posteriors."""
    
    pp = prior*posterior
    return (pp - prior) / (pp - posterior)


def estimate_update(p, prior, posterior):
    """estimate an update given an earlier enrichment"""
    
    update_ratio = estimate_update_ratio(prior, posterior)
    return update_single_ratio(p, update_ratio)


class EvidenceDatum():
    """Generic class that can set an annotation key/value.
    This is essentially a dict(), with some helper functions.   
    """
        
    def set_annotation(self, key, value):
        """add an extra annotation to this datum."""
        
        self.__dict__[key] = value

    def round(self, decimal_places=8):
        """get a copy of this datum with all numbers rounded."""
        
        result = self.copy()        
        for key, value in self.__dict__.items():
            if type(value) is float:
                value = round(value, decimal_places)
                result.__dict__[key] = value
        return result

    def copy(self):
        """create a copy of itself."""        
        return copy.copy(self)

    def __str__(self):
        """create json representation of object's data."""
        return json.dumps(self.__dict__)


class InferenceDatum(EvidenceDatum):
    """One component for an inference chain. """
    
    def __init__(self, tpr, fpr):       
        self.tpr = tpr
        self.fpr = fpr


class EvidenceChain():
    """A record encoding an inference calculation based on several data"""
    
    def __init__(self, **kwargs):
        """create a record of an inference procedure."""
        
        self.data = []
        if kwargs is not None:
            for k,v in kwargs.items():
                self.__dict__[k] = v

    def set_annotation(self, key, value):
        """add an annotation key/value pair."""
        
        self.__dict__[key] = value
        return self

    def has_annotation(self, key):
        return key in self.__dict__

    def add(self, datum):
        """add an element of data to the experiment chain.
        For inference data, this will regularize the tpr,fpr fields.
        
        Args:
            datum:      object of type InferenceDatum or CoverageDatum
            reg_lower:  lower bound for tpr,fpr fields
            reg_upper:  upper bound for tpr, fpr fields
        """   
                
        self.data.append(datum)
        return self

    def evaluate_inference(self):
        """compute posterior probability given inference data.""" 
        
        # transfer TPR, FPR from data elements into lists
        tpr = [0]*len(self.data)
        fpr = [0]*len(self.data)
        for i, datum in enumerate(self.data):            
            tpr[i] = datum.tpr
            fpr[i] = datum.fpr                
        
        self.posterior = evidence_update(self.prior, tpr, fpr)                    
        return self.posterior

    def evaluate(self):
        """compute posterior given prior and data."""

        return self.evaluate_inference()

    def to_json(self, decimal_places=8, nodata=False):
        """turn the data into a json representation."""
        
        # evaluate inference probability
        self.evaluate()
        
        # create a copy of this chain
        result = copy.deepcopy(self)
        
        if nodata:
            result.data = []
            
        # adjust all values in data (rounded numbers)
        for index, datum in enumerate(result.data):
            result.data[index] = datum.round()
            
        return jsonpickle.encode(result.__dict__, unpicklable=False)

    def __str__(self):
        """create a json representation of the evidence chain."""
        
        # for printing on screen, using json's indenting
        jsonstr = self.to_json()
        return json.dumps(json.loads(jsonstr), indent=2)


class InferenceChain(EvidenceChain):
    
    def __init__(self, prior, **kwargs):
        """initialize a chain with a prior probability."""
        super(InferenceChain, self).__init__(**kwargs)
        self.prior = prior

    
class LeanInferenceChain():
    """Another evidence chain class that has only add and evaluate functions."""

    def __init__(self, prior, **kwargs):
        """initialize a calculation with a prior and empty tpr/fpr.
        In this implementation, kwargs are ignored.
        """
        self.prior = prior
        self.tpr = []
        self.fpr = []

    def add(self, tprfpr):
        """add an element of data to the evidence chain
        
        Arguments:
            datum 
        """        
        if tprfpr[0] != tprfpr[1]:      
            self.tpr.append(tprfpr[0])
            self.fpr.append(tprfpr[1])        

    def evaluate(self):
        """always evaluates based on tpr and fpr data."""

        self.posterior = evidence_update(self.prior, self.tpr, self.fpr)
        return self.posterior        

