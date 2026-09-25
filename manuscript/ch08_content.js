// Chapter 8 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "8  Assessing Covariate Balance in the New Datasets"],

["h2", "8.1  Purpose and scope of this chapter"],

["p", "Chapters 5, 6 and 7 produced adjusted datasets by matching, weighting and stratification, and each chapter deferred the same question to this one: did the adjustment achieve what it was meant to achieve? The purpose of every propensity score method is to make the treated and control groups comparable, so that the difference in their outcomes can be attributed to the programme rather than to the differences between the persons in each group. The comparability that results is called covariate balance, and assessing it is the step that researchers are expected to report before any estimate is presented."],

["p", "The chapter has two parts. The first teaches the conventional diagnostics in full: the standardised mean difference that Chapter 2 introduced, the balance table built around it, and the checks that go beyond the mean (i.e., variance ratios, distributional comparisons, and balance on squares and interactions of the covariates). The second asks what those diagnostics can and cannot tell a researcher, using the six draws of Chapters 5 to 7 and the truth file to score each adjusted dataset. Its central finding is that, among datasets that pass the diagnostics, the diagnostics do not rank them by the bias of the estimates they produce, and in the comparison that Chapter 5 left open the most widely reported of them ranks the two samples the wrong way in every draw. The chapter then describes a secondary check, balance on a prognostic score, that does track the bias, and explains why the book presents it as a check rather than as a replacement for the conventional diagnostics."],

["p", "By the end of the chapter, readers should be able to build and read a balance table for a matched, weighted or stratified dataset, to compute the diagnostics beyond the mean and interpret them, and to recognise what a passing balance table certifies and what it does not. They should also be able to recognise when a balance diagnostic is flagging a real problem, which it does for the boosted score of Chapter 3, and to compute the prognostic score check as a secondary diagnostic."],

["p", "Three scoping notes. The first is that the chapter concerns the ATT throughout, as Chapter 5 did, and uses the same six draws and both scores of Chapter 3; the untrimmed population is used, so that the samples assessed are those whose bias Chapters 5 to 7 reported. The second is that no new estimator is introduced, and the estimates quoted are those of the earlier chapters, recomputed on the same draws. The third is that the bias that no diagnostic built from the observed data can detect is left to Chapter 10, which examines unobserved confounding directly."],

["h2", "8.2  The balance that matters"],

["p", "It is useful to begin with what balance is for, because the answer determines what a balance diagnostic can hope to achieve. Every estimator of the ATT in Chapters 5 to 7 compares a (possibly weighted) mean of the treated persons' observed outcomes with a (possibly weighted) mean of the controls' observed outcomes. The treated persons' observed outcome is their outcome with treatment, and the true ATT is the mean, over the same treated persons, of their outcome with treatment less their outcome without it. Subtracting the one from the other shows that the error of the estimate is exactly the difference between the treated persons' mean outcome without treatment and the controls' weighted mean outcome. In other words, the bias of an ATT estimate is the imbalance, between the adjusted groups, in the untreated outcome."],

["p", "Script 8.2 confirms the identity numerically: across the 96 samples of this chapter (i.e., eight samples on each of two scores in each of six draws), the estimate less the truth and the imbalance in the untreated outcome differ by less than a trillionth of a dollar. The identity is algebraic rather than empirical, but it has a practical consequence that is easy to overlook. The untreated outcome of the treated persons can never be observed, so the balance that matters can never be checked directly. Every balance diagnostic is therefore a proxy for it, and the covariates are useful in proportion to how well they predict the outcome that the treated persons would have had without the programme."],

["p", "Section 5.2.1 argued that matching is a design step and should be settled without reference to the 2019 earnings that the study is about, and the same principle governs weighting and stratification. The conventional diagnostics respect that principle, since they are computed from the covariates alone. The question for the rest of the chapter is how good a proxy they are, and whether anything that respects the principle can do better."],

["h2", "8.3  The standardised mean difference"],
["h3", "8.3.1  Definition and threshold"],

["p", "The standardised mean difference of a covariate is the difference between the treated and control means, divided by a standard deviation, so that covariates measured on different scales can be compared. Chapter 2 used it to describe the imbalance before any adjustment, and it is the most widely reported balance diagnostic in applied work. A value of 0.1 (i.e., a tenth of a standard deviation) is the conventional threshold below which a covariate is regarded as balanced; an older convention of 0.25 is still sometimes seen, and a stricter one of 0.05 is used in some evaluation standards (e.g., in education research), particularly for covariates believed to be strongly related to the outcome."],

