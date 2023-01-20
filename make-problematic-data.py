import biom
import pandas as pd
import sys
import qiime2
import random
import numpy as np

tab = biom.load_table(sys.argv[1])
tab.filter(lambda v, i, m: v.sum() >= 1000)
md = pd.read_csv(sys.argv[2], sep='\t', dtype=str).set_index('#SampleID')
md = md[md['env_package'].isin(['human-gut', 'human-skin',
                                'human-oral'])]
o = set(tab.ids()) & set(md.index)
md = md.loc[o]
tab = tab.filter(o).remove_empty()

size = int(sys.argv[3])
keep = []
for _, grp in md.groupby('env_package'):
    ids = list(grp.index)
    random.shuffle(ids)
    keep.extend(ids[:size])
tab = tab.filter(set(keep)).remove_empty()
random.shuffle(keep)
md = md.loc[keep]

md['intentional_mislabel'] = False
md['intentional_contamination'] = False
md['original_env_package'] = md['env_package']

gut = md[md['env_package'] == 'human-gut']
oral = md[md['env_package'] == 'human-oral']
skin = md[md['env_package'] == 'human-skin']

md.loc[gut.index[0], 'env_package'] = 'human-oral'
md.loc[gut.index[1], 'env_package'] = 'human-skin'
md.loc[gut.index[0], 'intentional_mislabel'] = True
md.loc[gut.index[1], 'intentional_mislabel'] = True
md.loc[gut.index[0], 'original_env_package'] = 'human-gut'
md.loc[gut.index[1], 'original_env_package'] = 'human-gut'

md.loc[oral.index[0], 'env_package'] = 'human-gut'
md.loc[oral.index[1], 'env_package'] = 'human-skin'
md.loc[oral.index[0], 'intentional_mislabel'] = True
md.loc[oral.index[1], 'intentional_mislabel'] = True
md.loc[oral.index[0], 'original_env_package'] = 'human-oral'
md.loc[oral.index[1], 'original_env_package'] = 'human-oral'

md.loc[skin.index[0], 'env_package'] = 'human-gut'
md.loc[skin.index[1], 'env_package'] = 'human-oral'
md.loc[skin.index[0], 'intentional_mislabel'] = True
md.loc[skin.index[1], 'intentional_mislabel'] = True
md.loc[skin.index[0], 'original_env_package'] = 'human-skin'
md.loc[skin.index[1], 'original_env_package'] = 'human-skin'

gut_sample = tab.data(gut.index[3], dense=False)
skin_sample = tab.data(skin.index[3], dense=False)
oral_sample = tab.data(oral.index[3], dense=False)

tab.matrix_data[:, tab.index(gut.index[4], 'sample')] += skin_sample
tab.matrix_data[:, tab.index(gut.index[5], 'sample')] += oral_sample

tab.matrix_data[:, tab.index(skin.index[4], 'sample')] += gut_sample
tab.matrix_data[:, tab.index(skin.index[5], 'sample')] += oral_sample

tab.matrix_data[:, tab.index(oral.index[4], 'sample')] += skin_sample
tab.matrix_data[:, tab.index(oral.index[5], 'sample')] += gut_sample

md.loc[gut.index[4], 'intentional_contamination'] = True
md.loc[gut.index[5], 'intentional_contamination'] = True
md.loc[gut.index[6], 'intentional_contamination'] = True
md.loc[skin.index[4], 'intentional_contamination'] = True
md.loc[skin.index[5], 'intentional_contamination'] = True
md.loc[skin.index[6], 'intentional_contamination'] = True
md.loc[oral.index[4], 'intentional_contamination'] = True
md.loc[oral.index[5], 'intentional_contamination'] = True
md.loc[oral.index[6], 'intentional_contamination'] = True

tab_ar = qiime2.Artifact.import_data('FeatureTable[Frequency]', tab)
tab_ar.save(sys.argv[4] + '.biom.qza')
md.to_csv(sys.argv[4] + '.tsv', sep='\t', index=True, header=True)
