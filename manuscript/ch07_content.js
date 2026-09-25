// Chapter 7 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "7  Stratification, Subclassification and Other Approaches"],

["h2", "7.1  Purpose and scope of this chapter"],

["p", "Chapters 5 and 6 balanced the treated and control groups by selecting controls and by weighting them. This chapter examines the third of the classical propensity score methods, which is to divide the eligible population into groups of persons with similar scores (i.e., strata, or subclasses) and to compare the treated and controls within each group. The method is the oldest of the three, it is the easiest to explain to a reader without a statistical background, and it remains common in applied work (e.g., in evaluations of health and education programmes), usually in its simplest form of five strata cut at the quintiles of the score."],

["p", "The chapter is built around a single decision, which is how many strata to form. Chapter 5 found that the caliper, the decision that attracts most of the attention in matching, moved the estimate by an average of less than a tenth of a percentage point. The number of strata behaves very differently. On the logistic score of Chapter 3, moving from five strata to twenty changes the estimate of the average treatment effect on the treated (ATT) by about ten percentage points, and it does so in every one of the six draws, which makes it one of the few procedural choices in this book that clearly matters. The chapter then shows that a regression within each stratum removes most of that dependence, and it closes with an approach that replaces the strata altogether with a smooth model of the outcome as a function of the score."],

["p", "By the end of the chapter, readers should be able to form strata on a propensity score and estimate both the ATT and the average treatment effect (ATE) from them, to recognise the subclassification estimate as a weighted comparison, and to choose and report the number of strata. They should also be able to recognise when a regression on the propensity score is estimating something other than the effect it appears to estimate, which is the subject of the box in Section 7.7, and to avoid the default setting that makes a spline of the score unreliable, which is the subject of the Trap box in Section 7.9."],

["p", "Three scoping notes. The first is that the chapter keeps the conventions of Chapters 5 and 6: the six draws are the same six, every estimate is scored against the true effect for the persons it describes, and the untrimmed and trimmed populations are those of Chapter 4. The second is that the chapter works on the logistic score throughout; Chapter 8 returns to the boosted score, whose behaviour under stratification is best understood through the balance diagnostics developed there. The third is that the standard errors quoted are again the naive ones, which Chapter 9 corrects."],

["h2", "7.2  Stratification as weighting in steps"],
["h3", "7.2.1  The subclassification estimator"],

["p", "The idea of subclassification is that persons with similar propensity scores had similar chances of commencing the programme, so that within a group of such persons the treated and controls should be comparable, at least on the covariates that entered the score. The researcher therefore sorts the eligible population by the score, divides it into K strata of equal size, computes the difference in mean outcomes between the treated and controls within each stratum, and averages those differences. For the ATT, each stratum's difference is weighted by the stratum's share of the treated persons; for the ATE, it is weighted by the stratum's share of everyone."],

["frag", [
  "cuts = np.quantile(ps, np.linspace(0, 1, K + 1))        # K strata of equal size",
  "s = np.clip(np.searchsorted(cuts, ps, side=\"right\") - 1, 0, K - 1)",
  "att = 0.0",
  "for k in range(K):",
  "    t, c = (s == k) & (D == 1), (s == k) & (D == 0)",
  "    att += t.sum() / D.sum() * (y[t].mean() - y[c].mean())   # treated share",
], "Fragment 7.1  The subclassification estimate of the ATT. Full script: ch07/07_01_form_strata.py"],

["p", "Rosenbaum and Rubin, who introduced the propensity score, proposed subclassification as one of its three principal uses, and they drew on a much older result of Cochran's: that five subclasses on a single confounding variable can be expected to remove about 90 per cent of the bias it causes. That result is the origin of the convention of five strata, and Section 7.4 examines how well it transfers to a propensity score built from eighteen covariates."],

["h3", "7.2.2  The same estimate, written as weights"],

["p", "Section 6.2.3 described stratification as a form of weighting in which the weights change in steps rather than continuously. The description is exact rather than figurative. For the ATT, give every treated person a weight of one and give each control in stratum k a weight equal to the number of treated persons in that stratum divided by the number of controls in it. The weighted control mean is then the same average of stratum means that Fragment 7.1 computes, and the weighted difference in means is the subclassification estimate. Weights of this kind are known as marginal mean weights through stratification."],

