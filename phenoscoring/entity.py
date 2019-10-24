"""
Container holding an entity with phenotypes for the Phenoscoring DB
"""

import json
from statistics import mean
from scoring.experiment import Experiment
from .phenotypedatum import PhenotypeDatum


class Entity():
    """Container for an entity with a description and a set of phenotypes"""
    
    def __init__(self, id, category, timestamp=None, **kwargs):
        """object holding a model description

        :param id: string identifier for a model
        :param category: string identifier for a group of models
        :param timestamp: string timestamp
        :param kwargs: additional named arguments
        """
        
        self.id = id
        self.category = category
        self.timestamp = timestamp
        # copy additional descriptors into a dict
        self.description = dict()
        for key, value in kwargs.items():
            self.description[key] = value
        self.data = []

    def set_description(self, key, value):
        """add a key/value pair to the model's description."""         

        self.description[key] = value

    def set_description_full(self, d):
        """transfer several key/value pairs from a dict into."""        

        for key, value in d.items():
            self.description[key] = value

    def add(self, datum):
        """add a phenotype datum to this model."""

        if type(datum) is not PhenotypeDatum:
            raise Exception("cannot add object of type "+str(type(datum)))
        self.data.append(datum)
        return self    
    
    def _split_phenotypes(self):
        """split items in self.data into arrays indexed by phenotype"""

        result = dict()
        for datum in self.data:
            phenotype = datum.phenotype
            if phenotype not in result:
                result[phenotype] = []
            result[phenotype].append(datum)
        return result

    def consensus(self):
        """redefine the phenotype data to collapse multiple entries using a consensus"""
        
        # partition the data by phenotype, then scan each phenotype
        parts = self._split_phenotypes()
        result = []
        for phenotype in parts.keys():            
            data = [_.experiment for _ in parts[phenotype]]            
            num0 = sum([_.value == 0 for _ in data])
            numP = sum([ 0 < _.value < 1 for _ in data])
            num1 = sum([_.value == 1 for _ in data])
            num_majority = max(num0, numP, num1)
            if num_majority == numP:
                data = [_ for _ in data if 0 < _.value < 1]
            elif num_majority == num0:
                data = [_ for _ in data if _.value == 0]
            else:
                data = [_ for _ in data if _.value == 1]
            majority = mean([_.value for _ in data])             
            tpr = mean([_.tpr for _ in data])
            fpr = mean([_.fpr for _ in data])
            tpr = max(fpr, tpr*float(num_majority)/(num0+numP+num1))
            datum = PhenotypeDatum(phenotype, Experiment(majority, tpr, fpr))
            result.append(datum)
        
        self.data = result
        return self

    def average(self):
        """redefine the phenotype data to collapse multiple entries using an average"""

        # partition the data by phenotype, then scan each phenotype
        parts = self._split_phenotypes()
        result = []
        for phenotype in parts.keys():
            data = [_.experiment for _ in parts[phenotype]]
            # this part requires work
            val = mean([_.value for _ in data])
            if val > 0:
                tpr = mean([_.tpr*_.value for _ in data])
            else:
                tpr = mean([_.tpr for _ in data])
            fpr = mean([_.fpr for _ in data])
            # create a single simplified phenotype
            datum = PhenotypeDatum(phenotype, Experiment(val, tpr, fpr))
            result.append(datum)
        self.data = result
        return self

    def trim_ancestors(self, obo, keep=set()):
        """redefine the phenotype data to remove entries with vague ontology terms

        :param obo: ontology structure object
        :parma keep: set with phenotypes that will not be trimmed
        
        :return: changes self object to remove some phenotypes
        """
        
        # scan all the data and identify ancestors
        ancestors = dict()        
        for datum in self.data:
            if datum.value==0:
                continue
            phenotype = datum.phenotype
            ancestors[phenotype] = obo.ancestors(phenotype)
            
        result = []
        datalen = len(self.data)
        for i in range(datalen):
            idatum = self.data[i]
            iphen = idatum.phenotype
            ival = idatum.value            
            if ival == 0:
                result.append(idatum)
                continue
            is_vague = False
            for j in range(datalen):
                jdatum = self.data[j]
                jphen = jdatum.phenotype
                jval = jdatum.value 
                if jval==0:
                    continue
                if iphen in ancestors[jphen] and ival <= jval:
                    is_vague = True            
            if iphen in keep or not is_vague:
                result.append(idatum)
        
        self.data = result
        return self

    def description_str(self):
        """get a string capturing all the description field."""

        return json.dumps(self.description)

    def has(self, key):
        """get a logical to check if a key has a value."""

        if key == "description":
            return True
        return key in self.__dict__ or key in self.description
    
    def get(self, key):
        """extract individual components describing the model."""        

        if key == "description":
            return self.description_str()
        elif key in self.__dict__:
            return self.__dict__[key]        
        else:
            return self.description[key]

    def equivalent(self, other):
        """determine if two Entity object contain the same data."""
        
        if self.id != other.id or self.category != other.category:
            return False
        if self.description != other.description:
            return False        
        if len(self.data) != len(other.data):
            return False        
        return sorted(self.data) == sorted(other.data)

    def __str__(self):
        """a string with all the data in the object, 
        not including the phenotype data attributed to the model."""
        
        result = (str(self.id), str(self.category), self.description_str())
        return "(" + ",".join(result) + ")"


def filter_entities_cat(objects, categories=None):
    """get a subset of objects that satisfy category properties

    :param objects: dict or iterable of Entity objects
    :param categories: None or a set of allowed values for object.category
        leave None to get all objects, or use a set
    :return: dict or list of objects that satisfy the category criteria.
    """

    if categories is None:
        return objects
    
    def filter_fun(x):
        return x.category in categories    
    return filter_entities(objects, filter_fun)


def filter_entities(objects, filter=None):
    """get a subset of objects that satisfy category properties

    :param objects: dict or iterable of Entity objects
    :param filter: filter function acting on an Entity object and
        return True/False
    :return: dict or list of objects that satisfy the filter function
    """
    
    if filter is None:
        return objects

    if type(objects) is dict:
        result = dict()
        for k,v in objects.items():
            if filter(v):
                result[k] = v
    else:
        result = [_ for _ in objects if filter(_)] 

    return result 

