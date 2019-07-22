"""table definitions for the phenoscoring DB

All classes subclass DBTable and define one table in a sqlite3 database.

@author: Tomasz Konopka
"""

from db.table import DBTable


class ModelDescriptionTable(DBTable):
    """Table model for model phenotype experiment data."""
    
    tabname = "model_description"
    textfields = ("id", "category", "description", "timestamp")
    
    def add(self, id=None, category=None, description=None, timestamp=None):
        self.data.append((id, category, description, timestamp))


class ModelPhenotypeTable(DBTable):
    """Table model for model phenotype experiment data."""
    
    tabname = "model_phenotype"
    textfields = ("id", "phenotype", "timestamp")
    realfields = ("value", "TPR", "FPR")    
    
    def add(self, id=None, phenotype=None, timestamp=None,  
            value=None, TPR=0.8, FPR=0.05):            
        self.data.append((id, phenotype, timestamp, value, TPR, FPR))


class ModelScoreTable(DBTable):
    """Table model for model phenotype experiment data (with timestamp)"""
    
    tabname = "model_score"
    textfields = ("model", "reference", "timestamp")
    realfields = ("general", "specific")
    
    def add(self, model=None, reference=None, timestamp=None, 
            general=None, specific=None):
        self.data.append((model, reference, timestamp, 
                          general, specific))


class ReferenceNeighborsTable(DBTable):
    """Table indicating which references and similar."""
    
    tabname = "reference_neighbors"
    textfields = ("id", "neighbor")
    realfields = ("rank",)
    
    def add(self, id=None, neighbor=None, rank=None):
        self.data.append((id, neighbor, rank))


class ReferencePriorsTable(DBTable):
    """Table model for reference priors."""
    
    tabname = "reference_priors"
    textfields = ("id",)
    realfields = ("value",)
    
    def add(self, id=None, value=None):
        self.data.append((id, value))


class ReferenceConcisePhenotypeTable(DBTable):
    """Table model for reference phenotypes (raw)."""
    
    tabname = "reference_concise_phenotype"
    textfields = ("id", "phenotype")
    realfields = ("value",)
    
    def add(self, id=None, phenotype=None, value=None):
        self.data.append((id, phenotype, value))
        

class ReferenceCompletePhenotypeTable(DBTable):
    """Table model for reference phenotypes (all and specific)."""
    
    tabname = "reference_complete_phenotype"
    textfields = ("id", "phenotype")
    realfields = ("value", "specific_value")
    
    def add(self, id=None, phenotype=None, value=None, specific_value=None):
        self.data.append((id, phenotype, value, specific_value))


class PhenotypeFrequencyTable(DBTable):
    """Table model for capturing inferred phenotype abundance."""
    
    tabname = "phenotype_frequency"
    textfields = ("phenotype",)
    realfields = ("frequency",)
    
    def add (self, phenotype, frequency):
        self.data.append((phenotype, frequency))

