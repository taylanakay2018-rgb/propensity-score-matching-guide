// Chapter 9 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "9  Causal Effect Estimation and Correct Variance"],

["h2", "9.1  Purpose and scope of this chapter"],

["p", "Chapter 2 set the 2019 earnings aside and asked that they not be examined until this chapter, so that every decision about the design (i.e., the propensity score, the trimming rule, the matching, weighting or stratification, and the balance assessment) could be made without knowing what it would do to the estimate. Chapters 3 to 8 did use the outcome, but only to score each design against the truth, which is a luxury of a simulated dataset. This chapter takes the step that a researcher with real data takes once the design is settled: it estimates the effect of the programme on the primary dataset, reports it in dollars with a standard error and a confidence interval, and asks whether that standard error and that interval can be trusted."],

["p", "The chapter's central argument is that a standard error must reflect how the estimate was built. Every estimate in Chapters 5 to 7 was reported with a naive standard error, computed as though the propensity score were known rather than estimated, as though matched pairs were unrelated to one another, and as though the design had not been chosen with the data in hand. Using 200 independent draws of PLIDA-SIM, the chapter measures how far each naive standard error is from the actual spread of the estimates, and it shows which of the available alternatives (i.e., sandwich estimators that include the propensity model, the bootstrap, paired and matching-specific formulas) are right in these data. It then asks what a correct 95 per cent interval actually promises, and the answer is less than most readers of an evaluation report assume."],

["p", "By the end of the chapter, readers should be able to compute a standard error that accounts for the estimated propensity score, by a sandwich estimator or by the bootstrap; to choose a standard error for a matched sample; to recognise the default output of a weighted regression as unreliable; and to compare two designs by the standard error of their difference rather than by their separate intervals. They should also be able to say what a confidence interval measures and what it does not."],

["p", "Three scoping notes. The first is that the chapter works on the logistic score of Chapter 3 and the untrimmed eligible population, as Chapter 8 did, so that the estimators are those whose bias Chapters 5 to 7 reported. The second is that the 200 draws include the six used since Chapter 5, and the chapter reports what the larger number of draws says about the book's own six-draw results. The third is that, where an interval fails to contain the truth, this chapter measures the failure but leaves its cause to Chapter 10."],

["h2", "9.2  The estimates on the primary dataset"],

["p", "Table 9.1 reports the principal estimators of Chapters 5 to 7 on the primary dataset, in 2019 dollars. The outcome is annual earnings in 2019, which is also the base year of the price indices that Chapter 2 used to deflate the earlier years, so the estimates need no further adjustment; a report should nonetheless state the base year, since a reader cannot otherwise tell whether a figure of $5,601 is in the prices of 2019 or of the year the report was written. For each estimate the table gives the standard error that the earlier chapters quoted, the standard error that Section 9.9 recommends, and the 95 per cent interval built from the latter."],

["tab", "9.1", "The estimates on the primary dataset, 2019 dollars.",
  [3300, 1150, 1150, 1100, 1300, 2026],
  ["", "Estimate", "SE as quoted", "SE", "Method", "95% interval"],
  [
    ["ATT: odds weighting", "$5,601", "$366", "$241", "sandwich", "$5,129 to $6,072"],
    ["ATT: doubly robust", "$5,551", "$263", "$254", "bootstrap", "$5,053 to $6,049"],
    ["ATT: subclassification, 20 strata", "$5,627", "$320", "$237", "bootstrap", "$5,163 to $6,090"],
    ["ATT: 20 strata, regression within strata", "$5,728", "", "$225", "bootstrap", "$5,288 to $6,168"],
    ["ATT: PS matching, 1:1", "$4,921", "$443", "$443", "paired", "$4,052 to $5,790"],
    ["ATT: PS matching, with replacement", "$4,933", "$443", "$463", "Abadie–Imbens", "$4,026 to $5,841"],
    ["ATT: Mahalanobis matching, 1:1", "$6,640", "$337", "$337", "paired", "$5,979 to $7,301"],
    ["ATT: Mahalanobis matching, 1:3", "$6,193", "$285", "$285", "paired", "$5,633 to $6,752"],
    ["ATE: normalised IPW", "$4,285", "$606", "$494", "sandwich", "$3,317 to $5,253"],
    ["ATE: doubly robust", "$4,584", "$414", "$393", "bootstrap", "$3,814 to $5,355"],
  ],
  "Logistic score, eligible population, seed 20260808: 4,867 treated persons and 37,708 controls. SE as quoted is the naive standard error of Chapters 5 to 7 (the influence function with the score treated as known, the within-stratum formula, or the paired formula). The bootstrap uses 200 replicates, refitting the score in each. PS matching is propensity score matching. The interval is the estimate plus or minus 1.96 standard errors.",
  ["l", "r", "r", "r", "l", "r"]
],