["frag", [
  "w = np.where(D == 1, 1.0, 0.0)",
  "for k in range(K):",
  "    t, c = (s == k) & (D == 1), (s == k) & (D == 0)",
  "    w[c] = t.sum() / c.sum()        # the stratum's controls stand in for its treated",
  "att_w = y[D == 1].mean() - np.average(y[D == 0], weights=w[D == 0])",
], "Fragment 7.2  The same estimate as a weighted comparison. Full script: ch07/07_01_form_strata.py"],

["p", "Table 7.1 confirms the identity on the primary dataset. The two calculations agree to within a few trillionths of a dollar, which is rounding error, at every number of strata. The table also shows what the steps do to the effective size of the control sample, which Chapter 6 introduced as the Kish effective sample size. With five strata the 37,708 controls carry the information of about 27,600; as the strata become finer, the weights come to vary more and the effective sample falls toward, and at 100 strata slightly below, the 25,057 of the odds weights of Chapter 6."],

["tab", "7.1", "Subclassification and its weights, ATT, primary dataset.",
  [3200, 1450, 1450, 1450, 1476],
  ["", "Subclassification", "Weighted", "Difference", "Effective controls"],
  [
    ["5 strata", "$5,053", "$5,053", "1.8e−12", "27,628"],
    ["20 strata", "$5,627", "$5,627", "5.5e−12", "26,046"],
    ["100 strata", "$5,723", "$5,723", "1.2e−11", "24,875"],
    ["Odds weighting (Chapter 6)", "", "$5,601", "", "25,057"],
  ],
  "Logistic score, eligible population, seed 20260808. Strata are cut at quantiles of the score of the whole eligible population. The difference is in dollars. Effective controls is the Kish effective sample size of the control weights, out of 37,708 controls.",
  ["l", "r", "r", "r", "r"]
],

["p", "The identity has a consequence that is easy to overlook. Because subclassification averages the weights within each stratum, it smooths away the extreme weights that Chapter 6 found so troublesome, and it does so without any explicit rule. The price is that differences in the score within a stratum are ignored: two controls at opposite ends of a stratum receive the same weight, even though one of them resembles the treated persons much more closely than the other. The balance between those two effects is what the number of strata decides."],

["h2", "7.3  Forming the strata"],

["p", "Table 7.2 shows the five strata of the logistic score on the primary dataset. Each holds the same number of persons, about 8,500, but the treated are far from evenly spread among them: the highest stratum holds 1,847 treated persons, and therefore 38 per cent of the weight in the ATT, while the lowest holds 387. The highest stratum is also by far the widest, running from a score of 0.158 to 0.573, because scores above about 0.16 are comparatively rare in the population as a whole. The persons the ATT is most concerned with are therefore grouped most coarsely."],

["tab", "7.2", "Five strata on the logistic score, primary dataset.",
  [700, 1650, 900, 1000, 1150, 1150, 1100, 700, 976],
  ["", "Score range", "Treated", "Controls", "Treated mean", "Control mean", "Difference", "Weight", "True ATT"],
  [
    ["1", "0.022 to 0.062", "387", "8,128", "$62,322", "$64,103", "−$1,780", "0.080", "$3,195"],
    ["2", "0.062 to 0.083", "646", "7,869", "$47,285", "$41,634", "+$5,651", "0.133", "$4,534"],
    ["3", "0.083 to 0.111", "807", "7,708", "$36,925", "$33,344", "+$3,581", "0.166", "$5,682"],
    ["4", "0.111 to 0.158", "1,180", "7,335", "$32,398", "$26,880", "+$5,517", "0.242", "$6,792"],
    ["5", "0.158 to 0.573", "1,847", "6,668", "$25,958", "$19,336", "+$6,622", "0.379", "$7,809"],
  ],
  "Logistic score, eligible population, seed 20260808. Means are 2019 earnings. Weight is the stratum's share of the treated, which is its weight in the ATT. True ATT is the mean of the true individual effects of the stratum's treated persons, from the truth file, and is shown only to score the estimate.",
  ["l", "l", "r", "r", "r", "r", "r", "r", "r"]
],

["p", "The five differences, weighted by the treated shares, give an ATT of $5,053 against a true value of $6,408, a bias of −21.2 per cent. That is a large improvement on the naive difference in means, which has the wrong sign (i.e., −$2,910, a bias of −145.4 per cent), but it is not a good estimate. The last column shows where the shortfall arises. The difference in stratum 5 is $6,622 against a true effect of $7,809, and the difference in stratum 1 is negative where the true effect is positive, which suggests that within the widest and the lowest strata the treated and controls may still differ in ways that affect earnings (e.g., in prior income, which varies almost as widely within the highest stratum as in the whole population)."],

