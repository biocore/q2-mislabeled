import pandas as pd
import qiime2

input_md = pd.read_csv('tmi_16s_problematic.tsv', sep='\t').set_index('#SampleID')
result_md = qiime2.Artifact.load('test_run.qza').view(pd.DataFrame)

for r in input_md.itertuples():
    if r.intentionally_mislabled:
        original = r.original_env_package
        assert result_md.loc[r.Index, 'Mislabeled']
        corrected = result_md.loc[r.Index, 'corrected_label']
        assert original == corrected
    if r.intentional_contamination:
        assert result_md.loc[r.Index, 'Contaminated']