["p", "Three features of the table deserve comment before the standard errors are examined. The first is that the estimates of the ATT range from $4,921 to $6,640, a spread of more than $1,700 between designs applied to the same data, which is far larger than any of the standard errors. The choice of design therefore matters more to the answer than sampling variability does, which is the conclusion Chapters 5 to 7 reached from the other direction. The second is that, for odds weighting and subclassification, the recommended standard errors are between a quarter and a third smaller than those quoted in Chapters 6 and 7, and for the normalised ATE about a fifth smaller, so that the intervals are correspondingly narrower. The third is that the intervals of the different designs do not all overlap: the propensity score matched interval ends at $5,790 and the Mahalanobis matched interval begins at $5,979. At most one of them can contain the truth, and Section 9.8 reports which."],

["h2", "9.3  What a standard error has to account for"],

["p", "A standard error estimates how much an estimate would vary if the whole analysis were repeated on a fresh sample from the same population. The word whole is the important one. Each estimate in Table 9.1 was produced by a procedure (i.e., a propensity model was fitted, controls were selected or weighted by it, and a difference was computed), and each step of that procedure would come out differently on a fresh sample. A standard error that accounts for only the last step will generally be wrong, although, as this section shows, not always in the direction that intuition suggests."],

["h3", "9.3.1  The estimated propensity score"],

["p", "The naive standard errors of Chapters 6 and 7 treat the propensity score as fixed. It is not: it was estimated from the same data, and a different sample would have produced different scores and therefore different weights. The standard remedy is to recognise that the logistic regression and the weighted comparison are solved together, as one set of estimating equations, and to compute a sandwich standard error for the whole set. Fragment 9.1 shows the calculation for odds weighting; it adds the logistic regression's equations to those of the two weighted means, and the resulting standard error carries the uncertainty in the score into the uncertainty in the estimate."],

["frag", [
  "def psi(theta):                                    # one row per person",
  "    b, m1, m0 = theta[:p], theta[p], theta[p + 1]",
  "    e = expit(Zi @ b)",
  "    return np.c_[Zi * (D - e)[:, None],             # the logistic regression",
  "                 D * (y - m1),                       # the treated mean",
  "                 (1 - D) * e / (1 - e) * (y - m0)]   # the odds-weighted control mean",
  "",
  "A = jacobian(lambda t: psi(t).mean(0), theta)      # the 'bread'",
  "V = inv(A) @ (psi(theta).T @ psi(theta) / n) @ inv(A).T / n",
], "Fragment 9.1  A sandwich standard error with the propensity model stacked in. Full script: ch09/09_01_estimate_primary.py"],

["p", "On the primary dataset the correction is large. The naive standard error of odds weighting is $366, and the sandwich standard error is $241, a third smaller; for the normalised ATE the figures are $606 and $494. The direction is the one that theory predicts for weighting estimators: an estimated score adapts to the particular sample, removing some of the chance imbalance between the groups that a known score would leave, so that the estimate varies less than a standard error that ignores the estimation assumes. It is worth noting that the correction makes the interval narrower rather than wider, which runs against the common expectation that accounting for an additional source of uncertainty must increase the standard error."],

["h3", "9.3.2  The bootstrap"],

["p", "The sandwich estimator requires the estimating equations to be written down, which is practical for weighting but not for subclassification, matching or the doubly robust estimator, whose procedures include steps that are not smooth functions of the data. The bootstrap avoids the difficulty by repeating the whole procedure on resamples of the data: persons are drawn with replacement from the analysis file to form a sample of the same size, the propensity score is refitted, the design is rebuilt and the estimate recomputed, and the standard deviation of the estimates across a few hundred resamples is the bootstrap standard error. Fragment 9.2 shows the loop."],

