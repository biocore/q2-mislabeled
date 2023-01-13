import pandas as pd
import qiime2

input_md = pd.read_csv('mvp_problematic.tsv', sep='\t').set_index('#SampleID')
result_md = qiime2.Artifact.load('test_run.qza').view(pd.DataFrame)

for r in input_md.itertuples():
    if r.intentional_mislabel:
        incorrect = r.env_package
        original = r.original_env_package
        corrected = result_md.loc[r.Index, 'corrected_label']
        if original != corrected:
            print("MISLABELED")
            print(r.Index)
            print("Incorrect:", incorrect)
            print("Original:", original)
            print("Corrected:", corrected)
            print(result_md.loc[r.Index, 'Mislabeled'])
            print("---")
        assert result_md.loc[r.Index, 'Mislabeled']
        assert original == corrected
    if r.intentional_contamination:
        if not result_md.loc[r.Index, 'Contaminated']:
            print("CONTAMINATED")
            print(result_md.loc[r.Index, 'min_proportion'])
            print("---")
        assert result_md.loc[r.Index, 'Contaminated']
