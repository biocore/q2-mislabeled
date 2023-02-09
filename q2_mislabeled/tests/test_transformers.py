# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import io
from qiime2 import Metadata
import pandas as pd
import pandas.testing as pdt
from unittest import main
from qiime2.plugin.testing import TestPluginBase
from q2_mislabeled._pipelines import NOT_APPLICABLE
from q2_mislabeled._format import TSVFormat
import numpy as np


NA = NOT_APPLICABLE


# tests based off of
# https://github.com/qiime2/q2-demux/blob/master/q2_demux/tests/test_transformer.py  # noqa
class TransformerTests(TestPluginBase):
    package = 'q2_mislabeled.tests'

    def setUp(self):
        super().setUp()

        self.df = pd.DataFrame([
            ['a', 'x', 0.01, 'True', 'y', 'sink', np.nan, NA],
            ['b', 'x', 0.75, 'False', 'x', 'sink', 0.9, 'False'],
            ['c', 'y', 0.65, 'False', 'y', 'sink', 0.1, 'True'],
            ['d', 'y', 0.7, 'False', 'y', 'source', 0.7, 'False']],
            columns=['#SampleID', 'env_package', 'alleged_probability',
                     'Mislabeled', 'corrected_label', 'SourceSink',
                     'min_proportion', 'Contaminated']).set_index('#SampleID')

    def test_df_to_tsv(self):
        transformer = self.get_transformer(pd.DataFrame, TSVFormat)
        obs = transformer(self.df)

        with obs.open() as obs_fh:
            obs_df = pd.read_csv(io.StringIO(obs_fh.read()), sep='\t',
                                 dtype=str)
        obs_df['min_proportion'] = pd.to_numeric(obs_df['min_proportion'],
                                                 errors='coerce')
        obs_df['alleged_probability'] = \
            pd.to_numeric(obs_df['alleged_probability'], errors='coerce')

        obs_df.set_index('#SampleID', inplace=True)
        pdt.assert_frame_equal(obs_df, self.df)

    def test_tsv_to_df(self):
        transformer = self.get_transformer(TSVFormat, pd.DataFrame)
        ff = TSVFormat()
        with ff.open() as fh:
            self.df.to_csv(fh, sep='\t', index=True, header=True)
        obs = transformer(ff)
        print([type(x) for x in obs['Mislabeled']])
        print([type(x) for x in self.df['Mislabeled']])
        pdt.assert_frame_equal(obs, self.df)

    def test_tsv_to_metadata(self):
        transformer = self.get_transformer(TSVFormat, Metadata)
        ff = TSVFormat()
        with ff.open() as fh:
            self.df.to_csv(fh, sep='\t', index=True, header=True)
        obs = transformer(ff)
        self.assertEqual(obs, Metadata(self.df))


if __name__ == '__main__':
    main()