["frag", [
  "reps = []",
  "for b in range(200):",
  "    i = rng.integers(0, n, n)                        # resample persons",
  "    ps_b = fit_propensity(X.iloc[i], D[i])           # refit the score",
  "    reps.append(estimator(ps_b, D[i], y[i]))         # rebuild the design",
  "se = np.std(reps, ddof=1)",
], "Fragment 9.2  The bootstrap: resample persons and repeat everything. Full script: ch09/09_01_estimate_primary.py"],

["p", "The essential point is that everything the analyst did must be inside the loop. A bootstrap that resamples the matched pairs, or reuses the original weights, reproduces only the last step and inherits the naive standard error's errors. On the primary dataset the full bootstrap gives $240 for odds weighting, in close agreement with the sandwich estimator's $241, and $475 for the normalised ATE against $494. Its cost is computational: 200 replicates of the estimators in Table 9.1 take a few minutes here, and considerably longer in an environment such as the DataLab."],

["h3", "9.3.3  Matched pairs and reused controls"],

["p", "Matching raises two further questions. The first is whether the matched sample should be analysed as pairs. Holmes describes matched pairs as dependent samples, whose differences typically vary less than two independent groups would, and the paired standard error, computed from the within-pair differences, reflects that. On the primary dataset the paired standard error of one-to-one propensity score matching is $443, against $507 if the treated and matched controls are treated as unrelated groups. The second question arises when controls are reused: a control matched to four treated persons contributes one outcome to four differences, and those differences are not independent. Abadie and Imbens derived a standard error that adds a term for each reused control, and on the primary dataset it is $463, against a paired standard error of $443 for the same sample."],

["p", "The reuse correction is small here because reuse is modest: of 4,864 pairs formed with replacement on the primary dataset, 4,290 distinct controls appear, and no control appears more than four times. In data with fewer suitable controls, and therefore heavier reuse, the correction would matter more, and Section 5.10's advice to report the number of distinct controls alongside the number of pairs is what allows a reader to judge which case applies."],

["h2", "9.4  How good are the standard errors?"],

["p", "A standard error is right if it matches the actual variability of the estimate across repeated samples, which a real analysis cannot observe and a simulation can. Chapter 6 attempted the comparison with six draws (Table 6.8) and noted that six draws estimate a standard deviation only roughly. This section repeats it with 200 draws, which estimate a standard deviation to within about five per cent; the bootstrap, which is far more expensive, was run on the first 40 draws and is compared with the spread across those 40. Table 9.2 reports each standard error as a ratio to the actual spread, so that 1.00 is correct, a ratio above one overstates the uncertainty, and a ratio below one understates it."],

["tab", "9.2", "Standard error over the actual spread of the estimates, 200 draws.",
  [2900, 900, 850, 850, 850, 850, 850, 950, 1026],
  ["", "Actual spread", "Score known", "Sandwich", "Bootstrap", "Paired", "Unpaired", "Abadie–Imbens", "Weighted regression, robust"],
  [
    ["ATT: odds weighting", "$238", "1.54", "1.02", "0.97", "", "", "", "1.54"],
    ["ATT: doubly robust", "$247", "1.08", "", "0.98", "", "", "", ""],
    ["ATT: subclassification, 20 strata", "$248", "1.31", "", "0.99", "", "", "", ""],
    ["ATT: 20 strata, regression within strata", "$232", "", "", "0.91", "", "", "", ""],
    ["ATT: PS matching, 1:1", "$356", "", "", "1.08", "1.24", "1.42", "", ""],
    ["ATT: PS matching, with replacement", "$387", "", "", "1.39", "1.13", "", "1.18", "1.36"],
    ["ATT: Mahalanobis matching, 1:1", "$345", "", "", "", "0.99", "", "", ""],
    ["ATT: Mahalanobis matching, 1:3", "$259", "", "", "", "1.12", "", "", ""],
    ["ATE: normalised IPW", "$516", "1.20", "0.98", "1.04", "", "", "", "1.20"],
    ["ATE: doubly robust", "$456", "0.93", "", "0.95", "", "", "", ""],
  ],
  "Logistic score, untrimmed, 200 draws. Actual spread is the standard deviation across draws of the estimate less the truth for the persons it describes. Each entry is the mean standard error across draws over the actual spread; bootstrap entries use the first 40 draws and the spread across those 40. Score known is the influence-function standard error of Chapters 6 and 7, or the within-stratum formula for subclassification.",
  ["l", "r", "r", "r", "r", "r", "r", "r", "r"]
],

