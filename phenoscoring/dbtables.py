"""
Table definitions for the phenoscoring DB

All classes subclass DBTable and define one table in a sqlite3 database.
"""

from db.table import DBTable


class ModelDescriptionTable(DBTable):
    """Table model for model phenotype experiment data."""
    
    name = "model_description"
    text_fields = ("id", "category", "description", "timestamp")
    
    def add(self, id=None, category=None, description=None, timestamp=None):
        self.data.append((id, category, description, timestamp))


class ModelPhenotypeTable(DBTable):
    """Table model for model phenotype experiment data."""
    
    name = "model_phenotype"
    text_fields = ("id", "phenotype", "timestamp")
    real_fields = ("value", "TPR", "FPR")
    
    def add(self, id=None, phenotype=None, timestamp=None,  
            value=None, TPR=0.8, FPR=0.05):            
        self.data.append((id, phenotype, timestamp, value, TPR, FPR))


class ModelScoreTable(DBTable):
    """Table model for model phenotype experiment data (with timestamp)"""
    
    name = "model_score"
    text_fields = ("model", "reference", "timestamp")
    real_fields = ("general", "specific")
    
    def add(self, model=None, reference=None, timestamp=None, 
            general=None, specific=None):
        self.data.append((model, reference, timestamp, 
                          general, specific))


class ReferenceNeighborsTable(DBTable):
    """Table indicating which references and similar."""
    
    name = "reference_neighbors"
    text_fields = ("id", "neighbor")
    real_fields = ("rank",)
    
    def add(self, id=None, neighbor=None, rank=None):
        self.data.append((id, neighbor, rank))


class ReferencePriorsTable(DBTable):
    """Table model for reference priors."""
    
    name = "reference_priors"
    text_fields = ("id",)
    real_fields = ("value",)
    
    def add(self, id=None, value=None):
        self.data.append((id, value))


class ReferenceConcisePhenotypeTable(DBTable):
    """Table model for reference phenotypes (raw)."""
    
    name = "reference_concise_phenotype"
    text_fields = ("id", "phenotype")
    real_fields = ("value",)
    
    def add(self, id=None, phenotype=None, value=None):
        self.data.append((id, phenotype, value))
        

class ReferenceCompletePhenotypeTable(DBTable):
    """Table model for reference phenotypes (all and specific)."""
    
    name = "reference_complete_phenotype"
    text_fields = ("id", "phenotype")
    real_fields = ("value", "specific_value")
    
    def add(self, id=None, phenotype=None, value=None, specific_value=None):
        self.data.append((id, phenotype, value, specific_value))


class PhenotypeFrequencyTable(DBTable):
    """Table model for capturing inferred phenotype abundance."""
    
    name = "phenotype_frequency"
    text_fields = ("phenotype",)
    real_fields = ("frequency",)
    
    def add (self, phenotype, frequency):
        self.data.append((phenotype, frequency))

