# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from qiime2 import Metadata

from .plugin_setup import plugin
import pandas as pd
from ._format import TSVFormat


@plugin.register_transformer
def _1(ff: TSVFormat) -> pd.DataFrame:
    with ff.open() as fh:
        df = pd.read_csv(fh, sep='\t', dtype=str).set_index('#SampleID')
    df['alleged_probability'] = pd.to_numeric(df['alleged_probability'],
                                              errors='coerce')
    df['min_proportion'] = pd.to_numeric(df['min_proportion'],
                                         errors='coerce')
    return df


@plugin.register_transformer
def _2(data: pd.DataFrame) -> TSVFormat:
    ff = TSVFormat()
    with ff.open() as fh:
        data.to_csv(fh, sep='\t', index=True, header=True)
    return ff


@plugin.register_transformer
def _3(ff: TSVFormat) -> Metadata:
    return Metadata.load(str(ff))