["p", "Three choices are made in forming the strata, and each should be reported. The first is where to cut. Table 7.2 cuts at quantiles of the whole eligible population's scores, which is the usual choice and the one used throughout this chapter; cutting at quantiles of the treated persons' scores instead places more strata where the treated are, and in these data it performed slightly worse at five strata (a bias of −26.5 per cent across the six draws, against −22.2) and similarly at twenty. The second is the estimand, which determines only the weights given to the stratum differences, so that one set of strata serves both the ATT and the ATE. The third is what to do with a stratum that lacks treated persons or controls. Such a stratum has no comparison to offer and must be dropped, which changes the population the estimate describes; on the logistic score this never happened, at any number of strata up to 100, in any of the six draws."],

["h2", "7.4  How many strata"],

["p", "Table 7.3 repeats the subclassification across the six draws with between two and 100 strata, for both estimands, and with and without Chapter 4's variance-minimising trimming rule. The weighting estimators of Chapter 6 are included for comparison, since Section 7.2 showed that subclassification approaches weighting as the strata become finer."],

["tab", "7.3", "Bias by the number of strata, six draws.",
  [3000, 1550, 1250, 1550, 1676],
  ["", "ATT", "ATT, trimmed", "ATE", "ATE, trimmed"],
  [
    ["2 strata", "−55.8% (8.1)", "−42.7%", "−70.2% (11.7)", "−45.4%"],
    ["5 strata", "−22.2% (6.2)", "−18.0%", "−31.5% (9.7)", "−19.2%"],
    ["10 strata", "−14.8% (5.7)", "−12.7%", "−21.0% (8.4)", "−14.1%"],
    ["20 strata", "−12.0% (5.5)", "−10.6%", "−17.8% (8.2)", "−12.6%"],
    ["50 strata", "−10.7% (5.5)", "−9.6%", "−15.9% (6.7)", "−11.0%"],
    ["100 strata", "−10.5% (5.4)", "−9.5%", "−16.2% (6.4)", "−11.0%"],
    ["Odds weighting (ATT)", "−11.8% (5.4)", "−8.6%", "", ""],
    ["Normalised IPW (ATE)", "", "", "−22.7% (9.6)", "−12.1%"],
    ["Naive difference in means", "−149.3% (9.8)", "−110.7%", "−158.6% (11.7)", "−112.4%"],
  ],
  "Logistic score. Mean bias across six draws, with the standard deviation across draws in parentheses for the untrimmed population. Each estimate is scored against the true effect for the population it describes. Trimmed is the variance-minimising rule of Chapter 4.",
  ["l", "r", "r", "r", "r"]
],

["p", "The table's first message is that the number of strata matters a great deal. With five strata the ATT is 22.2 per cent low; with twenty it is 12.0 per cent low. Because the six draws are the same at each number of strata, the change can be measured within each draw, and moving from five strata to twenty raises the estimate by between 9.0 and 11.6 percentage points in every draw, by 10.2 on average, with a standard deviation of only 1.10. That is nearly twice the standard deviation of the estimate across draws, which is 5.5 with twenty strata. Chapter 5 found the caliper to move the estimate by an average of 0.09 percentage points against a draw-to-draw variation almost a hundred times larger; the number of strata is a decision of an altogether different order."],

["p", "The second message is that the gains stop at about twenty strata. Moving from twenty strata to 100 improves the ATT by a further 1.4 percentage points and the ATE by 1.6, and beyond twenty the estimates sit close to odds weighting for the ATT, as Section 7.2 would lead us to expect. For the ATE the picture is more favourable to subclassification than to weighting: with twenty or more strata the untrimmed estimate is less biased than the normalised inverse probability weighted estimate, at −17.8 per cent against −22.7, and somewhat more stable. This is the smoothing of Section 7.2 at work, since the averaging of weights within strata removes the extreme ATE weights that make the normalised estimator unstable."],

["p", "The third message concerns Cochran's 90 per cent. Five strata remove 85 per cent of the naive bias in the ATT and 80 per cent in the ATE, which is not far from Cochran's figure, and when measured against the bias that weighting on the same score removes, five strata achieve 92 per cent of it for the ATT and 94 per cent for the ATE. The rule of thumb is therefore approximately right as a statement about proportions. It is misleading as a statement about adequacy, because the naive bias in these data is so large that the remaining tenth of it is still about ten percentage points of the effect, which is as large as any difference between the estimators compared in Chapters 5 and 6. Researchers who report five strata because the literature says five strata remove 90 per cent of the bias may therefore, in data of this kind, be reporting an estimate that twenty strata would have improved substantially."],

