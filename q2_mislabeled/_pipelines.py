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

NOT_APPLICABLE = 'not applicable'


# defaults from HMP SOP
# https://www.hmpdacc.org/hmp/doc/QiimeCommunityProfiling.pdf
def within_dataset(ctx, table, env, alleged_min_probability=0.25,
                   env_min_proportion=0.6, n_jobs=1, sampling_depth=1000):
    feat_filter = ctx.get_action('feature_table', 'filter_features')
    rarefy = ctx.get_action('feature_table', 'rarefy')
    classifier = ctx.get_action('sample_classifier', 'classify_samples_ncv')
    st = ctx.get_action('sourcetracker2', 'gibbs')

    env_df = env.to_dataframe()
    c = env_df.columns[0]  # MetadataColumn, so our col of interest is idx 0

    # get our table dimensions
    nfeat, nsamp = table.view(biom.Table).shape
    min_samples = int(nsamp * 0.01)

    # From the HMP SOP
    # Rarefy OTU tables at depth 100 (n.b., classifier is faster now so
    # we use a depth of 1000):
    raretab, = rarefy(table, sampling_depth=sampling_depth)

    # From the HMP SOP
    # Drop all OTUs present in less than 1% of the samples:
    filttab, = feat_filter(raretab, min_samples=min_samples)
    _, feat, prob = classifier(filttab, env, n_jobs=n_jobs)
    prob_df = prob.view(pd.DataFrame)

    # We deviate slightly from the HMP SOP here. Specifically, instead of
    # creating a copy of the mapping file, we augment our mapping file with
    # what samples are below our probability threshold. As the HMP SOP notes,
    # the contaminatin check is then run "...for all remaining samples..."
    prob_below_min = _set_mislabeled(env_df, prob_df, c,
                                     alleged_min_probability)

    # set our source/sink variable. Note that since we are using LOO, we are
    # only evaluating the "source" samples for contamination. In this case,
    # that means the samples which do not appear to be mislabeled.
    env_df.loc[prob_below_min.index, 'SourceSink'] = ['sink' if v else 'source'
                                                      for v in prob_below_min]

    # From the HMP SOP:
    # Reduce number of features further before running SourceTracker
    # (to reduce run-time): Remove OTUs present in <1% of the samples, then
    # rarefy at depth 100 (n.b. ST is faster now so we use 1000 here), then
    # again remove OTUs present in <1% of the remaining samples:
    if min_samples > 1:
        filttab, = feat_filter(table, min_samples=min_samples)
    else:
        filttab = table
    raretab, = rarefy(filttab, sampling_depth=sampling_depth)
    if min_samples > 1:
        refilttab, = feat_filter(raretab, min_samples=min_samples)
    else:
        refilttab = raretab

    # Run source tracker in leave-one-out mode. We are disabling rarefaction
    # as that's already been resolved.
    st_metadata = qiime2.Metadata(env_df[['SourceSink', c]])
    proportions, _ = st(refilttab, st_metadata, jobs=n_jobs,
                        source_category_column=c, loo=True,
                        source_rarefaction_depth=0,
                        sink_rarefaction_depth=0)
    proportions_df = proportions.view(pd.DataFrame).T

    _set_contamination(env_df, proportions_df, c, prob_below_min,
                       env_min_proportion)

    mislabelings = qiime2.Artifact.import_data('SampleData[Mislabeled]',
                                               env_df)
    return mislabelings


