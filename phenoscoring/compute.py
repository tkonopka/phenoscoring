"""
Class for computing phenosocing scores with the Phenoscoring system.
"""

from math import ceil, floor
from obo.obo import MinimalObo
from scoring.representation import Representation
from .dbhelpers import get_refsets, get_model_representations
from .dbhelpers import get_ref_priors, get_phenotype_priors 
from .dbtables import ModelScoreTable


class PhenocomputePacket:
    """A runnable object for phenoscoring calculation
    
    On init, this requires minimal information about what scores to compute.
    The object fetches the relevant data from the db when run()    
    """
        
    def __init__(self, config, references=None, models=None,
                 log=None, run_msg="Packet "):
        """A runnable class for processing a set of references and models

        :param config: object of class PhenoscoringConfig
        :param references: iterable with reference names
        :param models: iterable with model names
        :param stamp: timestamp for calculations
        :param log: a logging function
        :param run_msg: a template for a status message
        """

        self.config = config        
        self.stamp = config.stamp        
        self.log = log
        self.run_msg = run_msg
        self.phen_priors = None
        self.ref_priors = None
        self.general_refset = None
        self.specific_refset = None
        self.models = dict()
        self.references = set()

        # setup calculation with references and stub models
        self.references = set(references)
        for id in models:
            self.models[id] = Representation(name=id)

    def prep(self):
        """loads initial data from the db."""
        
        config = self.config
        dbpath = config.db
        # load the ontology
        obo = MinimalObo(config.obo)
        # prepare information about references
        self.phen_priors = get_phenotype_priors(dbpath)
        self.ref_priors = get_ref_priors(dbpath, self.references)        
        general, specific = get_refsets(dbpath, ref_priors=self.ref_priors)
        # assign an ontology for reasoning        
        specific.learn_obo(obo)
        general.learn_obo(obo)
        self.general_refset = general
        self.specific_refset = specific
        # transfer model phenotypes
        model_names = list(self.models.keys())
        self.models = get_model_representations(dbpath, obo,
                                                log=self.log,
                                                log_prefix=self.run_msg,
                                                model_names=model_names)

    def _clear(self):
        """clears some objects to release memeory"""
        
        self.phen_priors = None
        self.ref_priors = None
        self.general_refset = None
        self.specific_refset = None
        self.models = dict()
        self.references = set()

    def _run_inference(self):
        """run calculation of general and specific scores. 
        
        This is a helper to run(). Don't use separately.
        """
                
        g_refset = self.general_refset
        s_refset = self.specific_refset
        penalty = self.config.fp_penalty
        
        general, specific = dict(), dict()
        for id in self.models:
            model = self.models[id]
            general[id] = g_refset.inference(model, fp_penalty=penalty)
            specific[id] = s_refset.inference(model, fp_penalty=penalty)

        return general, specific  

    def run(self):
        """Perform calculations on declared groups of models and references."""
                            
        if self.log is not None:
            self.log(self.run_msg + " - starting") 
                
        # compute scores
        self.prep() 
        general_scores, specific_scores = self._run_inference()         
        stamp = self.stamp

        # thresholds determining if scores are stored in db
        min_inf = self.config.min_inference
        min_ratio = self.config.min_enrichment
        bg = self.ref_priors

        # transfer scores to db
        scorestab = ModelScoreTable(self.config.db)
        refnames = list(self.general_refset.names())        
        for modelid in self.models:
            general = general_scores[modelid]
            specific = specific_scores[modelid]
            for ref in refnames:
                g, s = general[ref], specific[ref]
                pass_abs = (g > min_inf)
                pass_ratio = (g / bg[ref] > min_ratio)
                if not pass_abs and not pass_ratio:
                    continue
                scorestab.add(model=modelid, reference=ref, timestamp=stamp,
                              general=g, specific=s)
        scorestab.save()
        self._clear()

        if self.log is not None:
            self.log(self.run_msg + " - done")        


def prep_compute_packets(config, references=None, models=None, 
                         partition_size=None, log=None):
    """prepare ComputePacket packets for calculating scores.

    :param config: PhenoscoringConfig object with settings
    :param references: names of references to score
    :param models: names of models to score
    :param partition_size: integer, can override partition_size in config
    :param log: function to use for logging
    :return: array with PhenocomputePackets, which together cover
        all combinations of references and models
    """
    
    if references is None or models is None:
        return []
    if len(references) == 0 or len(models) == 0:
        return []
    
    # identify a partition size 
    if partition_size is None:
        partition_size = config.partition_size
    max_size = partition_size
       
    # estimate number of packets
    n_refs, n_models = len(references), len(models)    
    # split up into groups of partition_size each
    n_ref_groups = ceil(n_refs/max_size)
    n_model_groups = ceil(n_models/max_size)
    n_packets = n_ref_groups * n_model_groups
        
    # create sets for holding model/reference combinations in each packet
    ref_groups = [None] * n_packets
    model_groups = [None] * n_packets
    for z in range(n_packets):
        ref_groups[z], model_groups[z] = set(), set()        
    for i, ref_id in enumerate(references):
        zi = floor(i/max_size) * n_model_groups
        for zj in range(n_model_groups):
            ref_groups[zi+zj].add(ref_id)
    for j, model_id in enumerate(models):
        zj = floor(j / max_size)
        for zi in range(n_ref_groups):
            model_groups[(zi*n_model_groups)+zj].add(model_id)
    
    packets = [None]*n_packets
    for z in range(n_packets):        
        packets[z] = PhenocomputePacket(config,
                                        references=ref_groups[z],
                                        models=model_groups[z],
                                        log=log,
                                        run_msg="Packet "+str(z))
    return packets

