#!/bin/bash
source activate qiime2-2022.11

qiime mislabeled within-dataset \
   --i-table mvp_problematic.biom.qza \
   --m-env-file mvp_problematic.tsv \
   --o-mislabelings test_run.qza \
   --m-env-column env_package \
   --verbose

python assess-test-run.py
