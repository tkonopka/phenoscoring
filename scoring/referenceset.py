"""
Class that holds a set of reference representations.

This is essentially a matrix with some additional fields. 
Adding data into the matrix is through Representation objects.
"""

from operator import itemgetter
from math import log10, tanh
from .evidence import InferenceDatum, estimate_update
from .evidence import InferenceChain, LeanInferenceChain
from .representation import Representation
from .comparisoncodes import comparison_code
from .write import write_refset
from collections import Counter


class ReferenceSet():    
    """Data frame and auxiliary information/functions."""

    def __init__(self, priors, ids, row_priors=None):
        """create a set of reference representations.
        
        Arguments:
            priors        dict with prior probabilities for all references.
            ids           list of all the feature names
            row_priors    dict with prior probabilities for all features.          
        """ 

        # mappings from feature ids to indexes
        self.rows = dict()
        # mapping from indexes to feature ids
        self.row_names = tuple(ids)
        # array and dict with row priors
        self.row_priors = [1.0] * len(ids)
        self.feature_priors = dict()
        for index, feature in enumerate(self.row_names):
            self.rows[feature] = index
            if row_priors is not None:
                self.row_priors[index] = row_priors[feature]
                self.feature_priors[feature] = row_priors[feature]
            else:
                self.feature_priors[feature] = 1.0
        
        # mappings from reference ids to indexes, reverse, and priors
        self.columns = dict()
        self.column_names = [None] * len(priors)
        self.column_priors = [1.0] * len(priors)
        self.reference_priors = priors.copy()
        for refname in priors.keys():
            index = len(self.columns)
            self.columns[refname] = index
            self.column_names[index] = refname
            self.column_priors[index] = priors[refname]
        
        # data store as nested arrays
        # first index is reference index, second is feature index        
        self.data = [None] * len(self.columns)
        for _ in range(len(self.columns)):
            self.data[_] = [0.0] * len(self.rows)
        
        # map to ontology parents
        self.parents = None
        
        # cache for finding positive parents during FP inference calculations
        self.cache = dict()
        self.temp = Counter()
        
        
    def learn_obo(self, obo):
        """extract parent-of relations from ontology"""

        self.parents = [None] * len(self.row_names)
        for index, feature in enumerate(self.row_names):
            parent_names = obo.parents(feature)
            parent_indexes = [self.rows[_] for _ in parent_names]
            self.parents[index] = tuple(parent_indexes)            

    def add(self, representation):
        """transfer data from a representation into this set"""
        
        if type(representation) is not Representation:
            raise Exception("input must be of type Representation")
        name = representation.name        
        if name is None:
            raise Exception("representation does not have a name")
        if name not in self.columns:
            raise Exception("representation is not compatible")
                                            
        refindex = self.columns[name]
        refdata = self.data[refindex]
        for key in representation.keys():            
            refdata[self.rows[key]] = representation.data[key]        
        
        return self

    def get(self, feature, reference):
        """Extract a value for a feature/reference."""
        keyindex = self.rows[feature]
        refindex = self.columns[reference]
        return self.data[refindex][keyindex]

    def get_representation(self, reference):
        """Extract a whole representation for one reference."""
        
        return Representation(data=self.get_data(reference), name=reference) 

    def get_data(self, reference):
        """extract data for one reference as a dict."""
        
        refindex = self.columns[reference]
        refdata = self.data[refindex]
        result = dict()
        for feature, index in self.rows.items():
            result[feature] = refdata[index]
        return result

    def names(self):
        """get a list of all the reference names in this set."""
        
        return self.column_names.copy()

    def prep(self):
        """compute background probabilities of all features."""
                
        # create a dict with prior probabilities
        self.row_priors = [0.0]*len(self.rows)
        self.feature_priors = dict()
        
        # denominator is given by reference priors
        denominator = sum(self.column_priors)
        # null_feature_prior is used when feature is not observed at all
        # this is set up to scale with features, i.e. arbitrarily adding
        # child features into an ontology should not skew sums over repr.
        null_feature_prior = 1/max(denominator, float(len(self.rows)))
                
        for rowname, rowindex in self.rows.items():            
            numerator = 0
            for colname, colindex in self.columns.items():                
                colprior = self.column_priors[colindex]
                numerator += self.data[colindex][rowindex]*colprior
            if numerator == 0:
                numerator = null_feature_prior            
            self.row_priors[rowindex] = float(numerator)/denominator
            self.feature_priors[rowname] = self.row_priors[rowindex]

        return self        

    def _find_positive_ancestor(self, refdata, seedindex):
        """Traverse obo; find a node with value greater than its prior
        
        Args:
            refdata:     list with data for the reference
            seedindex:   index of feature (within this reference set)
            
        Returns:
            tuple of length 2. 
            First element: a feature index.
            Second element: score for the enrichment wrt to the prior
        """ 
        
        seedval = refdata[seedindex]
        if seedval > self.row_priors[seedindex]:        
            return seedindex, -seedval/self.row_priors[seedindex]
        
        # find parents of seed
        parents = self.parents
        seedparents = parents[seedindex]
        parents_len = len(seedparents)
        if parents_len == 0:
            return None, 0
        elif parents_len == 1:
            return self._find_positive_ancestor(refdata, seedparents[0])
        elif parents_len == 2:
            # handle special case when there are only two items
            # instead of doing a general query and sort, pick best of two                
            r0 = self._find_positive_ancestor(refdata, seedparents[0])
            r1 = self._find_positive_ancestor(refdata, seedparents[1])
            if r1[1] < r0[1]:
                return r1    
            return r0        
        
        # study multiple paths toward root, return most enriched
        result = [self._find_positive_ancestor(refdata, _) for _ in seedparents]        
        return min(result, key=itemgetter(1))
        
    def _positive_ancestor(self, refindex, seedindex):
        """Traverse obo, find a node with value greater than prior.
        
        This is a wrapper for _find_positive_ancestor. This saves results into 
        a cache so that the same calculation is not repeated many times. 
        
        Args:
            refindex    integer, identifier for reference
            seedindex   integer, identifier for a feature
        
        Returns:
            integer index for a feature for which the reference is positive
        """
       
        key = (len(self.row_names)*refindex) + seedindex
        if key in self.cache:
            return self.cache[key]
        
        refdata = self.data[refindex]
        result = self._find_positive_ancestor(refdata, seedindex)[0]
        self.cache[key] = result
        return result

    def inference_chain(self, model, target, verbose=False, fp_penalty=1):
        """Construct an evidence chain for comparing a model to a reference

        Arguments:
            model       Representation object
            target      string with a reference name
            verbose     logical set to obtain less/more detail in output
            fp_penalty  numeric value determines handling of false positives

        Returns:
            an EvidenceChain        
        """

        refindex = self.columns[target]
        prior = self.column_priors[refindex]
        refdata = self.data[refindex]
        
        row_priors = self.row_priors
        #parents = self.parents
        rows = self.rows        

        InfChainClass = InferenceChain if verbose else LeanInferenceChain
        result = InfChainClass(prior, reference=target, model=model.name)

        for feature, model_val in model.data.items():                    
            # determine prior, reference, background values
            ifeature = rows[feature]
            ref_val, bg = refdata[ifeature], row_priors[ifeature]
            
            # avoid calculation if ref_val or model_val are bg
            if (model_val == bg or ref_val == bg) and not verbose:
                continue                                
            
            # create an evidence items with an initial tpr, fpr
            tpr, fpr = model_val, bg
            datum = (tpr, fpr)
            alpha = 0             
            if verbose:
                datum = InferenceDatum(tpr, fpr)
            
            if model_val > bg and ref_val > bg:
                # True positive
                tpr = model_val
                fpr = bg
                alpha = (ref_val - bg) / (1-bg)              
            
            elif model_val > bg and ref_val < bg:
                # False positive                
                iancestor = self._positive_ancestor(refindex, ifeature)                                
                if iancestor is None:
                    ancestor_val, ancestor_bg = 1, 1
                else:                                    
                    ancestor_bg = row_priors[iancestor]
                    ancestor_val = refdata[iancestor]
                if verbose:
                    parent = "NA"
                    if iancestor is not None:
                        parent = self.row_names[iancestor]
                    datum.set_annotation("ancestor_feature", parent)
                    datum.set_annotation("ancestor_bg", ancestor_bg)
                    datum.set_annotation("ancestor_value", ancestor_val)                
                # adjust probabilities with a combination
                # first adjustment can only bring score up
                beta = tanh(fp_penalty * log10(ancestor_bg/bg))                            
                ancestor_estimate = estimate_update(ancestor_bg, bg, model_val)
                tpr0 = ancestor_estimate*(1-beta) + ancestor_bg*beta
                fpr0 = ancestor_bg                
                # second part of FP calculation, reduce tpr to penalize far-away FPs                 
                tpr = tpr0 * (1 - model_val)
                fpr = fpr0 * (1 - bg)
                if ancestor_val > bg:
                    alpha = (ancestor_val - bg) / (1-bg)                
                
            elif model_val < bg and ref_val > bg:
                # False Negative
                tpr = (1 - bg)
                fpr = (1 - model_val)
                alpha = (ref_val - bg) / (1 - bg)             
                
            elif model_val < bg and ref_val < bg:
                # True Negative
                tpr = (1 - model_val)
                fpr = (1 - bg)
                alpha = (bg-ref_val) / bg
            
            else:
                # do nothing (this is when model_val==bg or ref_val==bg)
                if verbose:                    
                    fpr = tpr = bg                    
                else:
                    datum = None            
            
            if datum is not None:
                # interpolate based on strength of reference value
                # alpha ~ 0 means weak reference, no adjustment
                # alpha ~ 1 means strong reference, full tpr/fpr adjustment
                tpr = alpha*tpr + (1-alpha)*fpr                
                             
                if verbose:
                    datum.tpr = tpr
                    datum.fpr = fpr                                        
                    datum.set_annotation("feature", feature)
                    datum.set_annotation("reference", ref_val)
                    datum.set_annotation("background", bg)
                    datum.set_annotation("model", model_val)
                    action = comparison_code(model_val, ref_val, bg)
                    datum.set_annotation("result", str(action))
                else:
                    datum = (tpr, fpr)
                result.add(datum)
        
        return result

    def inference(self, model, target=None, fp_penalty=1, verbose=False):
        """compute inference scores to severage references
        
        This function assumes row_priors and column_priors are set.
        They must be set either manually, or via self.prep()
        
        Args:
            model        Representation object        
            target       list of reference names to score target
            fp_penalty   numeric, weight for false positives
            verbose     logical, passed on to inference_chain
        
        Returns:
            dictionary
        """

        if target is None:
            target = list(self.columns.keys())
                    
        result = dict.fromkeys(target, 0)
        for ref in target:
            echain = self.inference_chain(model, ref, 
                                          fp_penalty=fp_penalty, verbose=verbose)                        
            result[ref] = echain.evaluate()            
            
        return result

    def save(self, fileprefix, first_colname=""):
        """Dump contents of this array to a set of files."""
                
        write_refset(self, fileprefix, first_colname=first_colname)

    def __str__(self):
        """Provide a description of some of the data in the reference set."""
        
        result = ["rows: " + str(self.rows)]
        result.append("columns: "+str(self.columns))
        result.append("data: "+str(self.data))
        return "\n".join(result)