["p", "For the weighting estimators the message is clear. The standard error with the score treated as known overstates the spread by 54 per cent for odds weighting and by 20 per cent for the normalised ATE, and the robust standard error from a weighted regression is identical to it, because it too treats the weights as fixed. The sandwich estimator with the propensity model stacked in is right to within two per cent for both, and the bootstrap to within five. Subclassification's within-stratum formula overstates by 31 per cent, for the same reason, and the bootstrap is right. The doubly robust estimators' naive standard errors are close, at 1.08 and 0.93, because the outcome model absorbs much of the variation that the weights would otherwise carry, so that the estimate depends less on the score, and the bootstrap is right for both. This corrects the reading of Table 6.8, whose six draws suggested that the doubly robust ATT's naive standard error was a quarter too small; its spread across those six draws was, by chance, unusually large."],

["p", "For matching the picture is less tidy. The paired standard error of Mahalanobis matching is right (0.99). For propensity score matching, every conventional standard error overstates the spread: the paired standard error by 24 per cent, the unpaired by 42 per cent, and, under replacement, the Abadie–Imbens standard error by 18 per cent. The likeliest explanation is the one that applies to weighting, since matching on an estimated score also adapts to the sample, and Abadie and Imbens have shown that, for the ATT, the adjustment for an estimated score can go in either direction, so that a standard error that ignores the estimation may be too large, as it is here, or too small. The full bootstrap comes closest for one-to-one matching, at 1.08, but it has no theoretical guarantee for matching, and under replacement it overstates by 39 per cent. The practical position is therefore that, for propensity score matching, the paired standard error is conservative, which is the safe direction for an error to take, and that ignoring the pairing is the worst choice available."],

["p", "Two points from Chapter 5 need revising in the light of the table. Section 5.10 counted the reuse of controls so that this chapter would have something to work with, and the answer is that, in these data, reuse is not what makes the naive standard error wrong: the Abadie–Imbens correction adds only four per cent to the paired standard error, and both overstate the spread. And the matched-set bootstrap, which resamples treated persons together with their matched controls, reproduces the paired standard error almost exactly (1.23 for one-to-one matching and 1.14 under replacement), because it too holds the matched sample fixed and so cannot see how the sample would have been built differently."],

["box", "Trap: the default standard error of a weighted regression", [
  "A common way to compute a weighted estimate is to regress the outcome on the treatment indicator by weighted least squares, and to report the standard error that the software prints. The default in most regression software treats the weights as measures of precision, as they would be if each observation were an average of several, rather than as the sampling or balancing weights they are here. The resulting standard error can be wrong in either direction. For the normalised ATE it is 0.58 of the actual spread, so that a researcher would report an interval barely more than half as wide as it should be; for odds weighting it happens to be almost right, at 1.01, by coincidence rather than design.",
  "Software that treats the weights as frequencies (i.e., as the number of persons each observation represents) does worse still, at 0.41 for the ATE and 2.12 for the ATT. The robust (sandwich) option avoids these errors but, as Table 9.2 shows, still ignores the estimation of the score. The safe course is never to report the default standard error of a weighted regression, and to use the sandwich estimator of Fragment 9.1 or the bootstrap of Fragment 9.2 instead.",
]],

["fig", "9.1", "Standard errors against the actual spread, and what the resulting intervals cover. (a) The standard error quoted in Chapters 5 to 7 (open circles) and the one recommended in Section 9.9 (squares), each over the actual spread across 200 draws; 1.0 is correct, and for PS matching and Mahalanobis matching the two coincide. (b) The error of odds weighting in the first 40 draws, as a percentage of the true ATT, with its 95 per cent interval from the sandwich standard error; intervals that contain the truth are drawn in black. Produced by Script 9.2.",
  "figure_9_1_standard_errors.tif"],

["h2", "9.5  What a 95 per cent interval covers"],

["p", "A 95 per cent confidence interval is usually read as a range that contains the true effect with 95 per cent probability, or, more precisely, as the output of a procedure that captures the truth in 95 per cent of repeated samples. The second reading can be tested directly. Table 9.3 reports, for each estimator with its recommended standard error, how often the interval contains the true effect across the 200 draws, and how often it contains the estimator's own long-run average, which is what the interval would cover if the estimator were unbiased."],

