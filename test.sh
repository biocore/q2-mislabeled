#!/bin/bash
source activate qiime2-2022.11

qiime mislabeled within-dataset \
   --i-table mvp_problematic.biom.qza \
   --m-env-file mvp_problematic.tsv \
   --o-mislabelings within_test_run.qza \
   --m-env-column env_package \
   --p-n-jobs 2 \
   --verbose

qiime mislabeled against-dataset \
   --i-focus tmi_problematic.biom.qza \
   --i-reference mvp_reference.biom.qza \
   --m-focus-env-file tmi_problematic.tsv \
   --m-focus-env-column env_package \
   --m-reference-env-file mvp_reference.tsv \
   --m-reference-env-column env_package \
   --o-mislabelings against_test_run.qza \
   --p-alleged-min-probability 0.5 \
   --p-n-jobs 2 \
   --verbose

python assess-test-run.py
