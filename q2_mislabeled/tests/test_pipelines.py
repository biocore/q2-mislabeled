# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import unittest
import pandas as pd
import pandas.testing as pdt

from q2_mislabeled._pipelines import (_set_mislabeled, _set_contamination,
                                      NOT_APPLICABLE)


class Tests(unittest.TestCase):
    def test_set_mislabeled(self):
        env_df = pd.DataFrame([['foo', 'fecal'],
                               ['bar', 'oral'],
                               ['baz', 'skin'],
                               ['extra', 'fecal']],
                              columns=['#SampleID', 'env'])
        env_df.set_index('#SampleID', inplace=True)
        prob_df = pd.DataFrame([['bar', 0.5, 0.2, 0.3],
                                ['baz', 0.3, 0.3, 0.4],
                                ['foo', 0.6, 0.2, 0.2]],
                               columns=['#SampleID', 'fecal', 'oral', 'skin'])
        prob_df.set_index('#SampleID', inplace=True)

        exp = pd.DataFrame([['foo', 'fecal', 0.6, 'False', 'fecal'],
                            ['bar', 'oral', 0.2, 'True', 'fecal'],
                            ['baz', 'skin', 0.4, 'False', 'skin'],
                            ['extra', 'fecal', NOT_APPLICABLE,
                             NOT_APPLICABLE, NOT_APPLICABLE]],
                           columns=['#SampleID', 'env', 'alleged_probability',
                                    'Mislabeled', 'corrected_label'])
        exp.set_index('#SampleID', inplace=True)
        exp_below = pd.Series([False, True, False],
                              index=['foo', 'bar', 'baz'],
                              name='alleged_probability')
        exp_below.index.name = '#SampleID'

        obs_below = _set_mislabeled(env_df, prob_df, 'env', 0.25)

        pdt.assert_frame_equal(env_df, exp)
        pdt.assert_series_equal(obs_below, exp_below)

    def test_set_contamination(self):
        env_df = pd.DataFrame([['foo', 'fecal', 0.6, 'False', 'fecal'],
                               ['bar', 'oral', 0.2, 'True', 'fecal'],
                               ['baz', 'skin', 0.4, 'False', 'skin'],
                               ['extra', 'fecal', NOT_APPLICABLE,
                                NOT_APPLICABLE, NOT_APPLICABLE]],
                              columns=['#SampleID', 'env',
                                       'alleged_probability', 'Mislabeled',
                                       'corrected_label'])
        env_df.set_index('#SampleID', inplace=True)

        prop_df = pd.DataFrame([['bar', 0.5, 0.2, 0.3],
                                ['baz', 0.3, 0.3, 0.4],
                                ['foo', 0.7, 0.1, 0.2]],
                               columns=['#SampleID', 'fecal', 'oral', 'skin'])
        prop_df.set_index('#SampleID', inplace=True)

        below = pd.Series([False, True, False],
                          index=['foo', 'bar', 'baz'],
                          name='alleged_probability')
        below.index.name = '#SampleID'

        exp = pd.DataFrame([['foo', 'fecal', 0.6, 'False', 'fecal', 0.7,
                             'False'],
                            ['bar', 'oral', 0.2, 'True', 'fecal', 0.2,
                             NOT_APPLICABLE],
                            ['baz', 'skin', 0.4, 'False', 'skin', 0.4, 'True'],
                            ['extra', 'fecal', NOT_APPLICABLE,
                             NOT_APPLICABLE, NOT_APPLICABLE,
                             NOT_APPLICABLE, 'False']],
                           columns=['#SampleID', 'env', 'alleged_probability',
                                    'Mislabeled', 'corrected_label',
                                    'min_proportion', 'Contaminated'])
        exp.set_index('#SampleID', inplace=True)

        _set_contamination(env_df, prop_df, 'env', below, 0.6)

        pdt.assert_frame_equal(env_df, exp)


if __name__ == '__main__':
    unittest.main()
