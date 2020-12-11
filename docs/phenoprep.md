# phenoprep

`phenoprep` implements a collection of convenience scripts to prepare data files that can be accepted by `phenoscoring.py`. Running `phenoprep.py` is not strictly required to use `phenoscoring` if the required data files for `phenoscoring.py` are prepared manually. Nonetheless, `phenoprep.py` is a convenient way to understand the file formats required for subsequent steps.

The overall structure of the `phenoprep` program can be viewed using the `--help` flag.

```
python phenoprep.py --help
```

The basic usage is to specify a command type alongside other options and inputs.

```
python phenoprep.py [COMMAND] --output [OUTPUT PREFIX] ... 
```

 - `[COMMAND]` is a single string indicating what kind of script to execute
 - `--output` is string used as a prefix for output files. Some tools generate more than one output that are associated with each other via this prefix.   



## Preparing reference data

### Ontology-ontology mapping

Human disease phenotypes are often available in human-specific encoding, for example using the [Human Phenotype Ontology](https://hpo.jax.org/app/). Data for mouse models are instead available encoded using [Mammalian Phenotype Ontology](http://www.informatics.jax.org/vocab/mp_ontology/). `phenoscoring` works within a single ontology, or can alternatively use a cross-ontology mapping to translate references into a new ontology. 

A third-party tool, [owlsim](https://github.com/owlcollab/owltools), can compute pairwise similarity scores for terms in two ontologies. Usage of that tools is beyond the scope of explanation here, but its output is a long table listing pairs of terms and numerical scorse. That output can be simplified using a `phenoprep` script. 

```
python phenoprep.py oomap 
                    --input hp-mp-owlsim-output.tab \
                    --obo mp.obo \
                    --output hp-mp
```

 - `--input` is a path to the output table from `owlsim`. In the above, the filename hints that the table should provide scores comparing HP and MP terms.
 - `--obo` is a path to a target ontology
 - `--output` is a prefix for output files. The final file will contain a suffix `oomap.tsv.gz`. Its content will be a three-column table with columns `term1`, `term2`, and `score`.

*Note* A oomap file is provided in the Supplementary Data of the manuscript.




### References

Preparing references refers to converting disease HPO annotations into a format for `phenoscoring`. 

The core input is data from the `phenotype_annotation.tab` file from the [HPO servers](http://compbio.charite.de/jenkins/job/hpo.annotations/lastStableBuild/artifact/misc/). However, the raw download must be adjusted with a header line.

```
Source  Disease_number  Disease_title   V4      Phenotype       Reference       V7      V8      Frequency       V10     V11     V12     Date    V14     V15
```

The downloaded data contains annotations for diseases defined by [OMIM](www.omim.org), [ORPHANET](www.orpha.net), and other curation database. The disease definitions are partly overlapping and it is recommended to split this data. The following assumes data pertaining to ORPHANET diseases are channeled into a separate file.

```
python3 phenoprep.py phenotypetab 
                     --input phenotype_annotation_ORPHANET.tab.gz \
                     --tpr 0.8 --fpr 0.05 \ 
                     --obo mp.obo \
                     --oomap hp-mp-oomap.tsv.gz \
                     --output phenoprep-ORPHANET
```

 - `--input` is a path to disease phenotypes, including a header line.
 - `--tpr` and `--fpr` are numerical values encoding true positive rate and false positive rate; see comments just below.
 - `--oomap` is a path to a cross-ontology mapping table. The mapping can be prepared using the `phenoprep oomap` tool (see above).

This script fulfils two roles. The first is to create a table mapping disease ids to phenotypes. The second role is to create technical controls. These are models (see below) that are based on the raw annotations, but pretend that each phenotype was measured experimentally. Arguments `--tpr`, `--fpr`, and `--obo` are required for this role to tune these technical controls.




## Preparing model data

Several of the `phenoprep` scripts serve to create model definitions, which consist of two types of files.

 - Model description files declare model ids and provide auxiliary information about the models, e.g. genotype, background, or any other relevant information. These files have suffixes `model.tsv.gz`.
 - Model phenotype files associate models with their phenotype measurements. These files have suffixes `_pheotypes.tsv.gz`.
 

### MGI

Preparing MGI data refers to processing mouse phenotype data to estimate priors for mouse phenotypes and to create sets of files containing model descriptions and phenotypes. 

The core input for this script is a file `MGI_GenePheno.rpt` that can be downloaded from [MGI](http://www.informatics.jax.org/). However, the raw data from MGI must be augmented with a header

```
Allelic_Composition     Allele_Symbol   Allele_ID       Genetic_Background      Mammalian_Phenotype_ID  PubMed_ID       MGI_Marker_Accession_ID MGI_Genotype_Accession_ID
```

After downloading the raw data file and adding a header, the data is ready to be processed.

```
python phenoprep.py MGI 
                    --input MGI_GenePheno_wheader.rpt \
                    --tpr 0.8 --fpr 0.05 \
                    --obo mp.obo \
                    --priors marker \
                    --output phenoprep-MGI
```

 - `--input` is a path to prepared file following formating from MGI, but including a header.
 - `--tpr` and `--fpr` are numeric values. They are the assumed experimental true-positive and false-positive rates for each of the phenotypes. 
 - `--obo` is a path to the ontology in obo format. This ontology is used to eliminate duplicate phenotypes and to verify all phenotypes are valid. 
 - `--priors` is a string that indicates how to estimate phenotype priors. Setting the label to `markers` indicates phenotypes are assembled by gene (as opposed to by allele or by genotype).
 
Outputs from this tool include model description and model phenotype files for the MGI data. One of the outputs is a two-column table estimating the prevalence of all phenotypes in the MGI cohort. 



### IMPC

Preparing IMPC data refers to converting downloads from the IMPC data portal into sets of files containing model descriptions and phenotypes.

```
python phenoprep.py IMPC 
                    --input IMPC_statistical_results.csv.gz \
                    --tpr 0.8 --fpr 0.05 \ 
                    --obo mp.obo \
                    --simplify average \
                    --output phenoprep-IMPC
```

 - `--input` is a path to IMPC mouse data. This can be downloaded from the `statistical_results` SOLR core provided by the [IMPC data services](www.mousephenotype.org). 
 - `--tpr` and `--fpr` are numeric values. They are the assumed experimental true-positive and false-positive rates for each of the phenotypes.
 - `--simplify` is a label that indicates a method to simplify duplicate phenotypes in the statistical results data. It is recommended to use `average` to avoid recording duplicated phenotypes multiple times. 
 



### GXD Expression

Preparing expression data refers to using tissue level gene expression data as phenotypes.

```
python phenoprep.py GXD \
                    --tpr 0.8 --fpr 0.5 
                    --obo mp.obo \
                    --emapa MP_EMAPA_wheader.rpt.gz \
                    --gxd phenoprep-GXD.tsv.gz \
                    --output phenoprep-GXD
```

 - `--tpr` and `--fpr` are numeric values. They are the assumed experimental true-positive and false-positive rates for each of the phenotypes.
 - `--obo` is a path to the ontology in obo format. 
 - `--emapa` is a path to a file specifying conversion  between tissues (EMAPA codes) and mammalian phenotypes (MP codes). This file is available through the MGI. However, a header must be supplied. 
 - `--gxd` is a path to a file summarizing gene expression in various tissues. A compatible file can be obtained using the [download_gxd.py](download_gxd.md) utility.
  
The above script produces model definition files based on expression data alone. It is possible to execute the script with additional inputs specifiying models and phenotypes, for example describing IMPC or MGI models.

```
python phenoprep.py GXD 
                    --input phenoprep-IMPC-allele-universal-models.tsv.gz \
                    --phenotypes phenoprep-IMPC-allele-universal-phenotypes.tsv.gz \
                    --tpr 0.8 --fpr 0.5 \
                    --obo mp.obo \
                    --emapa MP_EMAPA_wheader.rpt.gz \
                    --gxd phenoprep-GXD.tsv.gz \
                    --output phenoprep-IMPC-allele-universal-expression
```

 - `--input` is a path to a model description file. The example uses a file with IMPC models prepared by `phenoprep IMPC`.
 - `--phenotypes` is a path to a model phenotypes file that matches the model description file provided in `--input`.
 - other inputs are similar to above
 
This script again produces new model definitions and phenotype files. The phenotypes for these new models contain previously declared phenotypes (if provided) and additional phenotypes derived from the GXD. 

Note that the `--tpr` and `---fpr` arguments affect annotations for the expression-derived phenotypes only. Because the link between expression and phenotype is speculative, it is recommended to use cautious values for these `--tpr` and `--fpr` values. In the example above, caution is implemented through a rather high value for `--fpr`.