["tab", "9.3", "What a 95 per cent interval covers, 200 draws.",
  [3500, 1300, 1000, 1000, 1150, 1076],
  ["", "Standard error", "Bias", "Bias in standard errors", "Contains the truth", "Contains the estimator's mean"],
  [
    ["ATT: odds weighting", "sandwich", "−10.9%", "−2.9", "18%", "96%"],
    ["ATT: doubly robust", "bootstrap", "−12.5%", "−3.1", "8%", "92%"],
    ["ATT: subclassification, 20 strata", "bootstrap", "−11.9%", "−3.1", "12%", "92%"],
    ["ATT: 20 strata, regression within strata", "bootstrap", "−8.3%", "−2.3", "40%", "92%"],
    ["ATT: PS matching, 1:1", "paired", "−9.9%", "−1.4", "74%", "97%"],
    ["ATT: PS matching, with replacement", "Abadie–Imbens", "−9.8%", "−1.4", "76%", "98%"],
    ["ATT: Mahalanobis matching, 1:1", "paired", "−1.3%", "−0.2", "94%", "96%"],
    ["ATT: Mahalanobis matching, 1:3", "paired", "−3.3%", "−0.7", "91%", "97%"],
    ["ATE: normalised IPW", "sandwich", "−22.6%", "−2.4", "32%", "94%"],
    ["ATE: doubly robust", "bootstrap", "−17.6%", "−2.2", "40%", "92%"],
    ["ATT: odds weighting, score known", "score known", "−10.9%", "−1.9", "54%", "100%"],
  ],
  "Logistic score, untrimmed. Rows using the bootstrap cover the first 40 draws, the rest all 200. Bias is the mean error as a percentage of the true effect; bias in standard errors is the mean error over the mean standard error. The last row repeats odds weighting with the naive standard error of Chapter 6.",
  ["l", "l", "r", "r", "r", "r"]
],

["p", "The last column shows that the standard errors are doing their job: around each estimator's own average, the intervals cover 92 to 98 per cent of the time, close to the promised 95. The fifth column shows that this is not the promise a reader of an evaluation report assumes. With a correct standard error, the interval for odds weighting contains the true ATT in only 18 per cent of draws, and the intervals for the doubly robust estimator and for twenty strata in 8 and 12 per cent. Panel (b) of Figure 9.1 shows why: the estimates cluster about eleven per cent below the truth, and an interval three standard errors wide on each side of an estimate that is nearly three standard errors too low will seldom reach it."],

["p", "Two features of the table are counterintuitive and worth stating plainly. The first is that the correct standard error makes coverage worse, not better: odds weighting with the naive standard error, which is 54 per cent too large, covers the truth 54 per cent of the time, against 18 per cent with the correct one. An inflated standard error can partly compensate for a bias, but only by accident, and it cannot be relied on to do so. The second is that the estimators with the smallest bias, the two Mahalanobis designs, are the only ones whose intervals cover the truth at close to the nominal rate, and they do so because their bias is small rather than because their standard errors are different in kind."],

["p", "A confidence interval therefore measures sampling error, and it measures it well when the standard error is chosen correctly, but it contains no allowance for bias. The bias of the propensity score estimators in these data is larger than their sampling error, and a correct interval around a biased estimate expresses a precision that the estimate does not have. The cause of that bias, and what a researcher can do about it, is the subject of Chapter 10."],

["h2", "9.6  How precise are this book's own results?"],

["p", "Every simulation result has a sampling error of its own. The means and standard deviations quoted in Chapters 5 to 8 are six-draw figures, and Chapter 6 cautioned that six draws estimate a standard deviation only roughly. Because the 200 draws of this chapter include those six as the first six, the book can now measure how representative they were. Table 9.4 compares the six-draw figures with those from all 200, and ranks the mean bias of the first six draws among 33 disjoint blocks of six."],