["p", "Researchers are sometimes tempted to test balance with a t-test or a chi-squared test for each covariate, and it is recommended that they do not. A significance test answers whether the difference in the sample could have arisen by chance, which depends on the size of the sample as much as on the size of the difference: a matched sample that discards many controls can therefore appear better balanced simply because it is smaller. Balance is a property of the sample in hand rather than of a population from which it was drawn, and the standardised difference, which does not depend on the sample size, measures it directly."],

["h3", "8.3.2  Weighted samples and the denominator"],

["p", "All three families of method can be assessed with one calculation, because each produces a weight for every person: a matched person has a weight equal to the number of times they were used, a person left unmatched has a weight of zero, and the weights of Chapters 6 and 7 are used as they stand. The weighted means of the treated and controls then replace the ordinary means. Fragment 8.1 shows the calculation, which Script 8.1 and Script 8.2 apply to every sample in this chapter."],

["frag", [
  "def smd(V, wt, wc, sd):",
  "    \"\"\"Weighted standardised difference, treated less controls.\"\"\"",
  "    return (wt @ V / wt.sum() - wc @ V / wc.sum()) / sd",
  "",
  "sd = np.sqrt((V[D == 1].var(0) + V[D == 0].var(0)) / 2)   # fixed, before adjustment",
  "balance = smd(V, wt, wc, sd)",
], "Fragment 8.1  The weighted standardised mean difference. Full script: ch08/08_01_balance_table.py"],

["p", "The choice of denominator deserves a sentence of justification. Fragment 8.1 fixes it at the pooled standard deviation of the unadjusted sample, so that a change in the standardised difference reflects a change in the means rather than a change in the spread. Some software recomputes the standard deviation within the adjusted sample instead; causalml's create_table_one, used in Table 8.1, does so. In these data the two conventions differ by less than 0.001 after matching, and the choice therefore matters little here; it can matter more when an adjustment discards a large and unusual part of the sample, and the fixed denominator is the safer default."],

["h3", "8.3.3  A balance table"],

["p", "Table 8.1 is a balance table for the propensity score matched sample of Chapter 5 on the primary dataset. It reports, for each of the eighteen covariates of the propensity model, the treated mean, the control mean before and after matching, and the standardised difference before and after, in the form that most reports and journals expect. The table was produced with causalml's create_table_one, which takes a matched dataset and returns the means, standard deviations and standardised differences directly, and the last column repeats the standardised difference with the fixed denominator of Fragment 8.1."],

