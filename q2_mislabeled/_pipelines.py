# ----------------------------------------------------------------------------
# Copyright (c) 2022-, Mislabeled development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd
import qiime2
import biom


# defaults from HMP SOP
# https://www.hmpdacc.org/hmp/doc/QiimeCommunityProfiling.pdf
def within_dataset(ctx, table, env, alleged_min_probability=0.25,
                   env_min_proportion=0.6, n_jobs=1):
    feat_filter = ctx.get_action('feature_table', 'filter_features')
    rarefy = ctx.get_action('feature_table', 'rarefy')
    classifier = ctx.get_action('sample_classifier', 'classify_samples_ncv')
    st = ctx.get_action('sourcetracker2', 'gibbs')

    env_df = env.to_dataframe()
    c = env_df.columns[0]  # MetadataColumn, so our col of interest is idx 0

    # get our table dimensions
    nfeat, nsamp = table.view(biom.Table).shape

    # From the HMP SOP
    # Rarefy OTU tables at depth 100 (n.b., classifier is faster now so
    # we use a depth of 1000):
    raretab, = rarefy(table, sampling_depth=1000)

    # From the HMP SOP
    # Drop all OTUs present in less than 1% of the samples:
    filttab, = feat_filter(raretab, min_samples=int(nsamp * 0.01))
    _, feat, prob = classifier(raretab, env, n_jobs=n_jobs)
    prob_df = prob.view(pd.DataFrame)

    # gather our probabilities, and store the alleged probability for the
    # reported environment type. note that care has to be taken with the
    # possibility that samples were removed from the input table due to the
    # rarefaction procedure.
    env_df['alleged_probability'] = 'Not applicable'
    overlap = [i for i in env_df.index if i in prob_df.index]
    env_df.loc[overlap, 'alleged_probability'] = \
        [prob_df.loc[r.Index, getattr(r, c)]
         for r in env_df.loc[overlap].itertuples()]
    prob_below_min = \
        env_df.loc[overlap, 'alleged_probability'] < alleged_min_probability

    env_df['Mislabeled'] = 'Not applicable'
    env_df.loc[prob_below_min, 'Mislabeled'] = True
    env_df.loc[~prob_below_min, 'Mislabeled'] = False

    # qiime2.Metadata cannot handle bool dtype which would occur if no
    # samples are dropped from rarefaction
    env_df['Mislabeled'] = env_df['Mislabeled'].astype(str)

    # record what we believe the correct label to be. for mislabeled samples,
    # pull the most probable label. For non-mislabeled samples, record the
    # original label
    env_df['corrected_label'] = 'Not applicable'
    mislabeled = env_df[env_df['Mislabeled'] == 'True']
    notmislabeled = env_df[env_df['Mislabeled'] == 'False']

    env_df.loc[mislabeled.index, 'corrected_label'] = \
        [prob_df.loc[r.Index].idxmax()
         for r in env_df.loc[mislabeled.index].itertuples()]

    env_df.loc[notmislabeled.index, 'corrected_label'] = \
        [prob_df.loc[r.Index].idxmax()
         for r in env_df.loc[notmislabeled.index].itertuples()]

    # We deviate slightly from the HMP SOP here. Specifically, instead of
    # creating a copy of the mapping file, we augment our mapping file with
    # what samples are below our probability threshold. As the HMP SOP notes,
    # the contaminatin check is then run "...for all remaining samples..."
    env_df['SourceSink'] = ['sink' if v else 'source' for v in prob_below_min]

    # From the HMP SOP:
    # Reduce number of features further before running SourceTracker
    # (to reduce run-time): Remove OTUs present in <1% of the samples, then
    # rarefy at depth 100 (n.b. ST is faster now so we use 1000 here), then
    # again remove OTUs present in <1% of the remaining samples:
    filttab, = feat_filter(table, min_samples=int(nsamp * 0.01))
    raretab, = rarefy(filttab, sampling_depth=1000)
    refilttab, = feat_filter(raretab, min_samples=int(nsamp * 0.01))

    # Run source tracker in leave-one-out mode. We are disabling rarefaction
    # as that's already been resolved.
    proportions, _, _, _ = st(refilttab, qiime2.Metadata(env_df), jobs=n_jobs,
                              source_category_column=c, loo=True,
                              source_rarefaction_depth=0,
                              sink_rarefaction_depth=0)
    proportions_df = proportions.view(pd.DataFrame).T

    # gather our contamination levels, and store the minimum for the reported
    # environment type. note that care has to be taken with the possibility
    # that samples were removed from the input table due to the rarefaction
    # procedure.
    env_df['min_proportion'] = 'Not applicable'
    overlap = [i for i in env_df.index if i in proportions_df.index]
    env_df.loc[overlap, 'min_proportion'] = \
        [proportions_df.loc[r.Index, getattr(r, c)]
         for r in env_df.loc[overlap].itertuples()]
    comm_below_min = env_df.loc[overlap, 'min_proportion'] < env_min_proportion

    # From the HMP SOP
    # Add 'Mislabeled' column to the final mapping file, with 'NA' (n.b., we
    # use 'Not applicable') where mislabeling was not estimated (samples with <
    # 1000 [sic] sequences), 'TRUE' when the estimated probability of the
    # alleged label was < .25, 'FALSE' otherwise. Add 'Contaminated' column
    # with 'NA' when 'Mislabeled' is 'TRUE' or 'NA', 'TRUE' when 'Mislabeled'
    # is FALSE and 'Max_Proportion_this_Env' < .6, and 'FALSE' otherwise.
    env_df['Contaminated'] = False
    env_df.loc[prob_below_min, 'Contaminated'] = 'NA'
    contaminated = comm_below_min & (~prob_below_min.loc[overlap])
    contaminated_samples = contaminated[contaminated].index
    env_df.loc[contaminated_samples, 'Contaminated'] = True

    # qiime2.Metadata cannot handle bool, which would happen in an unusual
    # edge case here but let's protect ourselves anyway
    env_df['Contaminated'] = env_df['Contaminated'].astype(str)

    mislabelings = qiime2.Artifact.import_data('SampleData[Mislabeled]',
                                               env_df)
    return mislabelings