def against_dataset(ctx, focus, reference, focus_env, reference_env,
                    alleged_min_probability=0.25, env_min_proportion=0.6,
                    n_jobs=1, sampling_depth=1000):
    feat_filter = ctx.get_action('feature_table', 'filter_features')
    merge_tables = ctx.get_action('feature_table', 'merge')
    rarefy = ctx.get_action('feature_table', 'rarefy')
    fit_classifier = ctx.get_action('sample_classifier', 'fit_classifier')
    pred_classifier = ctx.get_action('sample_classifier',
                                     'predict_classification')
    st = ctx.get_action('sourcetracker2', 'gibbs')

    focus_env_df = focus_env.to_dataframe()
    focus_column = focus_env_df.columns[0]
    ref_env_df = reference_env.to_dataframe()
    ref_column = ref_env_df.columns[0]

    focus_column_values = set(focus_env_df[focus_column].unique())
    ref_column_values = set(ref_env_df[ref_column].unique())
    if not focus_column_values.issubset(ref_column_values):
        raise ValueError("The focus dataset contains environments that are "
                         "not represented in the reference dataset.")

    focus_env_df['SourceSink'] = 'sink'
    ref_env_df['SourceSink'] = 'source'

    if focus_column != ref_column:
        focus_env_df.rename(columns={focus_column: ref_column}, inplace=True)

    env_df = pd.concat([focus_env_df, ref_env_df])

    # get our table dimensions
    ref_nfeat, ref_nsamp = reference.view(biom.Table).shape
    foc_nfeat, foc_nsamp = focus.view(biom.Table).shape
    ref_min_samples = int(ref_nsamp * 0.01)
    foc_min_samples = int(foc_nsamp * 0.01)

    # From the HMP SOP
    # Rarefy OTU tables at depth 100 (n.b., classifier is faster now so
    # we use a depth of 1000):
    ref_raretab, = rarefy(reference, sampling_depth=sampling_depth)
    foc_raretab, = rarefy(focus, sampling_depth=sampling_depth)

    # From the HMP SOP
    # Drop all OTUs present in less than 1% of the samples:
    if ref_min_samples > 1:
        ref_filttab, = feat_filter(ref_raretab, min_samples=ref_min_samples)
    else:
        ref_filttab = ref_raretab
    if foc_min_samples > 1:
        foc_filttab, = feat_filter(foc_raretab, min_samples=foc_min_samples)
    else:
        foc_filttab = foc_raretab

    # construct a classifier from the reference data, and predict the samples
    # in the focus table
    estimator, _ = fit_classifier(ref_filttab, reference_env, n_jobs=n_jobs)
    _, prob = pred_classifier(foc_filttab, estimator, n_jobs=n_jobs)
    prob_df = prob.view(pd.DataFrame)

    # From the HMP SOP:
    # Reduce number of features further before running SourceTracker
    # (to reduce run-time): Remove OTUs present in <1% of the samples, then
    # rarefy at depth 100 (n.b. ST is faster now so we use 1000 here), then
    # again remove OTUs present in <1% of the remaining samples:
    if ref_min_samples > 1:
        ref_filttab, = feat_filter(reference, min_samples=ref_min_samples)
    else:
        ref_filttab = reference

    if foc_min_samples > 1:
        foc_filttab, = feat_filter(focus, min_samples=foc_min_samples)
    else:
        foc_filttab = focus

    ref_raretab, = rarefy(ref_filttab, sampling_depth=sampling_depth)
    foc_raretab, = rarefy(foc_filttab, sampling_depth=sampling_depth)

    if ref_min_samples > 1:
        ref_refilttab, = feat_filter(ref_raretab, min_samples=ref_min_samples)
    else:
        ref_refilttab = ref_raretab

    if foc_min_samples > 1:
        foc_refilttab, = feat_filter(foc_raretab, min_samples=foc_min_samples)
    else:
        foc_refilttab = foc_raretab

    merged, = merge_tables([ref_refilttab, foc_refilttab])

    # Run source tracker. We are disabling rarefaction
    # as that's already been resolved.
    st_metadata = qiime2.Metadata(env_df[['SourceSink', ref_column]])
    proportions, _ = st(merged, st_metadata, jobs=n_jobs,
                        source_category_column=ref_column, loo=False,
                        source_rarefaction_depth=0,
                        sink_rarefaction_depth=0)
    proportions_df = proportions.view(pd.DataFrame).T

    prob_below_min = _set_mislabeled(env_df, prob_df, ref_column,
                                     alleged_min_probability)
    _set_contamination(env_df, proportions_df, ref_column, prob_below_min,
                       env_min_proportion)

    env_df = env_df.loc[focus_env_df.index]
    mislabelings = qiime2.Artifact.import_data('SampleData[Mislabeled]',
                                               env_df)
    return mislabelings