["tab", "8.1", "A balance table: propensity score matching, primary dataset.",
  [2500, 1000, 1000, 1000, 1000, 1000, 1526],
  ["Covariate", "Treated mean", "Control mean, before", "SMD, before", "Control mean, after", "SMD, after", "SMD, fixed denominator"],
  [
    ["age", "38.899", "40.587", "−0.155", "39.101", "−0.017", "−0.017"],
    ["female", "0.493", "0.490", "+0.006", "0.495", "−0.005", "−0.005"],
    ["dependent children", "0.785", "0.768", "+0.024", "0.791", "−0.008", "−0.008"],
    ["highest education", "1.645", "1.943", "−0.230", "1.647", "−0.001", "−0.001"],
    ["remoteness", "0.656", "0.377", "+0.348", "0.656", "−0.003", "−0.004"],
    ["SEIFA decile", "5.494", "6.156", "−0.276", "5.502", "−0.002", "−0.002"],
    ["fortnights on payment", "15.288", "11.369", "+0.394", "15.285", "−0.001", "−0.001"],
    ["long-term recipient", "0.437", "0.268", "+0.358", "0.435", "+0.002", "+0.002"],
    ["GP attendances", "3.187", "3.117", "+0.027", "3.145", "+0.016", "+0.016"],
    ["mental health item", "0.153", "0.098", "+0.167", "0.152", "+0.001", "+0.001"],
    ["log earnings 2014", "10.364", "10.493", "−0.226", "10.372", "−0.013", "−0.013"],
    ["earnings 2014 missing", "0.092", "0.069", "+0.087", "0.090", "+0.006", "+0.007"],
    ["log earnings 2015", "10.366", "10.503", "−0.255", "10.376", "−0.017", "−0.017"],
    ["earnings 2015 missing", "0.077", "0.061", "+0.065", "0.079", "−0.007", "−0.007"],
    ["log earnings 2016", "10.088", "10.309", "−0.341", "10.084", "+0.009", "+0.009"],
    ["earnings 2016 missing", "0.170", "0.113", "+0.164", "0.165", "+0.013", "+0.014"],
    ["earnings drop 2016", "0.162", "0.103", "+0.200", "0.169", "−0.022", "−0.022"],
    ["earnings drop missing", "0.226", "0.159", "+0.171", "0.223", "+0.007", "+0.008"],
  ],
  "Logistic score, eligible population, seed 20260808: 4,867 treated persons, 37,708 controls and 4,862 matched pairs (one-to-one, without replacement, caliper 0.1 standard deviations of the logit of the score). SMD is the treated mean less the control mean over a standard deviation: recomputed in the matched sample by create_table_one in the sixth column, and fixed at the unadjusted pooled value in the last.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "Before matching, 13 of the 18 covariates exceed the 0.1 threshold, led by fortnights on payment at +0.394 and long-term receipt at +0.358, which is the selection bias that Chapter 2 described: the persons who commence the programme have spent longer on income support and earned less in the years before. After matching, no covariate exceeds 0.1 and the largest standardised difference is 0.022, for the earnings drop of 2016. By the standard that most researchers apply, and that most journals require, this is a well-balanced sample."],

["h2", "8.4  Beyond the mean"],

["p", "A standardised difference compares means, and two groups can have equal means while differing in other ways (e.g., one group may be more spread out, or the two may differ in the tails of the distribution, or in how two covariates vary together). Because the outcome may depend on those features, several further diagnostics are commonly recommended. Basu, Polsky and Manning argued, in a setting with a skewed outcome much like earnings, that balance on means is a weak certificate and that higher moments and covariances also need to be checked, and Chapter 3 anticipated that this chapter would test whether interactions balance after matching."],

["p", "Three diagnostics are examined here. The variance ratio is the variance of a covariate in the treated group divided by its variance in the control group; a ratio between 0.8 and 1.25 is usually regarded as acceptable, and a ratio outside 0.5 to 2 as a serious imbalance. The Kolmogorov–Smirnov distance is the largest gap between the cumulative distributions of a covariate in the two groups, and it detects differences anywhere in the distribution rather than only in the mean. The third is balance on constructed terms, which applies the standardised difference to the square of each non-binary covariate and to the product of every pair of covariates, 164 terms in all, so that differences in spread and in covariance are assessed on the same scale as the means."],

["frag", [
  "def variance_ratio(V, wt, wc):",
  "    return wvar(V, wt) / wvar(V, wc)",
  "",
  "def ks(v, wt, wc):                 # largest gap between the two weighted CDFs",
  "    o = np.argsort(v)",
  "    return np.abs(np.cumsum(wt[o]) / wt.sum() - np.cumsum(wc[o]) / wc.sum()).max()",
], "Fragment 8.2  Variance ratios and the Kolmogorov–Smirnov distance, for weighted samples. Full script: ch08/08_01_balance_table.py"],

["p", "Table 8.2 reports these diagnostics on the primary dataset for the unadjusted sample and for five of the adjusted samples of Chapters 5 to 7. For each diagnostic it gives the most unfavourable value across the covariates, since a balance assessment is only as good as its worst covariate."],

["tab", "8.2", "Diagnostics beyond the mean, primary dataset.",
  [3000, 1000, 1150, 1100, 1000, 1100, 1176],
  ["", "Largest SMD", "Variance ratios outside 0.8–1.25", "Most extreme variance ratio", "Largest KS", "Largest SMD, 164 terms", "Terms over 0.1"],
  [
    ["Unadjusted", "0.394", "1", "1.70", "0.172", "0.358", "16"],
    ["Propensity score matching", "0.022", "0", "0.97", "0.019", "0.061", "0"],
    ["Mahalanobis matching", "0.062", "0", "1.07", "0.029", "0.060", "0"],
    ["Odds weighting", "0.004", "0", "0.94", "0.015", "0.049", "0"],
    ["Subclassification, 5 strata", "0.091", "0", "1.16", "0.029", "0.164", "3"],
    ["Subclassification, 20 strata", "0.028", "0", "1.06", "0.013", "0.090", "0"],
  ],
  "Logistic score, eligible population, seed 20260808. Variance ratios and KS distances are computed on the eleven continuous and ordinal covariates; the 164 constructed terms are the squares of the non-binary covariates and all pairwise products, standardised as in Fragment 8.1. Mahalanobis matching uses the four covariates of Section 5.6 within a caliper of 0.1.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "Before adjustment the diagnostics agree that the groups differ: one variance ratio lies outside the conventional range (i.e., 1.70, for remoteness), the largest KS distance is 0.172, and 16 of the 164 constructed terms exceed 0.1. After any of the adjustments except five strata, every diagnostic passes. Under propensity score matching the variance ratios run from 0.97 to 1.03, the largest KS distance is 0.019, and no square or interaction exceeds 0.1, so the promise of Chapter 3 is kept: the interactions balance after matching, without having been included in the propensity model. Five strata leave three constructed terms above 0.1, which is consistent with the coarse grouping that Section 7.4 found costly, and twenty strata remove them."],

["p", "The diagnostics beyond the mean therefore add information where the mean-based diagnostic is already failing, as for five strata, but they do not separate the well-adjusted samples from one another. Propensity score matching and Mahalanobis matching, which Chapter 5 found to differ by fifteen points of bias, differ on every column of Table 8.2 by amounts too small to act on, and on the largest standardised difference the propensity score matched sample looks the better of the two. Section 8.6 returns to this comparison across six draws."],

["h2", "8.5  Variables outside the model"],

["p", "A useful check that is less often reported is balance on pre-programme variables that did not enter the propensity model. If the adjustment has made the groups comparable in general, rather than only on the covariates it was given, such variables should also be approximately balanced. The analysis file of Chapter 2 contains nine such variables, including occupation_group, the pure outcome predictor that Chapter 3 held back from the score, and mutual_obligation_status, the near-instrument of Section 3.7. Table 8.3 reports the largest standardised difference within each, before and after propensity score matching."],

["tab", "8.3", "Balance on variables the propensity model does not use.",
  [3600, 1400, 1600, 2426],
  ["Variable", "Before", "After matching", "Least balanced category"],
  [
    ["occupation_group", "0.038", "0.017", "Professionals"],
    ["english_proficiency", "0.082", "0.055", "Not well"],
    ["family_composition", "0.064", "0.054", "Other"],
    ["country_of_birth_group", "0.040", "0.029", "Other"],
    ["state", "0.029", "0.042", "TAS"],
    ["labour_force_status_2016", "0.286", "0.024", "Employed FT"],
    ["mutual_obligation_status", "0.690", "0.689", "Intensive"],
    ["pbs_scripts", "0.061", "0.021", ""],
    ["earnings_volatility", "0.164", "0.008", ""],
  ],
  "Logistic score, primary dataset, propensity score matching as in Table 8.1. For a categorical variable, the largest absolute standardised difference across its categories, with missing values treated as a category.",
  ["l", "r", "r", "l"]
],

["p", "Two results in the table are instructive, and in opposite directions. Labour force status in 2016 and earnings volatility, which were imbalanced before matching at 0.286 and 0.164, are balanced after it at 0.024 and 0.008, although neither entered the score: they are closely related to the earnings and payment histories that did enter it, and balancing those balanced them. Mutual obligation status, by contrast, is imbalanced at 0.690 before matching and 0.689 after, and it remains so after every adjustment in this chapter. It was left out of the score deliberately, because Section 3.7 showed that it predicts treatment strongly and the outcome hardly at all, and its imbalance is therefore harmless to the estimate. A variable outside the model that remains imbalanced is a reason to ask whether it affects the outcome, and imbalance matters in proportion to how strongly the variable predicts the untreated outcome, which is the point of Section 8.2 seen from the other side."],

["h2", "8.6  What the diagnostics cannot see"],

["p", "Sections 8.3 to 8.5 assessed balance on a single dataset, which is the position of every researcher with real data. PLIDA-SIM allows something that real data do not: the same assessment can be repeated on six draws, and each adjusted sample can be scored against the truth. Table 8.4 does so for the logistic score, reporting the mean across six draws of each diagnostic of Table 8.2 beside the bias of the estimate that each sample produces."],

["tab", "8.4", "Every diagnostic against the bias, logistic score, six draws.",
  [3000, 1500, 1000, 1000, 1000, 1000, 1026],
  ["", "Bias of the ATT", "Largest SMD", "Covariates over 0.05", "Variance ratios outside 0.8–1.25", "Largest KS", "Largest SMD, 164 terms"],
  [
    ["Unadjusted", "−149.3% (9.8)", "0.399", "15.0", "1.0", "0.181", "0.370"],
    ["Propensity score matching", "−14.4% (8.5)", "0.024", "0.0", "0.0", "0.021", "0.068"],
    ["Mahalanobis matching", "+0.7% (8.6)", "0.064", "1.5", "0.0", "0.023", "0.068"],
    ["Odds weighting", "−11.8% (5.4)", "0.005", "0.0", "0.0", "0.018", "0.060"],
    ["Subclassification, 2 strata", "−55.8% (8.1)", "0.203", "12.0", "1.0", "0.071", "0.217"],
    ["Subclassification, 5 strata", "−22.2% (6.2)", "0.096", "1.0", "0.0", "0.035", "0.155"],
    ["Subclassification, 20 strata", "−12.0% (5.5)", "0.026", "0.0", "0.0", "0.017", "0.074"],
    ["Subclassification, 100 strata", "−10.5% (5.4)", "0.009", "0.0", "0.0", "0.017", "0.059"],
  ],
  "Logistic score, untrimmed, ATT. Means across six draws, with the standard deviation of the bias across draws in parentheses. Bias is against the true ATT for the treated persons each sample describes. The biases reproduce Tables 5.2, 6.6 and 7.3.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "The diagnostics separate the badly adjusted samples from the rest: the unadjusted comparison and two strata fail every test, and five strata fail some. Among the remainder, however, they carry little information about the bias. Of the 42 adjusted samples on the logistic score, 30 pass every test in the table (i.e., no covariate and no constructed term above 0.1 and no variance ratio outside 0.8 to 1.25), and the biases of those 30 run from −23.6 to +12.3 per cent. A researcher who saw any of them would have had no reason, from the balance diagnostics, to prefer one over another."],

["p", "The comparison that Chapter 5 left open makes the point sharply. Table 8.5 reports, for each draw, the difference between propensity score matching and Mahalanobis matching on the bias and on each diagnostic; a negative entry in a diagnostic column means that propensity score matching appears better balanced."],

["tab", "8.5", "Propensity score matching less Mahalanobis matching, by draw.",
  [1700, 1400, 1400, 1400, 1500, 1626],
  ["Draw", "Bias (points)", "Largest SMD", "Largest KS", "Largest SMD, 164 terms", "Most extreme variance ratio"],
  [
    ["20260808", "−26.8", "−0.040", "−0.010", "+0.001", "−0.041"],
    ["20260809", "−7.6", "−0.042", "+0.006", "−0.012", "−0.023"],
    ["20260810", "−10.9", "−0.026", "−0.005", "−0.003", "+0.025"],
    ["20260811", "−18.9", "−0.044", "−0.003", "+0.018", "+0.030"],
    ["20260812", "−15.0", "−0.027", "+0.001", "+0.020", "+0.003"],
    ["20260813", "−11.4", "−0.058", "−0.001", "−0.023", "+0.012"],
  ],
  "Logistic score, untrimmed. Each entry is the value for propensity score matching less the value for Mahalanobis matching in the same draw. For the variance ratio the entry is the difference in the absolute log of the most extreme ratio, so that a negative entry again favours propensity score matching.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "Propensity score matching is the more biased of the two in every draw, by between 7.6 and 26.8 points. The largest standardised difference says the opposite in every draw, by between 0.026 and 0.058, because matching on the propensity score balances the means of the covariates very closely while Mahalanobis matching trades a little balance on the means for closer pairs on the covariates that matter most for earnings. The KS distance, the constructed terms and the variance ratios split both ways by amounts too small to act on. None of the diagnostics beyond the mean distinguishes the two samples, as Section 5.15 anticipated, and Section 8.8 describes a check that does."],

["p", "The explanation follows from Section 8.2. The bias is the imbalance in the untreated outcome, and each covariate diagnostic weighs every covariate, and every square and interaction, equally. A sample can therefore pass every diagnostic while carrying small imbalances that all push the untreated outcome in the same direction, and a second sample can show a slightly larger imbalance on a covariate that matters little for the outcome while matching closely on those that matter most. Balance on the covariates is a necessary condition for a credible estimate, and the diagnostics remain the right first check, but it is not a sufficient condition and the diagnostics cannot be used to choose among designs that satisfy it."],

["h2", "8.7  When the diagnostics do see a problem"],

["p", "The conventional diagnostics are not powerless, and the boosted score of Chapter 3 shows when they help. Chapter 3 fitted the propensity score by gradient boosting as well as by logistic regression, and argued that a flexible estimator should be selected on balance and overlap rather than on fit, and constrained rather than used raw. Section 7.1 deferred to this chapter what happens when a boosted score is used for stratification. Table 8.6 reports the bias and the largest standardised difference for each adjusted sample on the boosted score, with the number of draws in which the sample fails the 0.1 threshold and the stricter 0.05 threshold."],

["tab", "8.6", "The boosted score: bias against the balance tests, six draws.",
  [3400, 1500, 1300, 1400, 1426],
  ["", "Bias of the ATT", "Largest SMD", "Draws failing 0.1", "Draws failing 0.05"],
  [
    ["Propensity score matching", "+18.8%", "0.115", "6 of 6", "6 of 6"],
    ["Mahalanobis matching", "+9.3%", "0.138", "6 of 6", "6 of 6"],
    ["Odds weighting", "−12.6%", "0.026", "0 of 6", "0 of 6"],
    ["Subclassification, 2 strata", "−35.9%", "0.199", "6 of 6", "6 of 6"],
    ["Subclassification, 5 strata", "+2.0%", "0.061", "0 of 6", "5 of 6"],
    ["Subclassification, 20 strata", "+16.4%", "0.093", "1 of 6", "6 of 6"],
    ["Subclassification, 100 strata", "+20.0%", "0.125", "6 of 6", "6 of 6"],
  ],
  "Boosted score of Chapter 3, untrimmed, ATT. Means across six draws of the bias and of the largest absolute standardised difference across the eighteen covariates.",
  ["l", "r", "r", "r", "r"]
],

["p", "Here the diagnostics do their job. Both matched samples on the boosted score fail the 0.1 threshold in every draw, with remoteness the least balanced covariate most often, and both produce estimates that are too high (i.e., by +18.8 and +9.3 per cent). The stratified samples are more instructive still. As strata are added, balance deteriorates, with the largest standardised difference rising from 0.061 at five strata to 0.093 at twenty and 0.125 at a hundred, while the bias rises from +2.0 to +16.4 and +20.0 per cent. On the logistic score of Table 8.4, adding strata improved balance; on the boosted score it worsens it, which is the signature of a score that separates the treated from the controls more sharply than their covariates warrant, so that finer strata compare treated persons with increasingly unusual controls."],

["box", "Trap: a threshold is a convention, not a test", [
  "The threshold of 0.1 is widely treated as a line between balanced and unbalanced samples, and a sample that falls just below it is often reported as balanced without further comment. On the boosted score, twenty strata produce a largest standardised difference of between 0.083 and 0.104 across the six draws, and so pass the 0.1 threshold in five draws of six, while the estimate is biased by between +9.4 and +23.1 per cent.",
  "A stricter threshold is not a remedy on its own. At 0.05, every sample in Table 8.6 except odds weighting fails in at least five draws, including five strata, whose estimate is the least biased on the boosted score. What exposed the problem in Section 8.7 was not the level of any one diagnostic but its direction as the design was refined: balance that worsens as strata are added, or as a caliper is tightened, is a warning about the score itself. Researchers should therefore compare the balance of several candidate designs, and report the comparison, rather than certify a single design against a fixed number.",
]],

["h2", "8.8  A secondary check: balance on a prognostic score"],

["p", "If the balance that matters is balance on the untreated outcome, the natural diagnostic is balance on a prediction of it. A prognostic score is each person's predicted outcome without treatment, estimated from a model of the outcome fitted to the controls, whose observed outcome is their untreated outcome. The idea is due to Hansen, and Stuart, Lee and Leacy proposed the imbalance in a prognostic score as a balance diagnostic, showing in simulations that it tracks the bias of the estimate better than the conventional measures do. The imbalance in the prognostic score, in dollars, is a predicted bias, and it can be expressed as a percentage of the estimate in the same way as the actual bias."],

["frag", [
  "c = np.where(D == 0)[0]                        # controls only",
  "fold = rng.integers(0, 2, len(D))              # two folds",
  "prog = np.zeros(len(D))",
  "for f in (0, 1):",
  "    fit = HistGradientBoostingRegressor().fit(Q[c[fold[c] != f]], y[c[fold[c] != f]])",
  "    prog[fold == f] = fit.predict(Q[fold == f])",
  "predicted_bias = wt @ prog / wt.sum() - wc @ prog / wc.sum()",
], "Fragment 8.3  The prognostic score, cross-fitted on the controls. Full script: ch08/08_02_diagnostics_across_draws.py"],

["p", "The check is built with three safeguards. The model is fitted to the controls only, so that no treated person's outcome is used and the treatment effect cannot enter the prediction. It is cross-fitted, meaning that the controls are divided into two halves and each half's predictions come from a model fitted to the other half, so that no control's prediction comes from a model that has seen its own outcome. And it is computed only after the design has been settled and recorded, so that it serves to question a design rather than to tune one. The model is a gradient boosting regression on the covariates of Chapter 6's outcome model, which include occupation_group; a linear model can be used instead, and performs less well in these data, in part because earnings depend non-linearly on prior earnings."],

["tab", "8.7", "The secondary check: actual bias against the bias predicted by the prognostic score, six draws.",
  [3400, 1400, 1400, 1400, 1426],
  ["", "Logistic: actual", "Logistic: predicted", "Boosted: actual", "Boosted: predicted"],
  [
    ["Unadjusted", "−149.3%", "−132.7%", "−149.3%", "−132.7%"],
    ["Propensity score matching", "−14.4%", "−3.3%", "+18.8%", "+24.6%"],
    ["Mahalanobis matching", "+0.7%", "+7.0%", "+9.3%", "+15.9%"],
    ["Odds weighting", "−11.8%", "−4.2%", "−12.6%", "−3.7%"],
    ["Subclassification, 2 strata", "−55.8%", "−44.4%", "−35.9%", "−24.6%"],
    ["Subclassification, 5 strata", "−22.2%", "−13.4%", "+2.0%", "+10.2%"],
    ["Subclassification, 20 strata", "−12.0%", "−4.1%", "+16.4%", "+23.3%"],
    ["Subclassification, 100 strata", "−10.5%", "−3.0%", "+20.0%", "+26.5%"],
  ],
  "Untrimmed, ATT, means across six draws. Predicted is the imbalance in the prognostic score of Fragment 8.3 as a percentage of the true ATT; it uses the controls' outcomes only, and the truth file only to express it on the same scale as the actual bias.",
  ["l", "r", "r", "r", "r"]
],

["p", "Across the 84 adjusted samples of the two scores, the predicted bias correlates at 0.97 with the actual bias, against −0.27 for the largest standardised difference and −0.19 for the largest KS distance. Among the 51 samples that pass the 0.1 threshold, which are the ones a researcher would actually be choosing among, the correlation is 0.88, against 0.45 and 0.63. Most importantly, the check sees the difference that the conventional diagnostics missed in Table 8.5: it predicts propensity score matching to be more biased than Mahalanobis matching in every draw, by between 4.4 and 16.0 points and by 10.3 on average, against an actual difference of 15.1."],

["p", "Three cautions explain why the book presents the prognostic score as a secondary check rather than as the primary balance diagnostic. The first is that it departs from the principle of Section 5.2.1, since it uses the controls' outcomes; the safeguards above limit the departure, but a researcher who computed it repeatedly while adjusting a design would be tuning the design to the outcome, which is exactly what the principle exists to prevent. The second is that it is only as good as the outcome model, and its predictions depend on choices (e.g., the covariates and the form of the model) that the conventional diagnostics do not require. The third is that it is consistently displaced from the truth: in every row of Table 8.7 the predicted bias lies above the actual bias, so that it understates a negative bias and overstates a positive one, because the prognostic score can only reflect imbalance in what the observed covariates predict. The part of the bias that no observed covariate predicts is invisible to this check as it is to every other, and Chapter 10 examines it directly."],

["p", "Used within those limits, the check answers a question that the conventional diagnostics cannot. A design that passes the covariate diagnostics but shows a large imbalance in the prognostic score has left an imbalance on something that matters for the outcome, and it should be revisited; a design that passes both has been examined as closely as the observed data allow."],

["box", "In the DataLab: balance output and the output checker", [
  "A balance table is output like any other, and an output checker is likely to examine it as such. Means and standardised differences of binary covariates in small matched or stratified groups are effectively cell counts, and the usual minimum-cell rules may apply to them; for continuous covariates, the means of small groups can approach the values of individuals. Reporting balance for the whole adjusted sample, as Tables 8.1 to 8.3 do, rather than by stratum or by subgroup, generally avoids the difficulty.",
  "Distributional diagnostics need more care. A KS distance is a single number and raises no difficulty, but a plot of the two cumulative distributions discloses the extremes of each covariate in each group, and it is likely to be treated as a release of those values; the statistic should be reported and the plot kept inside the environment. The prognostic score check requires an outcome model, which is an analytical output in its own right, and it is worth confirming at the approval stage that the project's outputs may include balance on a predicted outcome as well as on the covariates.",
]],

["h2", "8.9  Is this dataset balanced?"],
["h3", "8.9.1  What to record about a balance assessment"],

["p", "Six things should be recorded about the balance of any adjusted dataset before its estimate is carried into Chapter 9 for variance estimation."],

["list", [
  "The standardised difference of every covariate of the propensity model before and after adjustment, with the denominator stated.",
  "The variance ratios of the continuous covariates, the largest KS distance, and the largest standardised difference among the squares and interactions.",
  "Balance on pre-programme variables outside the model, with an explanation for any that remain imbalanced.",
  "The balance of at least one alternative design (e.g., a different number of strata or a different distance), so that a reader can see whether balance moved as the design changed.",
  "The threshold used, stated as a convention rather than a test, and no significance tests of balance.",
  "If the prognostic score check is reported, the outcome model, the fact that it was fitted to controls only and cross-fitted, and the point in the analysis at which it was computed.",
]],
["h3", "8.9.2  What this chapter found"],

["p", "The conventional diagnostics did what they are designed to do. They separated the unadjusted comparison and the coarsest stratifications from the rest, they showed that the interactions balance after matching as Chapter 3 anticipated, and on the boosted score they failed the matched samples in every draw and showed balance worsening as strata were added. What they could not do was rank the designs that passed them: 30 samples on the logistic score passed every test with biases from −23.6 to +12.3 per cent, and in the comparison between propensity score and Mahalanobis matching the most widely reported diagnostic pointed the wrong way in all six draws. Balance on a prognostic score, used as a secondary check, tracked the bias closely and pointed the right way in every draw, but it too was displaced from the actual bias, for reasons that belong to Chapter 10."],

["h3", "8.9.3  Recommendations"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, we would report a full balance table with fixed denominators for every adjusted dataset, together with the diagnostics beyond the mean and balance on the variables outside the model, and we would compare the balance of more than one candidate design rather than certify a single design against 0.1. We would compute the prognostic score check once, after the design had been settled, and report it beside the covariate diagnostics as a secondary check. We would not choose between two designs that both pass the conventional diagnostics on the basis of those diagnostics, since Table 8.5 shows that they can point the wrong way."],

["p", "The recommendation most worth carrying to other data is the one that follows from Section 8.2. Balance matters because of the outcome, and a covariate matters in proportion to how strongly it predicts the outcome without treatment. A researcher who knows which covariates those are, from the substantive knowledge that Chapter 2 drew on, should hold them to a stricter standard than the rest, and should read a passing balance table as evidence that the adjustment has not failed, rather than as evidence that it has succeeded."],

["h3", "8.9.4  Scripts for this chapter"],

["tab", "8.8", "Scripts for Chapter 8. All available from the companion website.",
  [1100, 3600, 3000, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["8.1", "ch08/08_01_balance_table.py", "Tables 8.1 to 8.3", "10 s"],
    ["8.2", "ch08/08_02_diagnostics_across_draws.py", "Tables 8.4 to 8.7; the identity of Section 8.2", "5 min"],
  ],
  "Script 8.2 generates its own draws, the six of Chapters 5 to 7, and ignores --datadir for that reason. Script 8.1 uses causalml for Table 8.1; the other tables use the functions of Fragments 8.1 and 8.2.",
  ["l", "l", "l", "r"]
],
["h3", "8.9.5  Further reading"],

["p", "Austin's work on balance diagnostics for matched samples, and Austin and Stuart's for weighted samples, set out the standardised difference, variance ratios and distributional comparisons with worked examples, and are the natural companions to Sections 8.3 and 8.4. Stuart's review of matching methods discusses the choice of denominator and argues, with Imai, King and Stuart, against significance tests of balance, whose dependence on the sample size they call the balance test fallacy."],

["p", "On the limits of balance on the means, readers should return to Basu, Polsky and Manning, whose simulations with a skewed outcome motivated Section 8.4. Hansen introduced the prognostic score as an analogue of the propensity score on the outcome side, and Stuart, Lee and Leacy developed prognostic score balance as a diagnostic and compared it with the conventional measures; their paper is the basis of Section 8.8 and discusses the tension with the principle of outcome-blind design at greater length than this chapter can."],

["h3", "8.9.6  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Build Table 8.1 on PLIDA-SIM B for the propensity score matched sample and for the odds weighted sample. For the weighted sample, explain why create_table_one cannot be used directly and compute the standardised differences with Fragment 8.1.",
  "Compute the diagnostics of Table 8.2 on PLIDA-SIM B for five and twenty strata. At which number of strata do all 164 constructed terms first fall below 0.1?",
  "Report balance on mutual_obligation_status after each adjustment. Explain, without using the truth file, how a researcher could establish that its imbalance is harmless.",
  "Stratify on the boosted score of Chapter 3 with 5, 20 and 100 strata, and report the largest standardised difference at each. Does balance improve or worsen as strata are added, and what does that suggest about the score?",
  "Compute the prognostic score check of Fragment 8.3 for propensity score matching and Mahalanobis matching on PLIDA-SIM B, once with a linear model and once with gradient boosting. Which of the two designs does each prefer?",
]],
["h3", "8.9.7  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Why is the bias of an ATT estimate equal to the imbalance in the untreated outcome between the adjusted groups, and why can that imbalance never be checked directly?",
  "Why is a significance test an unsuitable measure of balance, and why is the standardised difference preferred?",
  "Two matched samples pass every covariate diagnostic, and the one with the smaller standardised differences produces the more biased estimate. How can that happen?",
  "A pre-programme variable remains badly imbalanced after every adjustment. Under what circumstances is that harmless, and how would a researcher find out?",
  "On the boosted score, balance worsened as strata were added. What does that indicate about the score, and why would a fixed threshold have missed it in most draws?",
  "The prognostic score check uses the controls' outcomes. What principle does that strain, what safeguards limit the strain, and why does the check still fail to predict the whole of the bias?",
]],

];
