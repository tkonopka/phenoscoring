# download_GXD

`download_GXD` is a utility to fetch mouse expression data from Mouse Gene Expression Database through [mousemine](http://www.mousemine.org/).

The basic usage is to provide a set of files containing marker ids and an output file.

```
python download_GXD.py \
   --input phenoprep-MGI-genotype-universal-models.tsv.gz,phenoprep-IMPC-allele-universal-models.tsv.gz \
   --output phenoprep-GXD.tsv.gz
```

The utility reads the input files, assumed to contain tab-separated tables, and extract gene ids from column `marker_id`. The utility then runs several queries to mousemine to download expression data for those genes. 







