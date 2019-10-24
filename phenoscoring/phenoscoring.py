"""
Definition of a phenoscoring analysis object.

This is a gateway to performing phenoscoring calculations.
"""

import os
import sys
from os.path import exists, basename, dirname
from db.db import setup_db
from db.generator import DBGenerator
from obo.obo import MinimalObo
from tools.files import check_file, values_in_column
from .dbhelpers import get_rootpath
from .dbtables import ModelDescriptionTable, ModelPhenotypeTable
from .dbtables import ModelScoreTable, PhenotypeFrequencyTable
from .dbtables import ReferenceNeighborsTable, ReferencePriorsTable
from .dbtables import ReferenceConcisePhenotypeTable
from .dbtables import ReferenceCompletePhenotypeTable
from .build import fill_concise_reference_table
from .build import fill_complete_reference_table
from .build import fill_phenotype_frequency_table
from .update import update_model_descriptions, add_model_phenotypes
from .time import now_timestamp
from .compute import prep_compute_packets
from .dbhelpers import get_refsets, get_model_names, get_ref_names
from .dbhelpers import delete_model_scores, delete_models
from .simplelogger import SimpleLogger
from .runner import run_packets


class Phenoscoring():
    """class that provides access to phenoscoring pipeline components.
    
    The constructor and functions starting with letters are meant to be
    called from outside scripts.
    
    Functions starting with an underscore are meant as internal components
    only.    
    """
    
    # tables created in the db
    tables = [ModelDescriptionTable,              
              ModelPhenotypeTable,                                 
              ModelScoreTable,
              PhenotypeFrequencyTable,
              ReferenceNeighborsTable,
              ReferencePriorsTable,
              ReferenceConcisePhenotypeTable,
              ReferenceCompletePhenotypeTable]                            

    def __init__(self, config):
        self.config = config
        if not hasattr(config, "scale_oo_scores"):
            self.config.scale_oo_scores = True
        if not hasattr(config, "stamp"):            
            self.config.stamp = now_timestamp()
        self.reset = config.reset
        self.dbpath = config.db
        self.rootpath = get_rootpath(self.dbpath)
        self.logger = SimpleLogger(not config.quiet)

    def _start(self):
        """Run this to initiate an analysis."""
        
        self.logger.msg1("Starting Phenoscoring - "+ self.config.action)
        return self.dbpath, self.config

    def _end(self):
        """Run this to finalize an analysis."""

        self.logger.msg1("Done")

    def setup(self):
        """create a db with tables (and leave all blank)"""
        
        dbpath, config = self._start()
        
        self.logger.msg1("Workding directory: "+dirname(dbpath))
        # test if already exists - build from scratch or not?
        if exists(dbpath):
            if not self.reset:            
                self.logger.msg1("Skipping database build; database exists")
                return None, None       
            self.logger.msg1("Removing existing database")
            os.remove(dbpath)

        # create a new database file
        self.logger.msg1("Creating new database: "+basename(dbpath))        
        setup_db(dbpath, tables=self.tables)
        
        return dbpath, config

    def build(self):
        """create a db for phenoscoring, includes setup and table-filling."""
                        
        # create db with empty tables
        dbpath, config = self.setup()
        
        # avoid work if setup decided db exists and build can be skipped
        if dbpath is None:
            return        
        
        # check prerequisite files        
        obopath = check_file(config.obo, dbpath, "obo")
        refpath = check_file(config.reference_phenotypes, dbpath, 
                             "reference_phenotypes")
        freqpath = check_file(config.phenotype_frequencies, dbpath,
                              "phenotype_frequencies")

        self.logger.msg1("Loading ontology")        
        obo = MinimalObo(obopath, True)
        
        self.logger.msg1("Preparing phenotype frequencies")
        fill_phenotype_frequency_table(dbpath, freqpath)
        
        # fill database with data
        self.logger.msg1("Preparing references")
        fill_concise_reference_table(dbpath, refpath)        
        fill_complete_reference_table(dbpath, obo, config)        
                
        self._end()
    
    def clearmodels(self):
        """remove all data from model tables."""
        
        dbpath, config = self._start()                        
        ModelDescriptionTable(dbpath).empty()
        ModelPhenotypeTable(dbpath).empty()
        ModelScoreTable(dbpath).empty()        
        self._end()

    def remove(self):
        """remove certain model descriptions and phenotypes from database."""
        
        dbpath, config = self._start()        
        desc_file = check_file(config.model_descriptions, dbpath,
                               "model_descriptions", allow_none=False)            
        self.logger.msg1("Reading model ids")
        ids = values_in_column(desc_file, "id")
        self.logger.msg1("Deleting models: "+str(len(ids)))
        delete_models(dbpath, ids)
        self._end()
        
    def _update(self, desc_file, phen_file):
        """update description and phenotype tables (without compute).""" 
        
        self.logger.msg1("Update summary")
        
        stamp = self.config.stamp
        summary = update_model_descriptions(self.dbpath, desc_file, stamp)
        for k, v in summary.items():
            kstr = k.replace("_", " ") + ": "
            self.logger.msg2("models with " + kstr + str(len(v)))
        
        summary = add_model_phenotypes(self.dbpath, phen_file, stamp)
        for k, v in summary.items():
            kstr = k.replace("_", " ") + ": "
            self.logger.msg2("models with " + kstr + str(len(v)))
        
        return summary

    def update(self):
        """add model descriptions and phenotypes to the database."""
                
        dbpath, config = self._start()
        
        self.config.obo = check_file(config.obo, dbpath, "obo")       
        desc_file = check_file(config.model_descriptions, dbpath,
                               "model_descriptions", allow_none=True)            
        phen_file = check_file(config.model_phenotypes, dbpath,
                               "model_phenotypes", allow_none=True)
                        
        summary = self._update(desc_file, phen_file)                
        if len(summary["incorrect_ids"]) == 0 and not config.skip_compute:
            self._compute(models=summary["new_phenotypes"])
                     
        self._end()

    def _compute(self, references=None, models=None):
        """calculate model scores for the specified models"""
                                               
        config = self.config
        if references is None:
            self.logger.msg2("Working with all references")
            references = get_ref_names(self.dbpath)
        
        self.logger.msg1("Dropping scores for "+str(len(models))+ " models")
        delete_model_scores(self.dbpath, models)
        self.logger.msg2("Working with " + str(len(references)) +
                         " references, " + str(len(models)) + " models")
        packets = prep_compute_packets(config, 
                                       references=references,
                                       models=models,
                                       log=self.logger.msg2)                    
        
        # run calculations on all the packets
        msg = str(config.cores)+ " cores, " + str(len(packets))+ " packets"
        self.logger.msg1("Scoring ("+msg+")")
        run_packets(packets, config.cores)

    def recompute(self):
        """removes everything in the scores table and computes all from scratch."""
                        
        dbpath, config = self._start()
        
        self.logger.msg1("Deleting existing scores")
        scorestab = ModelScoreTable(self.dbpath)
        scorestab.empty()
        
        self.logger.msg1("Fetching model ids")
        modelids = get_model_names(self.dbpath)
        references = get_ref_names(self.dbpath)        
        
        self.logger.msg1("Computing model scores")
        self._compute(references, modelids)
        
        self._end()

    def explain(self):
        """Perform a verbose calculation of inference scores.
        
        The prep for this function is similar as for compute().
        Once the relevant data is loaded from the db, the calculations
        are performed and recorded manually.
        """
                
        self.logger.verbose = False        
        dbpath, config = self._start()        
                
        if config.explain not in ["specific", "general"]:
            return "--explain must be 'general' or 'specific'"
        config.obo = check_file(config.obo, dbpath, "obo")
        
        # allow user to pass several model/reference pairs
        models = config.model.split(",")
        references = config.reference.split(",")        
        M = len(models)
        
        if len(references) != M:
            raise Exception("incompatible number of models and references")
                
        # use the packet to load information from the db, refset and models
        packet = prep_compute_packets(self.config, 
                                      references=references, 
                                      models=models,
                                      partition_size=M)[0]
        packet.prep()
        refset = packet.general_refset        
        if config.explain == "specific":
            refset = packet.specific_refset
        refset.learn_obo(MinimalObo(config.obo))

        allresults = [None]*M
        for i, (modelid, refid) in enumerate(zip(models, references)):
            data = packet.models[modelid]
            result = refset.inference_chain(data, refid, verbose=True,
                                            fp_penalty=config.fp_penalty)
            allresults[i] = result.to_json(nodata=config.explain_nodata)            
        
        return "["+(",".join(allresults))+"]"; 

    def export(self, out=sys.stdout):
        """connect to a database and export one of the tables line-by-line"""

        tablemodel = None
        for x in self.tables:
            if x.name == self.config.table:
                tablemodel = x
        
        if tablemodel is None:
            return
                
        # output the header
        tableinstance = tablemodel(self.dbpath)
        fieldnames = list(tableinstance.fieldnames())    
        out.write("\t".join(fieldnames) + "\n")        
        # output the table contents
        generator = DBGenerator(tablemodel(self.dbpath))
        for row in generator.next():
            temp = [str(row[_]) for _ in fieldnames]
            out.write("\t".join(temp) + "\n")    
    
    def export_representations(self):
        """write matrix representations for models and refs to disk."""
        
        dbpath, config = self._start()      
        
        self.logger.msg1("Loading ontology")
        obopath = check_file(config.obo, dbpath, "obo")        
        self.obo = MinimalObo(obopath, True)
        
        self.logger.msg1("Saving reference representations")
        general_refset, _ = get_refsets(self.dbpath)
        general_refset.save(self.rootpath+"-references", "phenotype")        
                
        self._end()

