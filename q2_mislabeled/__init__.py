# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from ._pipelines import within_dataset, against_dataset
from . import _version
__version__ = _version.get_versions()['version']

__all__ = ['within_dataset', 'against_dataset']