["p", "One further caution belongs here. The naive standard error of the subclassification estimate, computed from the within-stratum variances, ranged from 0.71 to 1.27 times the actual spread of the error across the six draws, depending on the estimand, the number of strata and whether the sample was trimmed. Six draws cannot distinguish ratios in that range from one, and Chapter 9 takes up the question with the variance estimators it develops."],

["box", "In the DataLab: strata and the output checker", [
  "Each row of a table such as Table 7.2 reports the number of treated persons and controls in a stratum and their mean earnings, and an output checker is likely to treat each row as a cell subject to the usual minimum-size and dominance rules. With five strata on the primary dataset the smallest cell holds 387 persons. With 100 strata it holds 11, and 12 of the 200 cells hold fewer than 20 persons; with 200 strata the smallest holds 3 and 93 cells fall below 20. A stratum-level table at those numbers of strata is unlikely to be released without suppression.",
  "The practical ceiling this sets is not a serious constraint in these data, because Table 7.3 shows little to be gained beyond about twenty strata, where the smallest cell holds 68 persons. It is likely to matter more, however, in smaller populations or for subgroup analyses (e.g., a single state or a single cohort of commencements), where the number of strata that the data can support and the number that can be released may both be lower. The estimate itself, which is a single weighted average, raises no such difficulty.",
]],

["h2", "7.5  Balance within strata"],

["p", "A researcher who formed five strata and then checked balance would, in most cases, have seen little to prompt more. Table 7.4 reports the standardised mean difference of each of the eighteen covariates after stratification, computed within each stratum and averaged with the estimand's stratum weights, alongside the bias of the estimate. Chapter 8 develops balance diagnostics properly; the point here is only what the conventional threshold of 0.1 would have said."],

