# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import importlib
from qiime2.plugin import Plugin, MetadataColumn, Float, Categorical, Int
from q2_types.feature_table import FeatureTable, Frequency
from q2_types.sample_data import SampleData

from ._types import Mislabeled
from ._format import TSVDirectoryFormat, TSVFormat
import q2_mislabeled


plugin = Plugin(
    name='mislabeled',
    version=q2_mislabeled.__version__,
    website='https://github.com/biocore/q2-mislabeled',
    package='q2_mislabeled',
    description="Methods for identifying mislabeled samples",
    short_description="Methods for identifying mislabeled samples"
)

plugin.register_semantic_types(Mislabeled)
plugin.register_formats(TSVDirectoryFormat)
plugin.register_artifact_class(
    SampleData[Mislabeled],
    directory_format=TSVDirectoryFormat)
#plugin.register_semantic_type_to_format(Mislabeled,
#                                        artifact_format=TSVDirectoryFormat)

plugin.pipelines.register_function(
    name="Within dataset mislabelings",
    description="Identify mislabelings and contaminated samples within a "
                "specific dataset based on the HMP SOP",
    function=q2_mislabeled.within_dataset,
    inputs={'table': FeatureTable[Frequency]},
    parameters={'alleged_min_probability': Float,
                'env_min_proportion': Float,
                'env': MetadataColumn[Categorical],
                'n_jobs': Int},
    outputs=[('mislabelings', SampleData[Mislabeled])],
    input_descriptions={'table': 'The feature table to examine'},
    parameter_descriptions={
        'alleged_min_probability': 'The minimum probability a sample must '
                                   'must have from classification to be '
                                   'considered correctly classified.',
        'env_min_proportion': 'The minimum environment proportion a sample '
                              'must have from source tracking to be '
                              'considered correctly classified',
        'env': 'The column in the metadata with the variable to assess '
               'mislabelings with',
        'n_jobs': 'The number of CPUs to use'},
    output_descriptions={'mislabelings': 'A tabular file describing '
                                         'mislabelings per sample'}
)

importlib.import_module('q2_mislabeled._transformers')
