# Phenoscoring

`Phenoscoring` is a suite of programs for incremental data integration, adapted for use with phenotype data and for tracking model-disease associations. 

Incremental data integration is a concept for how to summarize datasets that can change over time. Suppose, for example, that information at an initial moment in time can be collapsed into an association score. When new evidence becomes available that is consistent with the previous data, it is natural to presume that a recomputed association score should reflect that. However, this is not necessarily the case when the score is computed with commonly used integration approaches such as averaging, consensus, or normalization - those approaches only work well at a single moment in time. Incremental data integration is a pivot toward tracking associations in a way that is consistent at all time points, or all stages of a dataset lifecycle. 

The focus on consistency at multiple stages in a dataset lifecycle has some strong consequences on how association scores can be defined. In shoft, the focus shifts shifts toward cumulative summaries as opposed to normalized quantities. `Phenoscoring` is an exploration of these consequences in a specific context where the data consists of phenotypes associated with mouse models and the goal is to track the similarity of these models to human disease.



## Installation

Programs in the `phenoscoring` suite requires python 3.6 to run. You can check your version of python using one of the following commands,

```
python --version
python3 --version
``` 

Some third party packages are also required. These can be installed using the `pip` package manager

```
pip install jsonpickle numpy numba
```

After ensuring you have the right version of python and the required packages, you can obtain the software by cloning it from the source repo. 

```
git clone https://www.github.com/tkonopka/Phenoscoring
```

No further installation procedures are required. However, running the software successfully does require the assembly of a number of required data files, explained in the documentation below.




## Usage

The repo root contains a number of executables. A typical workflow relies on just two of these programs.

 - [phenoprep.py](docs/phenoprep.md) prepares data files for use with phenoscoring.py
 - [phenoscoring.py](docs/phenoscoring.md) builds and manages a phenoscoring database

The repo also contains other executables. These are auxiliary scripts that can be relevant for debugging, post-processing, or supplementary calculations. 

 - [obotools.py](docs/obotools.md) is set of miscellanous tools for handling ontology `obo` files
 - [download_GXD.py](docs/download_gxd.md) fetches expression data in mouse tissues
 - [phenojoin.py](docs/phenojoin.md) prepares data files with modesl supported by IMPC and MGI



## Applications

Algorithms and applications are described in a manuscript

> *Incremental data integration for tracking genotype-disease associations.* Submitted (Journal link, biorxiv link).


