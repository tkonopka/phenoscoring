# obotools

`obotools` implements a collection of utilities for processing ontology files in obo format. These utilities are not sophisticated and the functionality is likely available through other tool and libraries. They are provided here for convenience of fetching ontology data through the command line.

The basic usage is to run the program specifying the utility name and one input ontology file. 

```
python obotools.py [UTILITY] --obo [OBO FILE]
```

The outputs are written to standard output, but it is straightforward to save into files by redirecting the output.

```
python obotools.py [UTILITY] --obo [OBO FILE] > [OUTPUT FILE]
```

In the primary use case, the ontology file is the mammalian phenotype ontology, `mp.obo`, which can be obtained from the [OBO foundry](http://www.obofoundry.org/ontology/mp).



## alts

The `alts` utility extracts mappings from active ontology ids to alternative ids. 

```
python obotools.py alts --obo mp.obo
```

The output contains only those ids that have alternatives. 



## ancestors

The `ancestors` utility recursively extracts ancestors - parents, the parents of parents, and so on - for all ontology terms.

```
python obotools.py ancestors --obo mp.obo
```

Most ontology ids have many ancestors: these are listed separated by a semicolon. The ordering of terms in the semicolon-separated list is not guaranteed to be meaningful.



## names

The `names` utility extracts a mapping between ontology id codes and short names.

```
python3 obotools.py names --obo mp.obo
```

The output contains only active terms in the ontology. 



## parents

The `parents` utility extracts the immediate parents for all ontology terms. 

```
python obotools.py parents --obo mp.obo
```

Most ontology ids have a single parent but some have more. Multiple parents are listed separated by semicolons. 


# obsolete

The `obsolete` utility extracts the identifiers that are no longer used/supported by the ontology. 

```
python obotools.py obsolete --obo mp.obo
```



# minimize

The `minimize` utility, unlike the other utilities above, does not produce an output table. Rather, it produces rows of text that are compatible with the obo format. The output is focused on just the connectivitiy between the ontology terms and is stripped from much descriptive information.

```
python obotools.py minimize --obo mp.obo > mp-min.obo
```

NB. This operation is not a 'minimization' in the form of compression. It produces a small output by removing certain information - use at your own risk.



