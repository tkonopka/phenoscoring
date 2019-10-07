"""
Class that holds a matrix, with some additional helper functions.

This is essentially a matrix with some additional fields. 
Adding data into the matrix is through Representation objects.
"""


import numpy as np
from math import inf
from .distance import vec_norm, cosine_distances
from .distance import neighbor_average


class ReferenceMatrix():
    """A similar object to ReferenceSet, but implemented using numpy."""
    
    def __init__(self, refset, features):
        """Initialize the matrix based on an existing refset

        Arguments:
            refset     ReferenceSet object
            features   iterable with a set of features, used to cut feature in refset
        """
        
        # subset features to those that are consistent with the input refset
        new_features = set(features)
        for id in features:
            if id not in refset.rows:
                new_features.remove(id)
        
        # transfer some metadata from refset to this new object        
        self.column_priors = np.array(refset.column_priors.copy(), 
                                      dtype=float)
        self.columns = refset.columns.copy()
        self.column_names = refset.column_names.copy()
        
        self.row_names = tuple(list(new_features))        
        self.rows = dict()        
        for index, id in enumerate(self.row_names):                        
            self.rows[id] = index        
                        
        # transfer data from the refset into this object
        nrows = len(self.rows)
        self.data = np.zeros((nrows, len(self.columns)))
        for ref_index, ref_name in enumerate(self.column_names):
            repdata = refset.get_data(ref_name)
            reparr = [0.0] * nrows
            for feature_index, feature_name in enumerate(self.row_names):
                reparr[feature_index] = repdata[feature_name]
            self.data[:, ref_index] = reparr

        # pre-compute data column norms
        ncols = len(self.columns)
        self.data_norms = np.array([0.0] * ncols, dtype=float)
        for ref_index in range(ncols):
            self.data_norms[ref_index] = vec_norm(self.data[:, ref_index])

    def n_features(self):
        """obtain the number of features in this object"""
        return len(self.row_priors)

    def n_references(self):
        """obtain the number of references in this object"""
        return len(self.column_priors)

    def range(self, feature):
        """get min and max values for a given feature"""

        keyindex = self.rows[feature]
        return min(self.data[keyindex]), max(self.data[keyindex])
        
    def nearest_neighbors(self, source, k):
        """get indexes for k neighbors for a given source
        
        Arguments:
            source    name of reference
            k         integer, number of nearest neighbors to find
        
        Returns:
            list with k nearest neighbors
        """

        source_index = self.columns[source]
        sourcedata = self.data[:, source_index]
        distances = cosine_distances(sourcedata, self.data, self.data_norms)
        distances[source_index] = inf
        dist_index = [(distances[_], _) for _ in range(len(distances))]
        dist_index.sort()
        column_names = self.column_names
        return [column_names[dist_index[_][1]] for _ in range(k)]

    def get_average(self, references):
        """make a dictionary with a neighbor average."""

        neighbors = np.array([self.columns[_] for _ in references])
        n_features = len(self.rows)
        data = neighbor_average(self.data, self.column_priors, neighbors)
        result = dict.fromkeys(self.row_names, 0.0)
        for i in range(n_features):
            result[self.row_names[i]] = data[i]        
        return result    

    def get_data(self, reference):
        """extract data for one reference as a dict."""
        
        refindex = self.columns[reference]
        refdata = list(self.data[:, refindex])
        repdata = dict()
        for feature, index in self.rows.items():
            repdata[feature] = refdata[index]
        return repdata

