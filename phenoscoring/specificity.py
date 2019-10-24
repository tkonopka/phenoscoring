"""
Helpers used when computing specificity of references.
"""

from .dbtables import ReferenceCompletePhenotypeTable
from .dbtables import ReferenceNeighborsTable
from .dbhelpers import get_phenotype_priors


class SpecificityPacket:
    
    def __init__(self, dbpath, refset, k):
        """packet for calculating specificity scores

        :param dbpath: path to phenoscoring db
        :param refset: ReferenceSet object
        :param k: integer, number neighbors to consider
        """
                
        self.dbpath = dbpath
        self.refset = refset
        self.k = k            
        self.ref_names = set()

    def add(self, ref_name):
        self.ref_names.add(ref_name)

    def run(self):
        """compute neighbors and fill in complete phenotype tables in the db
                
        The command will only process calculations starting from 
        references declared using add().            
        """        
                
        if len(self.ref_names) == 0:
            return
                
        phen_priors = get_phenotype_priors(self.dbpath)
        refset = self.refset
        # get a representation for the null model
        nulldata = refset.get_data("null")        

        # do rounding for priors and null outside of loop
        for i in nulldata.keys():
            phen_priors[i] = round(phen_priors[i], 7)            
            nulldata[i] = round(nulldata[i], 7)
        
        # handles for db tables
        model_phenotypes = ReferenceCompletePhenotypeTable(self.dbpath)
        model_neighbors = ReferenceNeighborsTable(self.dbpath)
        
        # by definition, add all phenotypes for the null reference
        if "null" in self.ref_names:
            for phenotype in nulldata.keys():
                null_val = nulldata[phenotype]
                prior_val = phen_priors[phenotype]                
                model_phenotypes.add("null", phenotype, null_val, prior_val)            
        
        # process declared references
        for refname in self.ref_names:
            # skip the null rep (handled outside) 
            if refname == "null":
                continue                            
            refdata = refset.get_data(refname)
            neighbors = refset.nearest_neighbors(refname, self.k)
            # save neighbors
            for rank in range(len(neighbors)):
                model_neighbors.add(refname, neighbors[rank], rank+1)                
            # record specific phenotype representation            
            neidata = refset.get_average(neighbors)
            for phenotype in refdata.keys():            
                null_val = nulldata[phenotype]
                prior_val = phen_priors[phenotype]
                self_val = round(refdata[phenotype], 7)
                nei_val  = round(neidata[phenotype], 7)
                if self_val < prior_val:
                    specific_val = prior_val + min(0, self_val - nei_val)
                    specific_val = max(self_val, specific_val)
                else:
                    specific_val = max(prior_val, self_val-nei_val)
                if self_val == null_val and specific_val == prior_val:
                    continue
                model_phenotypes.add(refname, phenotype, self_val, specific_val)
        
        model_phenotypes.save()
        model_neighbors.save()

