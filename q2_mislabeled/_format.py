# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import qiime2.plugin.model as model


class TSVFormat(model.TextFileFormat):
    HEADER = {'alleged_probability',
              'min_proportion',
              'Mislabeled',
              'Contaminated'}

    def sniff(self):
        with self.open() as fh:
            header = fh.readline()
            if self.HEADER.issubset(set(header.strip().split('\t'))):
                return True
            else:
                return False


TSVDirectoryFormat = model.SingleFileDirectoryFormat(
    'TSVDirectoryFormat', 'mislabeled.tsv', TSVFormat)
