# phenoscoring

`phenoscoring.py` is the primary program in the Phenoscoring repo. It manages a database of phenotype profiles and association scores. 

The program supports a number of arguments. The overall structure can be viewed using the `--help` flag.

```
python phenoscoring.py --help
```

The basic usage is as follows

```
python phenoscoring.py [COMMAND] --db [PATH TO DB] ...
```

The first positional argument describes the type of operation to perform, and the `--db` argument points the program on a specific phenoscoring database. The supported commands are:

 - build
 - update
 - explain
 - clearmodels
 - remove
 - recompute
 - export
 - representations

The first three commands provide the core functionality. Others provide auxiliary tools that can be helpful for advanced maintenance or debugging. 



## Core commands

### Build

The first step when using Phenoscoring is to build a database. 

```
python phenoscoring.py build 
                       --db phenoscoring-ORPHANET.sqlite \
                       --obo mp.obo \
                       --phenotype_frequencies phenoprep-MGI-priors.tsv.gz \
                       --reference_phenotype phenoprep-ORPHAET-phenotypes.tsv.gz \
                       --prior 0.0000001 \
                       --cores 8  
```

 - `--db` is a path to a database; in the build process, this is the primary output
 - `--obo` is a path to an ontology file defining acceptable phenotypes
 - `--phenotype_frequencies` is a path to a table assigning a background probability to phenotypes in the ontology. Subsequent algorithms assume that these probabilities follow the ontology hierarchy, i.e. priors for broad phenotypes are higher than priors for specific phenotypes. This file can be prepared using [phenoprep](phenoprep.md).
 - `--reference_phenotype` is a path to a table declaring reference (diseases) and their phenotypes. The phenotypes should match the ontology provided via `--obo`. A suitable file can be prepared using [phenoprep](phenoprep.md).
 - `--prior` is a numerical value used a starting score for all model-reference associations.
 - `--cores` is the number of threads to use during the calculation.
 
The command reads information about references and prepares an sqlite database. You can view the contents of this database using an sqlite client, for example [sqlitebrowser](https://github.com/sqlitebrowser/sqlitebrowser). 

Many of the steps in the build procedure are very quick. However, the build compares reference profiles to establish general and specific profiles for each disease. Depending on the size of the reference set and the ontology, this step may take time. 




### Update

The database build procedure sets up a database and objects pertaining to the references/diseases. It does not contain any models or any association scores. These can be added via an update command.

```
python phenoscoring.py update \
                       --db phenoscoring-ORPHANET.sqlite \
                       --obo mp.obo \
                       --model_descriptions phenoprep-IMPC-allele-universal-models.tsv.gz \
                       --model_phenotypes phenoprep-IMPC-allele-universal-phenotypes.tsv.gz \
                       --min_enrichment 100 \
                       --fp_penalty 1 \
                       --cores 8
```

 - `--db` is a path to an existing phenoscoring database
 - `--obo` is a path to an ontology file
 - `--model_description` is a file defining model ids and auxiliary fields. An appropriate file can be prepared using [phenoprep](phenoprep.md).
 - `--model_phenotypes` is a file mapping model ids to phenotypes. An appropriate file can be prepared using [phenoprep](phenoprep.md).
 - `--min_enrichment` numerical value, association scores for pairs that change with respect to the base score by this factor are recorded in the database for quick lookup.
 - `--fp_penalty` numerical value which determines how fuzzy phenotype matches are handled. See manuscript for details. 
 - `--cores` is the number of threads used in the calculation. 

The update command scans the provided models and phenotypes, and computes association scores to all the available references. Some associations are recorded for quick lookup within the database and others are discarded (they can be re-computed later).

The update command can be run multiple times on the same database. If the inputs specify new models, the calculation will augment the database with those new models and compute the relevant association scores. Thus, it is possible to populate the database in stages and start tracking new models at any time.

If the inputs refer to models that already exist in the database, the calculation will not create new model entries but rather update the existing entries. It will also adjust the phenotype sets for those models and recompute the relevant association scores. Thus, it is possible to add phenotype data in stages. 

*Note:* This last feature implies that the update command is not idempotent. If you execute the update once, a model will have a certain phenotype. If you execute it another time, the database will record that the same phenotype a second time. The downstream interpretation will be that the phenotype was observed and then independently confirmed, i.e. more confident. Association scores after the second update will be different than after the first update. 



### Explain

Once a database is populated with references and models, many association scores will have been computed and stored within one of its tables. These association can be extracted or queries directly from the database, or exported to text files (see `export` below). However, for in-depth analysis, it may be desirable to understand how each of the associations was computed. The `explain` tool provides functionality in this direction.

```
python phenoscoring.py explain \ 
                       --db phenosocinrg-ORPHANET.sqlite \
                       --obo mp.obo \
                       --explain general \
                       --pretty \
                       --reference ORPHA:179494 \
                       --model IMPC_MGI:5692557_hom_UA \
                       --fp_penalty 1
``` 

 - `--db` is a path to an existing phenoscoring database.
 - `--obo` is a path to an ontology file.
 - `--explain` is a string, either 'general' or 'specific', that determines which type of score is computed.
 - `--pretty` is a flag to pretty-print the output.
 - `--reference` is an identifier for a reference/disease. Multiple ids can be provided in a comma-separated format.
 - `--model` is an identifier for a model. Multiple ids can be provided in a comma-separated format.
 - `--fp_penalty` is a numerical value used during handling of false positives; see manuscript for details. 
 
The output is a JSON string containing the the final score for the association as well as an in-depth breakdown of how each of the model phenotypes contributed to the score. 




## Auxiliary commands

In addition to the core build-update-explain functionality, there `phenoscoring.py` program also provides several other commands. Some of these are under active development.


### Clearmodels

In cases when you would like to go back to a state equivalent to the state after build, you can clear all the model definitions, model phenotypes, and associations. 

```
python phenoscoring.py clearmodels --db phenoscoring-ORPHANET.sqlite 
```




### Export

The data managed by `phenoscoring.py` resides in an sqlite database and is thus easily accessible through command-line client or through plugins in R, python, etc. In some cases it can be handy to obtain the contents of particular tables as flat files. The export command generates such flat files.

```
python phenoscoring.py export \
                       --db phenoscoring-ORPHANET.sqlite \
                       --table model_description
```




### Recompute

The recompute command clears already computed value for all association scores that computes all of them again from scratch.

```
python phenoscoring.py recompute --db phenoscoring-ORPHANET.sqlite
```




### Remove

While the `clearmodels` command deletes all model information, it is also possible to remove individual models and their associated data. 

```
python phenoscoring.py remove \
                       --db phenoscoring-ORPHANET.sqlite \
                       --model_descriptions models.tsv.gz
```
 
This command scans a file with model descriptions and removes information on the specified models ids. 




### Representations

The representations command is a means to extract data on the references.

```
python phenoscoring.py representations \
                       --db $DBDIR/phenoscoring-$DBNAME.sqlite \
                       --obo mp.obo
```

This command does not require an `--output` argument, but produces output in a disk file based on the file path of the database. The output contains a table providing values for all phenotypes in the ontology and all references defined in the database. 