def _set_mislabeled(env_df, prob_df, c, alleged_min_probability):
    # gather our probabilities, and store the alleged probability for the
    # reported environment type. note that care has to be taken with the
    # possibility that samples were removed from the input table due to the
    # rarefaction procedure.
    env_df['alleged_probability'] = NOT_APPLICABLE
    overlap = [i for i in env_df.index if i in prob_df.index]
    env_df.loc[overlap, 'alleged_probability'] = \
        [prob_df.loc[r.Index, getattr(r, c)]
         for r in env_df.loc[overlap].itertuples()]
    prob_below_min = \
        env_df.loc[overlap, 'alleged_probability'] < alleged_min_probability

    is_mislabeled = prob_below_min[prob_below_min]
    is_not_mislabeled = prob_below_min[~prob_below_min]
    env_df['Mislabeled'] = NOT_APPLICABLE
    env_df.loc[is_mislabeled.index, 'Mislabeled'] = True
    env_df.loc[is_not_mislabeled.index, 'Mislabeled'] = False

    # qiime2.Metadata cannot handle bool dtype which would occur if no
    # samples are dropped from rarefaction
    env_df['Mislabeled'] = env_df['Mislabeled'].astype(str)

    # record what we believe the correct label to be. for mislabeled samples,
    # pull the most probable label. For non-mislabeled samples, record the
    # original label
    env_df['corrected_label'] = NOT_APPLICABLE
    mislabeled = env_df[env_df['Mislabeled'] == 'True']
    notmislabeled = env_df[env_df['Mislabeled'] == 'False']

    env_df.loc[mislabeled.index, 'corrected_label'] = \
        [prob_df.loc[r.Index].idxmax()
         for r in env_df.loc[mislabeled.index].itertuples()]

    env_df.loc[notmislabeled.index, 'corrected_label'] = \
        [prob_df.loc[r.Index].idxmax()
         for r in env_df.loc[notmislabeled.index].itertuples()]

    return prob_below_min


def _set_contamination(env_df, proportions_df, c, prob_below_min,
                       env_min_proportion):
    # gather our contamination levels, and store the minimum for the reported
    # environment type. note that care has to be taken with the possibility
    # that samples were removed from the input table due to the rarefaction
    # procedure.
    env_df['min_proportion'] = NOT_APPLICABLE
    overlap = [i for i in env_df.index if i in proportions_df.index]
    env_df.loc[overlap, 'min_proportion'] = \
        [proportions_df.loc[r.Index, getattr(r, c)]
         for r in env_df.loc[overlap].itertuples()]
    comm_below_min = env_df.loc[overlap, 'min_proportion'] < env_min_proportion

    # From the HMP SOP
    # Add 'Mislabeled' column to the final mapping file, with 'NA' (n.b., we
    # use NOT_APPLICABLE) where mislabeling was not estimated (samples with <
    # 1000 [sic] sequences), 'TRUE' when the estimated probability of the
    # alleged label was < .25, 'FALSE' otherwise. Add 'Contaminated' column
    # with 'NA' when 'Mislabeled' is 'TRUE' or 'NA', 'TRUE' when 'Mislabeled'
    # is FALSE and 'Max_Proportion_this_Env' < .6, and 'FALSE' otherwise.
    is_mislabeled = prob_below_min[prob_below_min]
    env_df['Contaminated'] = False
    env_df.loc[is_mislabeled.index, 'Contaminated'] = NOT_APPLICABLE
    contaminated = comm_below_min & (~prob_below_min.loc[overlap])
    contaminated_samples = contaminated[contaminated]
    env_df.loc[contaminated_samples.index, 'Contaminated'] = True

    # qiime2.Metadata cannot handle bool, which would happen in an unusual
    # edge case here but let's protect ourselves anyway
    env_df['Contaminated'] = env_df['Contaminated'].astype(str)
