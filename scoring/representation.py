"""
Class that holds a representation of experimental data.

This just holds a dict with a phenotype-associated API.
"""

from math import isclose


class Representation():    
    """An object that hold values associated with phenotypes."""
    
    def __init__(self, data=None, name=None):
        """new representation with some key-value data.""" 
        
        self.data = dict()
        if data is not None:
            for k, v in data.items():
                self.data[k] = float(v)
        self.name = name           

    def copy(self, name=None):
        """create a new object with a copy of the data
        
        :param name: string, name for new Representation
        """
                
        if name is None:
            name = self.name        
        result = Representation(name=name)
        result.data = self.data.copy()
        return result

    def impute(self, obo, defaults, seeds=None):
        """update the values in this representation using an ontology.

        :param obo: object of class ontologies.obo
        :param defaults: default values for all terms in the ontology.
        :param seeds: list of keys, imputation starts from these elements in
            specified order. If None, functions starts from all existing keys.
        """
                
        # add defaults to existing representation
        self.defaults(defaults)
        original = self.data.copy()
        current = self.data                
        
        def update_factor(key, factor, use_prior):
            val = current[key]
            if val is None:
                if use_prior:
                    val = 1-defaults[key]
                else:
                    val = 1
            current[key] = val*factor                   
                
        def propagate_up(key, factor):
            update_factor(key, factor, False)                
            for node in obo.ancestors(key):
                update_factor(node, factor, True)
        
        def propagate_down(key, value):
            if current[key] <= defaults[key]:
                current[key] = value
            for node in obo.descendants(key):                                
                if current[node] <= defaults[node] and value < current[node]:
                    current[node] = value                
                
        # get a list of current items with values
        # (sorted by value, from high to low)
        if seeds is None:
            temp = [(v,k) for k,v in current.items()]
            temp.sort(reverse=False)
            seeds = [k for v, k in temp]
        
        # Update up-the-tree using OR logic
        for key in original.keys():
            current[key] = None            
        # first set self.data to values (1-p), then reverse in 2nd loop
        for key in seeds:
            if key not in defaults:
                continue
            keyval = original[key]
            if keyval > defaults[key]:
                propagate_up(key, 1-keyval)
        for key in original.keys():
            if current[key] is None:
                current[key] = original[key]
            else:
                current[key] = 1 - current[key]
        
        # Update down the tree by direct propagation
        for key in seeds:                    
            if key not in defaults:
                continue
            keyval = original[key]
            if keyval < defaults[key]:
                propagate_down(key, keyval)
        
        return self

    def keys(self):
        return list(self.data.keys())

    def has(self, key):
        return key in self.data

    def get(self, key):
        return self.data[key]

    def sum(self):
        """get a sum of all the data."""
        return sum(self.data.values())

    def defaults(self, defaults):
        """extend the set of values encoded in the representation.

        Data already saved in self will not be overwritten.
        
        :param defaults: dict or series
        """
        
        old = self.data.copy()
        self.data = defaults.copy() 
        for i in old.keys():
            self.data[i] = old[i]               
        return self

    def set(self, key, value):
        self.data[key] = float(value)
        return self
    
    def equal(self, rep, rel_tol=1e-6, abs_tol=0.0):
        """Determine if self is "equal" to another representation object."""
        
        if type(rep) != Representation:
            return False        
        if self.name != rep.name:
            return False
        if self.data.keys() != rep.data.keys():
            return False
        for key in self.data.keys():
            if not isclose(self.data[key], rep.data[key], 
                           rel_tol=rel_tol, abs_tol=abs_tol):
                return False
        return True

    def __str__(self):
        return "Representation\nname: " + str(self.name) + \
               "\ndata: " + str(self.data)