["tab", "9.4", "The book's six draws against 200.",
  [3600, 1150, 850, 1150, 850, 1426],
  ["", "Six draws: mean bias", "sd", "200 draws: mean bias", "sd", "Rank of the six among 33 blocks"],
  [
    ["Odds weighting", "−11.8%", "5.4", "−10.9%", "3.7", "9"],
    ["Doubly robust", "−12.6%", "5.8", "−12.1%", "3.8", "15"],
    ["Subclassification, 20 strata", "−12.0%", "5.5", "−11.6%", "3.9", "16"],
    ["20 strata, regression within strata", "−9.0%", "6.0", "−8.3%", "3.6", "9"],
    ["PS matching, 1:1", "−14.4%", "8.5", "−9.9%", "5.5", "2"],
    ["Mahalanobis matching, 1:1", "+0.7%", "8.6", "−1.3%", "5.4", "29"],
    ["Mahalanobis matching, 1:3", "−3.4%", "7.6", "−3.3%", "4.1", "14"],
    ["Normalised IPW (ATE)", "−22.7%", "9.6", "−22.6%", "9.6", "19"],
  ],
  "Logistic score, untrimmed, ATT except the last row. Bias is the mean error as a percentage of the true effect, and sd its standard deviation across draws. The rank orders the first six draws' mean bias from most negative (1) to least negative (33) among the 33 disjoint blocks of six draws within the first 198.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "For weighting, stratification and the doubly robust estimator, the six draws were representative: their mean biases lie within a point of the 200-draw values, and their ranks fall in the middle of the 33 blocks. For matching they were not. By chance, the six draws were among the least favourable blocks for propensity score matching (second of 33) and among the most favourable for Mahalanobis matching (29th of 33), so that the gap between the two, fifteen points across the six draws, is 8.6 points across 200. The conclusions of Chapters 5 and 8 are unaffected in direction, since propensity score matching is the more biased of the two in 91 per cent of the 200 draws, but the magnitudes quoted there are six-draw means and should be read with that in mind."],

["p", "The table also shows that six draws overstate the draw-to-draw standard deviation in these data by about half (e.g., 5.4 against 3.7 points for odds weighting), which is the same chance excess that made Table 6.8 misleading. The 200-draw means have standard errors of their own, of about 0.3 points for the weighting estimators and 0.4 for matching, so that differences of a point or more between estimators at 200 draws are reliable in a way that the six-draw differences were not."],

["h2", "9.7  Comparing two designs"],

["p", "Chapter 2 found that removing a covariate from the propensity model moved the matched estimate by an average of seven percentage points across five draws, and noted that the spread of that change was too wide for any single draw to establish it. The difficulty is general: researchers often compare two designs by inspecting whether their confidence intervals overlap, and that comparison is far too conservative when the two estimates come from the same data. Estimates from the same data share most of their sampling error, so the difference between them varies much less than either does, and the relevant standard error is that of the difference. On the primary dataset the doubly robust and odds-weighted estimates differ by $50, and the bootstrap standard error of that difference is $59, against $350 if the two estimates were treated as independent; their bootstrap replicates correlate at 0.97."],

["frag", [
  "diff = reps[\"dr_att\"] - reps[\"odds\"]          # the same bootstrap resamples",
  "se_diff = np.std(diff, ddof=1)                   # not sqrt(se_a**2 + se_b**2)",
], "Fragment 9.3  The standard error of a difference between two designs. Full script: ch09/09_01_estimate_primary.py"],

["p", "Table 9.5 makes the comparison across the 200 draws for five pairs of designs. For each it reports the mean difference, the standard deviation of the difference across draws, the standard deviation of each design on its own, the share of draws in which the difference has the same sign as its mean, and the standard error that the comparison would have if the two designs were independent."],

["tab", "9.5", "Comparing two designs on the same draws, 200 draws.",
  [4000, 900, 900, 900, 900, 1426],
  ["", "Mean difference", "sd of difference", "sd of each", "Same sign", "SE if independent"],
  [
    ["PS matching less Mahalanobis matching, 1:1", "−8.6", "6.3", "5.4", "91%", "7.7"],
    ["Mahalanobis 1:3 less Mahalanobis 1:1", "−2.0", "3.2", "4.7", "75%", "6.7"],
    ["20 strata with regression less without", "+3.3", "1.6", "3.7", "99%", "5.3"],
    ["Doubly robust less odds weighting", "−1.3", "1.0", "3.8", "90%", "5.3"],
    ["PS matching with replacement less without", "+0.1", "2.0", "5.8", "53%", "8.2"],
  ],
  "Logistic score, untrimmed, ATT. All figures are in percentage points of the true ATT. Sd of each is the mean of the two designs' standard deviations; the last column is the standard deviation their difference would have if they were independent.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "The regression within twenty strata improves on plain subclassification by 3.3 points, with a standard deviation of only 1.6, and in 99 per cent of draws; judged by the designs' separate spreads, which are more than twice as large, the improvement would have looked like noise. The doubly robust estimate differs from odds weighting by 1.3 points with a standard deviation of 1.0, so that even a difference of little more than a point is detectable when the comparison is paired. By contrast, matching with and without replacement differ by 0.1 points on average, with the sign split evenly across draws, which is what Chapter 5 concluded about the choice."],

["p", "The second row settles a question that Chapter 5 left open. Section 5.16.3 recommended Mahalanobis matching with three controls for each treated person, combining two findings that Chapter 5 measured separately. Measured as a whole, the third control reduces the draw-to-draw standard deviation from 5.4 to 4.1 points and costs about two points of bias (−3.3 against −1.3 per cent), so that the root mean squared error is slightly smaller for one-to-three (5.2 against 5.5). The choice is therefore a trade between bias and precision rather than an improvement on both, and Section 5.16.3 states it as such."],

["box", "In the DataLab: bootstrapping inside a secure environment", [
  "The bootstrap is the most computationally demanding step in this book, and secure environments are usually provisioned for interactive analysis rather than for repeated model fitting. Two hundred replicates of the estimators in Table 9.1 take a few minutes on an ordinary computer and may take much longer on a shared virtual machine, and matching estimators, which are the slowest to rebuild, are the ones for which the full bootstrap is least essential in these data. It is worth estimating the time of one replicate before committing to several hundred, and setting the random seed so that the replicates can be reproduced when an output checker or a reviewer asks.",
  "The replicates themselves are intermediate results and should not be released; the standard error, which is a single number derived from them, raises no disclosure difficulty. The same applies to the sandwich estimator, whose matrices contain nothing that identifies a person but which there is equally no reason to export.",
]],

["h2", "9.8  Scoring the estimates"],

["p", "The true ATT on the primary dataset is $6,408, and the true effect for the treated persons that each matching design retains differs from it by no more than $33. Of the eight intervals for the ATT in Table 9.1, two contain it: those of Mahalanobis matching one-to-one ($5,979 to $7,301) and one-to-three ($5,633 to $6,752). The intervals of odds weighting, the doubly robust estimator, both subclassification estimators and both propensity score matching designs lie wholly below the truth. The true ATE is $5,412, and neither interval for the ATE contains it."],

["p", "The primary dataset is a single draw, and Table 9.3 shows that its pattern is typical: the Mahalanobis intervals cover the truth in more than nine draws of ten and the others in far fewer. A researcher with real data would not know which case applied. What a researcher can know, and should report, is that the interval measures sampling error alone, and that the estimates of different defensible designs differ by more than their standard errors; the second fact is the more informative about how far the estimate can be trusted."],

["h2", "9.9  Is this estimate ready to report?"],
["h3", "9.9.1  What to record about an estimate"],

["p", "Six things should be recorded about any propensity score estimate before it is reported."],

["list", [
  "The estimand, ATE or ATT, and the population it describes, including any trimming.",
  "The estimate in dollars of a stated base year, and its standard error with the method named.",
  "For weighting and stratification, whether the standard error accounts for the estimation of the propensity score, and how.",
  "For matching, whether the standard error is paired, and the number of distinct controls against the number of pairs.",
  "For a bootstrap, the number of replicates, the random seed, and confirmation that the propensity score was refitted in each replicate.",
  "The estimates of at least one alternative defensible design, with the standard error of the difference.",
]],
["h3", "9.9.2  What this chapter found"],

["p", "The naive standard errors of Chapters 5 to 7 were wrong, but not in the direction usually feared: for weighting, stratification and propensity score matching they overstated the variability, by between 20 and 54 per cent, chiefly because they ignored the estimation of the score. A sandwich estimator with the propensity model stacked in, or a bootstrap that refits the score, was right to within a few per cent for weighting and stratification; the paired standard error was right for Mahalanobis matching and conservative for propensity score matching; and the default standard error of a weighted regression was unreliable in either direction. With the standard errors corrected, the intervals covered each estimator's own mean at close to the nominal rate and covered the truth far less often, because the bias of most designs exceeded their sampling error. Comparisons between designs were much more precise than their separate intervals suggested, and the book's six draws proved representative for weighting and stratification but unfavourable to propensity score matching."],

["h3", "9.9.3  Recommendations"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, we would report a weighting or stratification estimate with a sandwich standard error that includes the propensity model, or with a bootstrap of at least 200 replicates that refits the score; a doubly robust estimate with a bootstrap standard error; and a matching estimate with the paired standard error, adding the Abadie–Imbens correction under replacement and reporting the reuse. We would never report the default standard error of a weighted regression. We would report the estimates of at least two defensible designs with the standard error of their difference, and we would state that the intervals measure sampling error and not bias."],

["p", "The recommendation most worth carrying to other data is the one Section 9.5 establishes. A correct confidence interval is a statement about the variability of a procedure, not about its distance from the truth, and in observational data the second can be much larger than the first. The interval should be reported, and computed correctly, but the case for believing the estimate rests on the design, on the balance it achieved, and on the sensitivity analysis that Chapter 10 describes."],

["h3", "9.9.4  Scripts for this chapter"],

["tab", "9.6", "Scripts for Chapter 9. All available from the companion website.",
  [1100, 3700, 2900, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["9.1", "ch09/09_01_estimate_primary.py", "Table 9.1; the figures of Sections 9.3 and 9.7", "6 min"],
    ["9.2", "ch09/09_02_standard_errors_across_draws.py", "Tables 9.2 to 9.5; Figure 9.1", "25 min"],
  ],
  "Script 9.2's tables come from the full run of 200 draws, with the bootstrap on the first 40, which takes about three hours on two cores and is committed to the repository as results/ch09_standard_errors_200.csv. By default the script reruns the first 40 draws, with the bootstrap on the first 5, and confirms that they reproduce the committed rows; --draws 200 --boot-draws 40 repeats the full run.",
  ["l", "l", "l", "r"]
],
["h3", "9.9.5  Further reading"],

["p", "On the variance of weighted estimators with an estimated propensity score, Lunceford and Davidian give the sandwich estimator for the ATE and show why ignoring the estimation of the score overstates its variance; the same stacking argument extends to the odds-weighted ATT, although for the ATT the direction of the naive error is not guaranteed in general. Holmes (2014) treats matched pairs as dependent samples and covers weighted least squares, and is the natural companion to Sections 9.3.3 and the Trap box. Abadie and Imbens derived the standard error for matching with replacement, showed that the ordinary bootstrap can fail for matching, and later derived the adjustment for matching on an estimated propensity score that Section 9.4 invokes."],

["p", "Austin and Small compare bootstrap methods for samples matched on the propensity score without replacement, in simulation, and their results are a useful complement to Table 9.2 in settings with less overlap than PLIDA-SIM. Efron and Tibshirani remain the standard general introduction to the bootstrap, including the choice of the number of replicates."],

["h3", "9.9.6  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Reproduce Table 9.1 on PLIDA-SIM B. For odds weighting and the normalised ATE, compare the naive, sandwich and bootstrap standard errors, and report by how much the correction narrows each interval.",
  "Run the bootstrap of Fragment 9.2 for odds weighting twice, once refitting the score in each replicate and once reusing the original weights. Explain the difference between the two standard errors.",
  "Estimate the ATT by weighted least squares with the odds weights, and report the default, robust and sandwich standard errors. Which would you report, and why?",
  "Match with replacement and report the number of distinct controls, the largest reuse, and the paired and Abadie–Imbens standard errors. How much does the reuse correction change the interval?",
  "Compute the bootstrap standard error of the difference between twenty strata with and without regression within strata, and compare it with the standard error you would infer from the two separate intervals.",
]],
["h3", "9.9.7  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Why can accounting for the estimation of the propensity score make a standard error smaller rather than larger?",
  "What must be inside the loop of a bootstrap for a propensity score estimator, and what goes wrong if the matched pairs are resampled instead?",
  "Why is the paired standard error of a matched sample usually smaller than the unpaired one, and when would reuse of controls make it too small?",
  "A correct 95 per cent interval contains the truth in fewer than one draw in five. What does the interval measure, and what does it not?",
  "An inflated standard error covers the truth more often than a correct one. Why is that no argument for using it?",
  "Two designs have overlapping 95 per cent intervals but one is better in 99 per cent of draws. How can both statements be true, and which standard error resolves the question?",
]],

];