["tab", "7.4", "Balance after stratification against the bias of the estimate, six draws.",
  [1600, 1250, 1250, 1100, 1250, 1250, 1326],
  ["", "ATT: largest SMD", "ATT: over 0.1", "ATT: bias", "ATE: largest SMD", "ATE: over 0.1", "ATE: bias"],
  [
    ["5 strata", "0.108", "0.8", "−22.2%", "0.054", "0.0", "−31.5%"],
    ["10 strata", "0.056", "0.0", "−14.8%", "0.022", "0.0", "−21.0%"],
    ["20 strata", "0.029", "0.0", "−12.0%", "0.017", "0.0", "−17.8%"],
  ],
  "Logistic score, untrimmed, means across six draws. SMD is the absolute standardised mean difference of a covariate after stratification, across the eighteen covariates of the propensity model. Over 0.1 is the average number of covariates exceeding that threshold.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "With the ATE weighting, every covariate passes the threshold at five strata, with the largest standardised difference at 0.054, while the estimate is biased by −31.5 per cent. With the ATT stratum weights one covariate, on average, exceeds 0.1 at five strata, and none does at ten, while the estimate at ten strata is still 14.8 per cent low. Balance on the covariates of the score therefore improves as the strata become finer, as it should, but it does not track the bias closely, and a researcher who stopped adding strata when the balance table first passed would have stopped too early. Chapter 5 made the same observation about matching, and Chapter 8 examines it at length."],

["h2", "7.6  Regression within strata"],

["p", "The remaining differences between the treated and controls within a stratum can be adjusted for directly, by replacing the difference in means within each stratum with the coefficient on treatment in a regression of the outcome on treatment and the covariates, fitted to that stratum alone. The covariates here are those of Chapter 6's outcome model: the eighteen of the propensity model and occupation_group, the pure outcome predictor that Chapter 2 identified. The stratum coefficients are then averaged with the same weights as before. The approach has a long history in the propensity score literature, and it combines a coarse propensity score design with a local outcome model in much the way that the doubly robust estimator of Chapter 6 combines a weighting model with a global one."],

["frag", [
  "for k in range(K):",
  "    m = s == k",
  "    fit = LinearRegression().fit(np.c_[D[m], Q[m]], y[m])",
  "    diff_k = fit.coef_[0]            # the treatment coefficient, adjusted for Q",
], "Fragment 7.3  Regression within each stratum. Full script: ch07/07_02_compare_strata.py"],

["tab", "7.5", "Regression within strata, six draws.",
  [2400, 1550, 1250, 1550, 1250, 1026],
  ["", "ATT", "ATT, trimmed", "ATE", "ATE, trimmed", "Without regression, ATT"],
  [
    ["5 strata", "−9.4% (5.8)", "−9.6%", "−8.5% (9.3)", "−8.5%", "−22.2%"],
    ["10 strata", "−9.3% (5.7)", "−9.6%", "−8.5% (9.7)", "−9.4%", "−14.8%"],
    ["20 strata", "−9.0% (6.0)", "−9.5%", "−8.4% (10.8)", "−9.8%", "−12.0%"],
  ],
  "Logistic score. Mean bias across six draws, with the standard deviation across draws in parentheses for the untrimmed population. The regression within each stratum includes the eighteen covariates of the propensity model and occupation_group. The last column repeats the subclassification estimate without regression from Table 7.3.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "Table 7.5 shows that the regression removes most of the dependence on the number of strata. With regression, the ATT is −9.4, −9.3 and −9.0 per cent at five, ten and twenty strata, and within a single draw the three estimates differ by an average of only 0.66 percentage points, against the 10.2 points that separate five strata from twenty without regression. The ATE behaves similarly, at about −8.5 per cent untrimmed. These are among the least biased estimates in this book that rely on the estimated propensity score, and they are consistent with the explanation offered in Section 7.3: whatever the strata leave unbalanced appears, to a large extent, to be captured by the covariates."],

["p", "The regression does not, however, remove the remaining nine per cent. Chapter 6 showed that odds weighting on the true propensity score removes the shortfall on average, although with twice the variability, while adding the two unobserved confounders to Chapter 3's propensity model removes only part of it (Table 6.7). The shortfall is therefore a property of the score rather than of stratification, and no adjustment within strata can recover information that the score does not carry. The floor of about −9 to −12 per cent that the propensity score methods of Chapters 5 to 7 share is not, however, wholly a property of the data: Section 10.2 shows that part of it comes from how the covariates entered the score, which can be detected and corrected with the observed data, and the rest from a confounder that the data do not contain."],

["h2", "7.7  Regression on the propensity score"],

["p", "A simpler use of the score, and one that appears frequently in applied work, is to include it as a covariate in a regression of the outcome on treatment. The coefficient on treatment in a regression of 2019 earnings on the treatment indicator and the propensity score is then reported as the effect of the programme. In PLIDA-SIM this estimate averages $5,423 across the six draws, against a true ATE of $5,417, a bias of +0.1 per cent. Read at face value, it is the most accurate estimate of the ATE in this book."],

["box", "Right for the wrong reason, again: regression on the score", [
  "A regression of the outcome on a treatment indicator and a control variable does not estimate the ATE when the effect differs between persons. It estimates a weighted average of the effect in which each person is weighted, approximately, by the variance of their treatment status given the control variable, which here is ps(1 − ps). Persons with scores near a half receive the most weight and persons with scores near zero receive almost none. The estimand is the average effect in what is known as the overlap population, and in PLIDA-SIM it averages $6,147 across the six draws, between the ATE of $5,417 and the ATT of $6,446, because the effect is larger for persons more likely to be treated.",
  "Against its own estimand, the regression is 11.8 per cent low, which places it squarely among the other propensity score methods; weighting explicitly towards the overlap population, with weights of 1 − ps for the treated and ps for controls, gives −10.8 per cent. The apparent accuracy against the ATE is therefore a coincidence of two errors: the regression answers a question about a population in which the effect is larger, and it answers it with the same downward bias as everything else, and the two very nearly cancel. On the trimmed population they cancel less exactly, and the bias against the ATE is +1.2 per cent.",
  "Section 6.9 described an outcome regression that recovered the ATT for reasons unrelated to its merits. The lesson here is the same, with the difference that the error is one of estimand rather than of confounding. Before a regression on the score is reported as an ATE or an ATT, the researcher should establish which average it estimates, and the answer, for this common specification, is neither.",
]],

["p", "The overlap population is a legitimate estimand in its own right, and some researchers prefer it precisely because it gives most weight to the persons for whom treated and control comparisons are best supported. What is not legitimate is to estimate it and report it as something else. A researcher who wants the overlap effect should say so and should weight towards it explicitly, so that the population being described is stated rather than implied by a regression specification."],

["h2", "7.8  Trimming and stratification"],

["p", "The trimmed columns of Tables 7.3 and 7.5 show that Chapter 4's trimming rule helps subclassification much as it helped weighting, and for the same reason. Trimming removes persons with very low scores, for whom comparable persons in the other condition are scarce, and it improves the ATE more than the ATT: at five strata the ATE moves from −31.5 to −19.2 per cent, and the ATT from −22.2 to −18.0. At twenty strata the trimmed ATT, at −10.6 per cent, is close to the trimmed odds weighting estimate of −8.6 per cent. Once regression within strata is added, trimming makes little difference to either estimand. The number of strata remains the larger decision, and on the logistic score trimming is best regarded as a complement to an adequate number of strata rather than a substitute for it."],

["h2", "7.9  Modelling the outcome on the score"],

["p", "Subclassification models the outcome as a step function of the score, constant within each stratum. The natural refinement is to replace the steps with a smooth curve, fitting a flexible model of the outcome as a function of the score separately in each condition and using the two fitted curves to predict each person's outcome under the condition they did not receive. The ATT is then the mean, over the treated, of the observed outcome less the predicted outcome without treatment. Zhu has recently developed this idea in detail, describing it as propensity score modelling; we refer to it here as modelling the outcome on the score, to avoid confusion with propensity score matching."],

["p", "The flexible curve used here is a cubic spline in the logit of the score, with ten knots, which are the points at which the pieces of the spline join. The covariates can be added beside the spline, in which case the model becomes a regression adjustment in which the score carries the non-linear part of the relationship. Fragment 7.4 shows the essential steps."],

["frag", [
  "lp = np.log(ps / (1 - ps)).reshape(-1, 1)",
  "B = SplineTransformer(n_knots=10, degree=3, knots=\"quantile\").fit_transform(lp)",
  "m0 = LinearRegression().fit(B[D == 0], y[D == 0]).predict(B)   # outcome without treatment",
  "att = (y[D == 1] - m0[D == 1]).mean()",
], "Fragment 7.4  Modelling the outcome on a spline of the score. Full script: ch07/07_03_spline_on_score.py"],

["tab", "7.6", "Outcome models on a spline of the score, six draws.",
  [3400, 1700, 1100, 1700, 1126],
  ["", "ATT", "ATT, trimmed", "ATE", "ATE, trimmed"],
  [
    ["Knots at quantiles", "−10.2% (5.5)", "−9.3%", "−16.4% (7.9)", "−11.6%"],
    ["Knots at quantiles, with covariates", "−11.5% (5.7)", "−11.1%", "−13.9% (8.4)", "−11.4%"],
    ["Knots evenly spaced", "−1193.4% (2896.1)", "−4.4%", "−184.3% (381.2)", "−10.9%"],
    ["Knots evenly spaced, with covariates", "+3906.1% (9599.2)", "−28.2%", "+498.8% (1281.6)", "−13.7%"],
  ],
  "Logistic score. Mean bias across six draws, with the standard deviation across draws in parentheses for the untrimmed population. The spline is cubic in the logit of the score with ten knots. The covariates are the eighteen of the propensity model and occupation_group.",
  ["l", "r", "r", "r", "r"]
],

["p", "With the knots placed at quantiles of the score, Table 7.6 shows that modelling the outcome on the score performs much as the other methods of this chapter do: the ATT is −10.2 per cent without covariates and −11.5 per cent with them, and the ATE is −16.4 and −13.9 per cent, improving to about −11.5 per cent after trimming. Adding the covariates helps the ATE a little and does not help the ATT. The method is therefore probably best understood as a smooth version of subclassification, which avoids the choice of the number of strata, rather than as a remedy for the limitations shared by every estimator that relies on the estimated score."],

["box", "Trap: evenly spaced knots", [
  "The lower two rows of Table 7.6 differ from the upper two in one setting only. The spline library used in this book places its knots evenly across the range of the score unless told otherwise, and with that default the method fails badly and unpredictably. Averaged over six draws, the ATT is out by more than a thousand per cent and the ATE by nearly two hundred, although in three of the six draws the estimates are unremarkable.",
  "The cause is visible in Table 7.7. The range of the score is set by a handful of persons at each extreme, so evenly spaced knots place whole pieces of the spline where one condition has almost no one: in every draw the thinnest interval between knots holds 13 or fewer treated persons, and in one draw it holds 3 treated persons and a single control. The curve for that condition is then free to take almost any shape in that interval, and every person of the other condition who falls there receives a prediction from it. With knots at quantiles, every interval holds about a ninth of the eligible population, and the thinnest holds at least 156 treated persons. Trimming the tails also largely removes the problem, which is why the trimmed column is unremarkable, but the knots should be placed where the data are in any case.",
]],

["tab", "7.7", "The thinnest interval between knots, untrimmed population.",
  [1500, 1200, 1200, 1200, 1200, 1350, 1376],
  ["Draw", "Evenly spaced: treated", "Evenly spaced: controls", "At quantiles: treated", "At quantiles: controls", "Evenly spaced: ATT bias", "Evenly spaced: ATE bias"],
  [
    ["20260808", "13", "25", "176", "3,549", "−10.5%", "−12.8%"],
    ["20260809", "6", "2", "175", "3,461", "−11.6%", "−15.0%"],
    ["20260810", "3", "1", "156", "3,514", "−7105.1%", "−960.4%"],
    ["20260811", "4", "22", "184", "3,432", "−13.0%", "−82.9%"],
    ["20260812", "12", "23", "217", "3,565", "−1.9%", "−5.9%"],
    ["20260813", "3", "3", "181", "3,485", "−18.4%", "−29.0%"],
  ],
  "Logistic score. The fewest treated persons and the fewest controls in any of the nine intervals between ten knots, and the bias of the spline without covariates with evenly spaced knots. The fewest treated and the fewest controls need not fall in the same interval.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["h2", "7.10  Scoring the estimates"],

["p", "Table 7.8 brings together the principal estimators of the ATT from Chapters 5 to 7, recomputed on the same six draws with the functions of each chapter, so that the comparison is exact rather than assembled from separate runs. Each is scored against the true effect for the persons it describes, which for the matching estimators is the true effect for the treated persons who were matched."],

["tab", "7.8", "The ATT across Chapters 5 to 7, six draws.",
  [4800, 2200, 2026],
  ["", "Untrimmed", "Trimmed"],
  [
    ["Propensity score matching, caliper 0.1 (Chapter 5)", "−14.4% (8.5)", "−12.6%"],
    ["Mahalanobis matching within a caliper (Chapter 5)", "+0.7% (8.6)", "−0.4%"],
    ["Odds weighting (Chapter 6)", "−11.8% (5.4)", "−8.6%"],
    ["Doubly robust (Chapter 6)", "−12.6% (5.8)", "−11.5%"],
    ["Subclassification, 20 strata", "−12.0% (5.5)", "−10.6%"],
    ["Subclassification, 20 strata, regression within strata", "−9.0% (6.0)", "−9.5%"],
    ["Outcome modelled on the score, with covariates", "−11.5% (5.7)", "−11.1%"],
  ],
  "Logistic score. Mean bias across six draws, with the standard deviation across draws in parentheses for the untrimmed population. The matching estimates reproduce Chapter 5's Table 5.2 and Section 5.4; the weighting estimates reproduce Chapter 6's Table 6.6.",
  ["l", "r", "r"]
],

["p", "Two features of the table stand out. The first is how closely the estimators that rely on the score agree once each is used well: with twenty strata, with regression within strata, by odds weighting, by the doubly robust estimator or by modelling the outcome on the score, the ATT lies between about −9 and −13 per cent, and the draw-to-draw standard deviation of each is between 5.4 and 6.0. The choice among them matters much less than the decisions that preceded them, which is the conclusion Chapters 5 and 6 also reached. The second is that Mahalanobis matching remains the exception, for the reason Section 5.6 gave: it matches directly on covariates that carry much of the confounding, rather than on a score that summarises them imperfectly."],

["h2", "7.11  Is this stratified analysis ready?"],
["h3", "7.11.1  What to record about a stratified analysis"],

["p", "Six things should be recorded about any stratified analysis before its estimate is carried into Chapter 8 for balance assessment and Chapter 9 for variance estimation."],

["list", [
  "The estimand, ATE or ATT, and therefore the weights given to the stratum differences.",
  "The number of strata, how the cut points were chosen, and the estimate at a second number of strata, so that a reader can see whether the choice mattered.",
  "Any strata dropped for lacking treated persons or controls, and the number of persons they held.",
  "Whether the stratum differences are differences in means or regression-adjusted, and if the latter, the covariates of the regression.",
  "For a regression on the score, the estimand the specification actually targets, stated as such.",
  "For an outcome model on the score, the form of the model and where its knots were placed.",
]],
["h3", "7.11.2  What this chapter cost"],

["p", "The accounting for stratification is dominated by the number of strata. Moving from five strata to twenty was worth 10.2 percentage points on the ATT and 13.7 on the ATE, and moving from twenty to 100 was worth a further 1.4 and 1.6. Regression within strata was worth 12.8 points on the ATT at five strata and 2.9 at twenty. Trimming was worth 4.2 points on the ATT at five strata and 1.3 at twenty. Reporting a regression on the score as an ATE carried no measurable cost in these data only because two errors cancelled, and the misplaced knots of Section 7.9 cost, in the worst draw, many times the effect itself."],

["p", "As in Chapters 5 and 6, the expensive decisions are those that determine what information the estimate can use rather than how it is combined. Here the number of strata plays that role, because too few strata discard the information in the score within each stratum, which is the same loss that Section 5.9 described for coarsened matching."],

["h3", "7.11.3  Recommendations"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, we would form at least ten and preferably twenty strata at quantiles of the logistic score, estimate the stratum differences with a regression on the covariates within each stratum, and report the estimate at a second number of strata beside it. On these data that gives an ATT of about −9 per cent, which is among the least biased propensity score estimates in the book. We would not use five strata because a textbook reports that five strata remove 90 per cent of the bias, since in data with strong selection the remaining tenth may be larger than any other decision in the analysis."],

["p", "Two further recommendations carry to other data. A regression of the outcome on the treatment and the score should not be reported as an ATE or an ATT, because it estimates neither. And a flexible model of the outcome on the score should place its knots where the data are, which in the library used here means changing the default."],

["h3", "7.11.4  Scripts for this chapter"],

["tab", "7.9", "Scripts for Chapter 7. All available from the companion website.",
  [1100, 3400, 3200, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["7.1", "ch07/07_01_form_strata.py", "Tables 7.1 and 7.2; the cell counts of Section 7.4", "5 s"],
    ["7.2", "ch07/07_02_compare_strata.py", "Tables 7.3 to 7.5 and 7.8; the figures of Section 7.7", "5 min"],
    ["7.3", "ch07/07_03_spline_on_score.py", "Tables 7.6 and 7.7", "4 min"],
  ],
  "Scripts 7.2 and 7.3 generate their own draws, the six of Chapters 5 and 6, and ignore --datadir for that reason.",
  ["l", "l", "l", "r"]
],
["h3", "7.11.5  Further reading"],

["p", "Rosenbaum and Rubin's papers on the propensity score introduced subclassification on the score, and their 1984 paper on reducing bias with subclassification remains the clearest account of the method and of checking balance within subclasses. Cochran's much earlier analysis of subclassification on a single covariate is the source of the convention of five strata and repays reading for the conditions under which it was derived. Hong's work on marginal mean weighting through stratification develops the identity of Section 7.2 and its extension to treatments with more than two values."],

["p", "On regression with the propensity score as a covariate, and on the estimands that regression targets when effects are heterogeneous, the econometric literature on the weights implicit in regression is the relevant background; Li, Morgan and Zaslavsky's work on overlap weights develops the overlap population as an estimand in its own right. Zhu (2026) develops propensity score modelling of the outcome in detail and is the basis of Section 7.9."],

["h3", "7.11.6  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Reproduce Table 7.3 on PLIDA-SIM B for the ATT. At what number of strata does the estimate stop changing by more than one percentage point?",
  "Repeat the comparison of five and twenty strata with strata cut at quantiles of the treated persons' scores rather than everyone's. Explain why the choice matters more with few strata than with many.",
  "Compute the marginal mean weights for the ATE with five and with fifty strata and report the effective sample size of each group. Compare them with the inverse probability weights of Chapter 6.",
  "Estimate the regression of 2019 earnings on treatment and the propensity score, and compute the true effect in the overlap population from the truth file. Report the bias against the ATE, the ATT and the overlap effect.",
  "Fit the spline of Section 7.9 with evenly spaced knots and with knots at quantiles, and for each report the number of treated persons and controls in the thinnest interval. Does the evenly spaced version fail on PLIDA-SIM B?",
]],
["h3", "7.11.7  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "In what sense is subclassification a weighting method, and why does it produce less extreme weights than inverse probability weighting on the same score?",
  "Five strata remove about 85 per cent of the naive bias in these data. Why is that nonetheless an inadequate number of strata here, and in what kind of data might five be enough?",
  "Why can balance on the covariates pass the conventional threshold while the estimate remains substantially biased?",
  "Regression within strata makes the estimate almost insensitive to the number of strata. What does that suggest about the source of the bias that finer strata remove?",
  "A regression of the outcome on treatment and the score recovers the ATE almost exactly. What does it actually estimate, and why is its accuracy here a coincidence?",
  "Why does placing the knots of a spline evenly across the range of the score make the estimate unreliable, and why does trimming largely prevent the problem?",
]],

];
