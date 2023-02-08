Background
----------

A plugin which implements the [HMP SOP](https://www.hmpdacc.org/hmp/doc/QiimeCommunityProfiling.pdf) to assess sample mislabeling and contamination. To do so, `q2-mislabeled` relies on [`q2-sample-classifier`](https://docs.qiime2.org/2022.11/tutorials/sample-classifier/#nested-cross-validation-provides-predictions-for-all-samples)'s nested cross-validation, and separately, uses [SourceTracker2](https://github.com/biota/sourcetracker2) to determine sample contamination.

Installation
------------

`q2-mislabeled` has been tested within a `2022.11` QIIME 2 environment. To install:

```bash
$ pip install q2-mislabeled
```
