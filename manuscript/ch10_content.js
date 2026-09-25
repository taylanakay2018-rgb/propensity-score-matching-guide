// Chapter 10 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "10  Sensitivity, Interpretation and Policy Recommendations"],

["h2", "10.1  Purpose and scope of this chapter"],

["p", "Chapter 9 ended with an uncomfortable finding. Once the standard errors were computed correctly, the intervals of most designs covered their own long-run average at close to the nominal rate and covered the truth far less often, because the estimates were biased by more than their sampling error. Odds weighting on the logistic score of Chapter 3 is about eleven per cent low across draws, and no diagnostic in Chapter 8 could see it. This chapter asks where that bias comes from, what a researcher without the truth file could have known about it, and what the estimate, with its bias acknowledged, means for the policy decision it was built to inform."],

["p", "The chapter's central argument is that the remaining bias has three sources, and only one of them is unobservable. Part of it comes from how the covariates entered the propensity model, which a researcher can check with the data in hand; part comes from a confounder that no dataset recorded; and a smaller part remains when both are corrected. Sensitivity analysis is the tool for the second source only. The chapter shows what two standard sensitivity analyses would have said on the primary dataset and then does what no real analysis can: it checks each of them against the confounder that the generator's truth file shows was actually missing."],

["p", "By the end of the chapter, readers should be able to test the functional form of a propensity model against a richer alternative; to compute and interpret a robustness value and a benchmarked bound on omitted-variable bias; to compute Rosenbaum's bound for a matched design and to recognise what it does and does not describe; to translate an estimate into dollars per participant and a break-even cost; and to report subgroup and time-path estimates with the cautions they require. The chapter closes with the reproducibility and governance practices of a publishable analysis and a reporting checklist compiled from the whole book."],

["p", "Three scoping notes. The first is that Sections 10.2 and 10.3 use the generator's truth file beyond the true effect, which Chapter 6 did once and for the same reason: to diagnose rather than to estimate. Every quantity a researcher could compute is identified as such, and every quantity that needs the truth file is labelled in the tables. The second is that the chapter works, as Chapters 8 and 9 did, on the logistic score of Chapter 3 and the untrimmed eligible population. The third is that Section 10.2 uses 40 independent draws of PLIDA-SIM, while Sections 10.3 and 10.4.1 use the primary dataset, because a sensitivity analysis is something done to one estimate rather than to a procedure."],

["h2", "10.2  Three sources of the remaining bias"],

["p", "Chapter 2 declared the covariates as named lists so that a later analysis could be run by substituting one list rather than by rewriting the model. Table 10.1 does exactly that. Starting from Chapter 3's propensity model, it adds terms in turn and reports the bias of three estimators on each resulting score: odds weighting, the doubly robust estimator of Chapter 6 (whose outcome model gains the same terms) and Mahalanobis matching within a caliper on the score. The first two additions use only observed variables. The next two, the pre-programme earnings shock and the latent employability score, come from the truth file and could not be added in a real analysis. The last row weights by the true propensity score, which is the best any fitted model could do."],

["tab", "10.1", "Where the remaining bias comes from: bias of the ATT, per cent of the true effect, mean of 40 draws.",
  [3376, 1050, 1000, 1300, 1300, 1000],
  ["Propensity model", "Odds weighting", "Doubly robust", "Mahalanobis", "Change, odds weighting", "SE of change"],
  [
    ["Chapter 3's score", "−11.1%", "−12.5%", "−0.8%", "", ""],
    ["+ 2016 earnings in dollars and age squared", "−7.9%", "−8.3%", "−2.4%", "+3.2", "0.18"],
    ["+ education as categories and English proficiency", "−7.3%", "−7.6%", "−2.0%", "+0.6", "0.04"],
    ["+ the pre-programme earnings shock (truth file)", "−6.9%", "−7.1%", "−1.4%", "+0.5", "0.04"],
    ["+ employability (truth file)", "−3.3%", "−3.7%", "+1.6%", "+4.0", "0.07"],
    ["Employability alone (truth file)", "−7.0%", "−8.6%", "+3.3%", "+4.1", "0.08"],
    ["+ mutual obligation status", "−7.3%", "−7.9%", "−4.6%", "0.0", "0.65"],
    ["The true propensity score", "−1.5%", "−1.9%", "+3.5%", "+9.6", "1.72"],
  ],
  "Seeds 20260808 to 20260847. Rows 2 and 3 add their terms to the row above; rows 4, 5 and 7 add theirs to row 3; row 6 adds employability alone to Chapter 3's score. The change is the paired difference in the bias of odds weighting from the row it builds on (row 1 for rows 6 and 8), with the standard error of that difference across draws. Rows marked truth file use variables that no real analysis could observe.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "The table decomposes the eleven points of bias of odds weighting into parts. How the covariates entered accounts for almost four points: three for the form of 2016 earnings and the age term, and a little more than half a point for education and English proficiency. The confounder that nobody measured accounts for four. What remains after both corrections, about three points, is of the same order as the bias of weighting by the true score itself. The doubly robust estimator follows odds weighting closely throughout, as it did in Chapter 6, because its outcome model contains the same covariates and so inherits the same omissions."],

["p", "Mahalanobis matching behaves differently, and the difference is instructive. It matches on the covariates directly and uses the score only to set the caliper, so improvements to the score barely move it: its bias stays within a few points of zero on every row. Its small bias in Chapter 5 was therefore not the product of a better propensity score, and the refinements that help the weighting estimators do not help it."],

["h3", "10.2.1  How the covariates entered"],

["p", "Chapter 3 entered 2016 earnings as a logarithm, arguing that a dollar matters less to a person earning $80,000 than to one earning $5,000. The argument is reasonable, but the generator of PLIDA-SIM makes the probability of taking part depend on earnings in dollars, and the logarithm alone cannot reproduce that relationship at the top of the distribution. Adding earnings in dollars beside the logarithm, together with a squared term in age, removes 3.2 points of bias, and the standard error of that improvement, 0.18, shows it to be systematic rather than a feature of particular draws. Section 3.3.2 anticipates this: the log transform is an assumption to be checked rather than one that can simply be preferred."],

["p", "The important point is that this part of the bias could have been found without the truth file. A likelihood-ratio test compares the fit of the propensity model with and without the candidate term, and Fragment 10.1 shows the calculation. On the primary dataset the statistic is 10.4 on one degree of freedom, with a p-value of 0.001, and across the 40 draws the test rejects at the five per cent level in 28. It is a test of the assignment model, which uses only the treatment indicator and the covariates, and so it can be run before the outcome is examined without compromising the separation of design from analysis that Chapter 2 established."],

["frag", [
  "_, ll0 = fit_logit(X, D)                                # Chapter 3's model",
  "_, ll1 = fit_logit(pd.concat([X, extra], axis=1), D)    # with the candidate terms",
  "lr = 2 * (ll1 - ll0)",
  "p = chi2.sf(lr, extra.shape[1])                         # degrees of freedom: terms added",
], "Fragment 10.1  A likelihood-ratio test of the propensity model's functional form. Full script: ch10/10_01_sources_of_bias.py"],

["p", "Two cautions attach to the test. It rejected in 28 of 40 draws rather than in all of them, so that a researcher who relied on it would have missed the term about three times in ten. And a test of fit is not a test of balance: it asks whether the term improves the prediction of treatment, which Chapter 3 showed is not the objective, and it is useful here because the term it finds is one through which the assignment actually operates. The practical recommendation is therefore modest. The functional form of each continuous confounder should be tested against a richer alternative, such as the variable in levels beside its transform or a spline, and a term the test supports should be kept unless it damages overlap."],

["h3", "10.2.2  A confounder no one measured"],

["p", "The truth file holds two variables that the analysis file does not. Chapter 2 introduced the first, the pre-programme earnings shock, as the archetypal confounder, and undertook that this chapter would ask what happens when it is not observed. The answer is that very little happens. Adding the shock to the model moves the bias by half a point, because the shock leaves a direct trace in the analysis file: the fall in earnings between 2015 and 2016 records most of what it does, and the model already contains it. A confounder does little harm when a measured variable stands in for it, and the reason to measure the fall in earnings carefully, as Chapter 2 did, is that it stands in for the shock."],

["p", "The second variable, a latent employability score, is different. It lowers the probability of taking part, as a caseworker's judgement that a person is likely to find work unaided would, and it raises later earnings, and it is correlated with nothing that the analysis file records. Adding it to the model removes 4.0 points of bias, and adding it alone to Chapter 3's model removes 4.1, so that its contribution is almost exactly additive to that of the functional form. Because more employable persons are less often treated and would have earned more without treatment, the controls who resemble the treated on the observed covariates are, on average, more employable than the treated, and the estimate is too low. This is the part of the bias that no analysis of the observed data can remove, and it explains why the prognostic score of Section 8.8 tracked the bias but was displaced from it: a prognostic score is built from observed covariates and cannot see employability either."],

["p", "Table 10.1 also repeats the experiment of Section 3.7. Adding mutual obligation status, the near-instrument, leaves the average bias of odds weighting unchanged but raises its standard deviation across draws from 3.9 points to 5.5, and it pushes Mahalanobis matching from −2.0 to −4.6 per cent. A covariate that predicts treatment but hardly the outcome removes no bias, because it is barely a confounder, and costs precision, because it makes the weights more extreme. The finding matters for Section 10.3.2."],

["h3", "10.2.3  What is left"],

["p", "With the functional form corrected and employability added, odds weighting is 3.3 per cent low. Weighting by the true propensity score is 1.5 per cent low, but with a standard deviation of 10.9 points across draws, because the true score depends on the near-instrument and its weights are extreme. The residual is therefore partly a feature of the estimator and partly the remaining difference between a logistic model and the generator's assignment mechanism, and neither part is large enough, relative to the spread of the estimates, to be worth pursuing further. For the researcher the lesson is the ordering: four points were within reach of the observed data and a specification test, four were beyond reach of any analysis of the observed data, and the sensitivity analysis of the next section addresses only the second."],

["h2", "10.3  Sensitivity analysis"],

["p", "A sensitivity analysis asks how strong an unobserved confounder would have to be to change a conclusion. It does not estimate the confounder, and it cannot say whether one exists; what it offers is a statement of the form: an unmeasured variable would have to be at least this strongly related to treatment and to the outcome for the conclusion to be overturned. The reader of the analysis then judges whether a variable of that strength is plausible. Two approaches are standard, and they suit different designs. The first, due to Cinelli and Hazlett, applies to a regression estimate and expresses the confounder's strength as shares of explained variance. The second, due to Rosenbaum, applies to a matched design and expresses it as a ratio of the odds of treatment."],

["h3", "10.3.1  How strong would a confounder have to be?"],

["p", "Cinelli and Hazlett's approach begins from the regression of 2019 earnings on the treatment indicator and the covariates of the outcome model, which on the primary dataset gives an estimate of $6,027 with a standard error of $320. Two quantities summarise its robustness, and both are computed from the regression output alone, as Fragment 10.2 shows. The first is the partial R-squared of the treatment with the outcome: here 0.0083, meaning that a confounder explaining all of the outcome's residual variance would have to explain 0.83 per cent of the treatment's residual variance to remove the effect entirely. The second is the robustness value, the share of the residual variance of both treatment and outcome that a confounder would have to explain to bring the estimate to zero: here 0.087, or 8.7 per cent. To bring the estimate down to $5,000, the robustness value is 0.015."],

["frag", [
  "t = b[1] / se                                           # the treatment's t statistic",
  "r2_yd = t ** 2 / (t ** 2 + df)                          # its partial R-squared",
  "f = t / np.sqrt(df)",
  "rv = 0.5 * (np.sqrt(f ** 4 + 4 * f ** 2) - f ** 2)       # the robustness value",
  "",
  "# the largest bias from a confounder with partial R-squareds r2dz and r2yz",
  "bias = se * np.sqrt(df) * np.sqrt(r2yz * r2dz / (1 - r2dz))",
], "Fragment 10.2  The omitted-variable quantities of Cinelli and Hazlett, from the regression output. Full script: ch10/10_02_sensitivity.py"],

["p", "Numbers of this kind are hard to judge in the abstract, and the approach's most useful feature is that it can benchmark them against the observed covariates. The partial R-squareds of education, for example, are measured by leaving education out of the regression and asking how much of the remaining variance of treatment and earnings it explains. A hypothetical confounder with the same partial R-squareds as education, or with some multiple of them, then yields a bound on the bias that the reader can compare with the estimate. Table 10.2 gives the bounds for three benchmarks and, in its last row, for employability itself."],

["tab", "10.2", "How strong would a confounder have to be? The regression estimate on the primary dataset.",
  [3926, 1700, 1700, 1700],
  ["A confounder", "R² with treatment", "R² with earnings", "Largest bias"],
  [
    ["As strong as highest education", "0.0011", "0.0130", "$255"],
    ["Three times as strong as highest education", "0.0034", "0.0390", "$766"],
    ["As strong as log earnings 2016", "0.0005", "0.0227", "$212"],
    ["Three times as strong as log earnings 2016", "0.0014", "0.0682", "$636"],
    ["As strong as fortnights on payment 2016", "0.0005", "0.0056", "$114"],
    ["Three times as strong as fortnights on payment 2016", "0.0016", "0.0168", "$342"],
    ["Employability (truth file)", "0.0018", "0.0148", "$342"],
  ],
  "Regression of 2019 earnings on treatment and the covariates of Chapter 6's outcome model, including occupation: estimate $6,027, standard error $320. R² with treatment is the confounder's partial R-squared with the treatment indicator given the covariates; R² with earnings is its partial R-squared with 2019 earnings given treatment and the covariates. The largest bias is the absolute change in the estimate that a confounder of that strength could produce.",
  ["l", "r", "r", "r"]
],

["p", "The benchmarks give a clear picture. A confounder as strong as education would shift the estimate by at most $255, and one three times as strong by at most $766. To bring the estimate down to $5,000, a confounder would have to be 4.0 times as strong as education; to bring it to zero, 23.3 times as strong. A researcher reporting the analysis could therefore say that the conclusion that the programme raised earnings would survive any unmeasured variable up to twenty times as strong as education, and that the conclusion that it raised them by more than $5,000 would survive one up to four times as strong."],

["p", "The truth file allows the statement to be checked. Employability's partial R-squareds are 0.0018 with treatment and 0.0148 with earnings, a little stronger than education, and the bound gives $342. Refitting the regression with employability included moves the estimate to $6,368, a shift of exactly $342, because for a linear regression the bound is attained by a confounder of the stated strength. The benchmarking therefore worked as intended: the confounder that was actually missing was about as strong as a well-chosen observed covariate, and a reader who judged a confounder up to three times as strong as education to be plausible would have covered it. The direction, however, is one the bound does not supply. The shift was upward, so the missing confounder had made the estimate too low, and a researcher who assumed the usual story of positive selection into a programme would have guessed the sign wrongly."],

["fig", "10.1", "Sensitivity contours for the regression estimate on the primary dataset. Each contour joins the confounder strengths that could produce the stated largest bias; the horizontal axis is the confounder's partial R-squared with treatment and the vertical axis its partial R-squared with 2019 earnings. Open markers are benchmarks: a confounder as strong as highest education (circle), three times as strong (circle), as strong as log earnings 2016 (square) and as strong as fortnights on payment 2016 (triangle). The star is employability, from the truth file. Produced by Script 10.2.",
  "figure_10_1_sensitivity.tif"],

["p", "Figure 10.1 shows the same information as contours. The benchmarks and the actual confounder all lie in the lower left corner, where the largest bias is a few hundred dollars, while the estimate of $6,027 would need a confounder far off the scale of the plot to disappear. Two features of the figure deserve comment. The first is how small the partial R-squareds with treatment are: each benchmark covariate explains less than a fifth of one per cent of the residual variance in participation, which is what one would expect of a programme whose assignment depends largely on caseworkers' judgement. The second is that the contours bend sharply near the origin, so that a confounder weakly related to treatment can still produce a bias of several hundred dollars if it is strongly related to earnings. The analysis applies formally to the regression estimate; for the weighting and matching estimators, which adjust for the same covariates, it is a guide to the order of magnitude rather than an exact bound."],

["h3", "10.3.2  How much hidden bias would overturn the conclusion?"],

["p", "Rosenbaum's approach starts from a matched design. If treatment were assigned at random within matched pairs, each member of a pair would be equally likely to be the treated one; hidden bias means that an unobserved variable makes one member more likely to be treated than the other. The sensitivity parameter, conventionally written Γ, is the largest ratio by which the odds of treatment of two matched persons could differ because of it. At Γ = 1 there is no hidden bias. For each larger Γ the analysis computes the worst-case p-value of a test of no effect, and reports the critical Γ at which the conclusion would no longer be significant. Fragment 10.3 shows the calculation for Wilcoxon's signed-rank test on the pair differences in 2019 earnings."],

["frag", [
  "x = d - tau0                                            # pair differences less the effect tested",
  "r = rankdata(np.abs(x))",
  "T = r[x > 0].sum()                                      # the signed-rank statistic",
  "p = G / (1 + G)                                         # worst case at hidden bias G",
  "z = (T - p * r.sum()) / np.sqrt(p * (1 - p) * (r ** 2).sum())",
  "p_upper = 1 - norm.cdf(z)                               # the conclusion holds while p_upper <= 0.05",
], "Fragment 10.3  Rosenbaum's bound for matched pairs, with the normal approximation. Full script: ch10/10_02_sensitivity.py"],

["p", "Table 10.3 reports the critical Γ for three conclusions on each of the two matched designs of Chapter 5: that the programme raised earnings at all, that it raised them by more than $2,500, and that it raised them by more than $5,000. It also reports how much employability actually changes the odds of treatment between the members of each pair, which the truth file allows us to compute."],

["tab", "10.3", "How much hidden bias would overturn the conclusion? Critical Γ on the primary dataset.",
  [2226, 1000, 1000, 1000, 1000, 1400, 1400],
  ["Matched design", "Estimate", "Effect > $0", "Effect > $2,500", "Effect > $5,000", "Employability, median", "Employability, 95th percentile"],
  [
    ["Mahalanobis matching, 1:1", "$6,640", "2.29", "1.67", "1.20", "1.17", "1.56"],
    ["PS matching, 1:1", "$4,921", "1.68", "1.32", "1.03", "1.17", "1.57"],
  ],
  "Critical Γ: the largest ratio of the odds of treatment within a pair at which the one-sided signed-rank test still rejects the stated null hypothesis at the five per cent level. The last two columns (truth file) are the ratio by which employability alone changes the odds of treatment between the two members of each pair, as its median and 95th percentile across pairs. Caliper 0.1 standard deviations of the logit, without replacement. PS matching is propensity score matching.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "For Mahalanobis matching, the conclusion that the programme raised earnings would survive hidden bias up to Γ = 2.29, meaning an unobserved variable that more than doubled the odds of treatment of one member of a pair relative to the other. The conclusion that it raised them by more than $5,000 is much more fragile, surviving only up to Γ = 1.20. Propensity score matching is less robust on every conclusion, at 1.68, 1.32 and 1.03, chiefly because its estimate is lower."],

["p", "One feature of the last column needs explanation. The propensity score matched estimate is $4,921, yet the test rejects an effect of $5,000 or less at Γ = 1.03. The signed-rank test concerns a constant shift in the distribution of the pair differences rather than their mean, and its own estimate of that shift, the Hodges–Lehmann estimate, is $5,762 for these pairs. Rosenbaum's bound therefore applies to the rank test and its estimate, not to the mean difference that the chapter has reported throughout, and a report should say which estimate the bound refers to."],

["p", "Employability changes the odds of treatment within a pair by a median factor of 1.17, and by 1.56 in the 95th percentile of pairs. Both are well below the critical Γ for a positive effect in either design, so that the missing confounder, had its strength been guessed correctly, would not have overturned that conclusion. For an effect above $5,000, the median pair already reaches the critical Γ of Mahalanobis matching, and a researcher could not have claimed that conclusion as robust; the true effect, $6,408, happens to exceed it."],

["box", "Trap: Γ describes assignment, not outcomes", [
  "It is tempting to check a critical Γ against the actual odds ratios of the pairs, and the truth file makes that possible. For the true propensity score, the ratio of the odds of treatment of the two members of a pair has a median of 1.44 in the Mahalanobis matched sample, but its 95th percentile is 136.5, and 25.4 per cent of pairs differ by a factor of more than ten. Judged by those figures, the matched design suffers hidden bias far beyond its critical Γ of 2.29, and its conclusions are worthless.",
  "They are not, and the reason is that 81 per cent of the pairs with a ratio above ten differ in intensive mutual obligation, the near-instrument that Chapter 3 kept out of the model. Mutual obligation changes the odds of taking part enormously and the outcome hardly at all, so the hidden bias it creates in assignment produces almost no bias in the estimate. Rosenbaum's Γ is a statement about assignment, and the bound is a worst case that assumes the unobserved variable is also as closely related to the outcome as it could be. A large Γ is dangerous only if the variable that produces it also predicts the outcome, which is why a sensitivity analysis must be judged against plausible confounders rather than against the dispersion of the true score.",
]],

["h3", "10.3.3  What a sensitivity analysis can and cannot say"],

["p", "Both analyses, checked against the truth, would have served a researcher well. Each placed the actual confounder in the range that a careful reader would have judged plausible, and each correctly separated the robust conclusion (the programme raised earnings) from the fragile one (it raised them by more than $5,000). Neither could have supplied the direction of the bias, and neither addressed the four points that came from how the covariates entered, because a sensitivity analysis concerns a variable that is missing, not a variable that is present in the wrong form. It is therefore a complement to the specification checks of Section 10.2.1, not a substitute for them."],

["p", "Two practical choices follow. The benchmarks should be chosen before the analysis is run and should be covariates whose relationship to treatment and outcome a reader can judge, as education is; benchmarking against the strongest covariate available will make any estimate look fragile, and against the weakest will make it look robust. And the sensitivity analysis should be reported for the conclusion that matters to the decision, which is rarely whether the effect is positive. Chapter 2 noted that the same logic extends to data that are missing not at random and to attrition: in each case the question is how different the unobserved persons would have to be for the conclusion to change, and the answer is reported as a threshold for the reader to judge."],

["h2", "10.4  What the estimate means for policy"],

["p", "An estimate becomes useful to a decision when it is expressed in the units the decision is made in, for the persons the decision concerns and over the period that matters. This section takes each in turn, using the primary dataset for the dollar figures and the 40 draws for the subgroup and time-path estimates, whose bias the truth file lets us report."],

["h3", "10.4.1  In dollars"],

["p", "The estimates of Table 9.1, which apply the designs of Chapters 5 to 7 to Chapter 3's logistic score without trimming, range from $4,921 to $6,640. We take two of them for illustration: odds weighting, at $5,601 with a sandwich standard error of $241, and Mahalanobis matching, at $6,640 with a paired standard error of $337. The designs that Chapters 5 and 6 recommend give estimates within this range: $6,193 for Mahalanobis matching with three controls (Table 9.1) and $6,209 for odds weighting on the trimmed boosted score. Both are in 2019 dollars, the base year of the price indices of Chapter 2. For every 1,000 participants they imply an increase in annual earnings of between $5.6 million and $6.6 million in 2019."],

["p", "A decision about the programme turns on whether that gain justifies its cost, and the cost is not in PLIDA-SIM. Rather than invent one, Table 10.4 turns the question around. It reports the cost per participant at which the discounted earnings gain would just pay for the programme, for gains lasting one, three and five years, at the point estimate and at the lower end of each 95 per cent interval. A decision-maker who knows the programme's cost can read off whether it is below the break-even figure; one who does not can see how long the gain would have to last."],

["tab", "10.4", "The cost per participant at which the earnings gain would pay for the programme, 2019 dollars.",
  [2226, 1700, 1700, 1700, 1700],
  ["Years the gain lasts", "Odds weighting", "Lower bound", "Mahalanobis matching", "Lower bound"],
  [
    ["1", "$5,601", "$5,129", "$6,640", "$5,979"],
    ["3", "$16,318", "$14,944", "$19,344", "$17,419"],
    ["5", "$26,420", "$24,195", "$31,320", "$28,202"],
  ],
  "Primary dataset. The break-even cost is the 2019 effect multiplied by the sum of the discount factors at three per cent a year over the years the gain lasts, with the first year undiscounted. The lower bound uses the lower end of the 95 per cent interval of Chapter 9. The gain is assumed constant over the period.",
  ["l", "r", "r", "r", "r"]
],

["p", "Three cautions belong beside the table. The first is that an earnings gain is not the whole of the programme's value, nor is it all a gain to the public purse: some of it is offset by reduced income support, some is returned as tax, and some may come at the expense of other job seekers whom the participants displaced, which no comparison of participants with non-participants can detect. The second is that the data end in 2019, so that the persistence of the gain is an assumption, and the table shows it to be the assumption that matters most: the break-even cost varies far more with the years the gain lasts than with the choice of estimator or the width of the interval. The third is that the figures are for the persons who took part. The effect of extending the programme to others is the ATE, which Chapter 9 estimated at $4,285 to $4,584 against a true value of $5,412, and a decision to expand should use it."],

["p", "The sensitivity analysis of Section 10.3 translates into the same units. A confounder three times as strong as education could move the regression estimate by $766, or by roughly $2,200 over three years; a break-even comparison that survives that adjustment is robust to any unmeasured variable a reader is likely to find plausible."],

["h3", "10.4.2  For whom"],

["p", "Decision-makers usually want to know whether the programme works better for some groups than for others, since the answer bears on who should be referred. Table 10.5 reports the odds-weighted ATT, on Chapter 3's score, for three pairs of subgroups defined before the programme: persons with no education beyond Year 12 and those with more, long-term recipients of income support and others, and those whose earnings fell by more than a quarter in 2016 and those whose earnings did not."],

["tab", "10.5", "Who the programme helps: ATT by subgroup, 2019 dollars, mean of 40 draws.",
  [2826, 1000, 1000, 1000, 1000, 1100, 1100],
  ["Subgroup", "Treated persons", "Estimate", "Truth", "Bias", "Bias, observed terms added", "Bias, and employability"],
  [
    ["Low education (Year 12 or less)", "2,330", "$7,739", "$7,777", "−0.5%", "−3.2%", "−0.7%"],
    ["Higher education", "2,490", "$3,842", "$5,185", "−25.9%", "−13.4%", "−7.2%"],
    ["Long-term recipient", "2,116", "$7,408", "$7,743", "−4.3%", "−5.6%", "−3.0%"],
    ["Not a long-term recipient", "2,703", "$4,409", "$5,416", "−18.6%", "−9.0%", "−3.5%"],
    ["Earnings dip in 2016", "1,722", "$8,260", "$8,240", "+0.2%", "−2.5%", "+0.5%"],
    ["No earnings dip", "3,098", "$4,328", "$5,437", "−20.4%", "−11.3%", "−6.5%"],
  ],
  "Odds weighting applied within each subgroup; seeds 20260808 to 20260847. The estimate and its bias use Chapter 3's score; the last two columns repeat the calculation on the scores of rows 3 and 5 of Table 10.1, the second of which needs the truth file. An earnings dip is a fall of more than a quarter between 2015 and 2016. The truth is the mean true effect for the treated persons in the subgroup.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "The estimates point the right way. In every pair the true effect is larger for the group that is more disadvantaged before the programme, and so is the estimate. But the bias is not shared evenly. For the more disadvantaged groups the estimates are within a few per cent of the truth, while for the others they are between 19 and 26 per cent low, so that the estimated difference between groups is exaggerated. Between the two education groups, for example, the estimated gap is almost $3,900 and the true gap about $2,600."],

["p", "The last two columns show where the uneven bias comes from, and it is the two sources of Section 10.2. Correcting how the covariates entered halves the bias in the less disadvantaged groups, whose members had higher earnings in 2016, where the logarithm of Chapter 3 fits the assignment worst; adding employability removes about half of what remains. Both corrections move the more disadvantaged groups much less, because for persons whose earnings fell, or who have long relied on income support, the earnings history already records much of what drives participation. A researcher could have made the first correction and would then have reported a gap between the education groups closer to the truth; no researcher could have made the second."],

["p", "The policy implication is a cautious one. Targeting the programme at the more disadvantaged groups is supported, but a report that said the programme does little for persons with post-school education would be wrong: its true effect for them is over $5,000. A subgroup estimate inherits the bias of the full estimate unevenly, and a contrast between subgroups can be more biased than either of its parts, which is why subgroup estimates should be reported with the specification checks of Section 10.2.1 already applied."],

["h3", "10.4.3  Over time"],

["p", "PLIDA-SIM records earnings in 2017 and 2018 as well as 2019, and the same design can be applied to each year. Across the 40 draws the odds-weighted estimate is −$6,034 in 2017, +$1,802 in 2018 and +$5,724 in 2019. The first figure is the lock-in effect familiar from the evaluation of training programmes: participants earn less while the programme occupies them, and more once it ends. The time path should be reported, because a decision-maker comparing the programme's cost with its gains needs to know that the first year is a loss."],

["p", "Two cautions limit how far the earlier years can be read. The first is missing data: 2017 earnings are observed for 86 per cent of the analysis file and 2018 earnings for 82 per cent, so that the earlier estimates are for complete cases, a different population from the 2019 estimate, and Sections 2.7.5 and 2.8 showed how much such a difference in population can matter. The second is bias. The generator implies a true effect of +$3,541 in 2018 for all treated persons, so the 2018 estimate is about half the truth, a larger relative error than in 2019, and the recovery from lock-in is correspondingly slower in the estimates than in fact. The shape of the path is credible; its early magnitudes are not, and a report should present them as such."],

["h2", "10.5  Presenting results to non-technical readers"],

["p", "Most of the readers of an evaluation will not read its methods section, and the summary they do read determines what the analysis is taken to have shown. Four practices help. The first is to state the effect in dollars of a named year, for the persons it describes, in a sentence rather than a table: participants earned about $5,600 to $6,600 more in 2019 than comparable non-participants. The second is to present the range between defensible designs, rather than a single confidence interval, as the main statement of uncertainty, since Chapter 9 showed that the difference between designs exceeds the sampling error. The third is to express the sensitivity analysis as a comparison with something the reader knows. The fourth is to say plainly what the estimate does not show."],

["box", "A summary for a policy brief", [
  "People who took part in the programme earned about $5,600 to $6,600 more in 2019 than similar people who did not, in 2019 dollars. The range reflects two sound ways of choosing the comparison group, and both are well above zero. Participants earned less than the comparison group in the first year, while the programme occupied them, and more from the second year on.",
  "The comparison can adjust only for what the data record. For the conclusion that the programme raised earnings to be wrong, some unrecorded difference between participants and non-participants would have to be more than twenty times as influential as education. For the gain to be below $5,000, it would have to be about four times as influential, which is possible but would be surprising.",
  "The estimate does not include the programme's cost, reductions in income support, or effects on people who did not take part. It describes the people who took part, not the people who would take part if the programme were expanded.",
]],

["p", "The box avoids three habits of technical reporting that mislead non-technical readers. It does not use the word significant, which a lay reader hears as important. It does not report a single interval as though it captured all of the uncertainty. And it does not bury the limitations after the recommendations, where they will not be read. It is written for the ATT estimates of Table 10.4 and the sensitivity figures of Section 10.3.1, and every number in it can be traced to a table in this chapter."],

["h2", "10.6  Reproducibility and governance"],

["p", "An analysis of linked administrative data is reproducible when another analyst, given the same data and the code, obtains the same numbers, and when a reader can tell which decisions were made before the outcome was seen. The companion repository to this book illustrates the practices we would recommend for any such analysis. Every script sets its random seeds and states them in its output; the environment is pinned to specific versions of every package, because some of the book's numbers change in their later digits from one version to the next; the scripts are numbered in the order in which they must be run; and a single audit script re-derives every number that the manuscript quotes from the scripts' output and fails if any disagrees. The audit caught errors in the drafts of this book that no reading of the text had found."],

["p", "The order of decisions is harder to demonstrate than the code. Chapter 2 set the 2019 earnings aside until the design was settled, and Chapters 3 to 8 chose their designs with diagnostics that do not involve the outcome. A researcher can make that order verifiable by writing an analysis plan before the outcome is examined and lodging it with the data custodian or a public registry; the plan should name the estimand, the covariates, the propensity model and its checks, the design and its alternatives, the balance criteria, and the sensitivity analysis with its benchmarks. Deviations are not a failure, but they should be reported as deviations."],

["box", "In the DataLab: releasing a sensitivity analysis", [
  "The quantities of a sensitivity analysis are aggregates and raise few disclosure difficulties: a robustness value, the partial R-squareds of a benchmark covariate, a bias bound and a critical Γ are single numbers derived from the whole sample. The pair-level differences from which Rosenbaum's bound is computed are not, and should stay inside the environment, as should the fitted values of the regressions used to benchmark. A contour plot such as Figure 10.1 is built from the aggregate quantities alone and can be recreated outside the environment from the released numbers.",
  "Subgroup estimates need more care. Each cell of a table such as Table 10.5 must meet the output checker's rules on minimum counts, and a subgroup defined by several variables can fall below them quickly. It is worth deciding the subgroups in the analysis plan, both because it prevents the search for a favourable subgroup and because it lets the output checker anticipate what will be requested.",
]],

["h2", "10.7  A reporting checklist"],

["p", "Each chapter from Chapter 2 onward ended with a list of what to record about the stage it described. Table 10.6 compiles them into a single checklist for the report of a propensity score analysis, with the section where each item is discussed."],

["tab", "10.6", "A reporting checklist for a propensity score analysis of linked administrative data.",
  [1800, 1100, 6126],
  ["Stage", "Section", "Report"],
  [
    ["Data", "2.9.2", "The treatment, outcome, dates and eligible population; constant dollars of a stated base year; missingness and attrition by treatment group."],
    ["Propensity score", "3.9.1, 10.2.1", "The covariate set declared in advance; the functional form of each continuous covariate and the test of it; any regularisation."],
    ["Overlap and trimming", "4.8.1", "The rule, fixed before the estimate was seen; the untrimmed estimate beside the trimmed one; the persons removed, described."],
    ["Matching", "5.16.1", "The distance, caliper and ratio; replacement, with the number of distinct controls; the unmatched treated persons."],
    ["Weighting", "6.11.1", "The estimand and weights; normalisation; any trimming or capping; the effective sample size."],
    ["Stratification", "7.11.1", "The number of strata and the estimate at a second number; strata dropped; regression within strata."],
    ["Balance", "8.9.1", "Standardised differences with the denominator; variance ratios; balance outside the model; an alternative design; the threshold as a convention."],
    ["Estimate", "9.9.1", "The estimand and population; dollars with a named standard error; the treatment of the estimated score; an alternative design with the standard error of the difference."],
    ["Sensitivity", "10.3", "The robustness value; bounds benchmarked against named covariates chosen in advance; Rosenbaum's Γ for a matched design; the conclusion each refers to."],
    ["Interpretation", "10.4", "Dollars per participant and per 1,000; the break-even cost; subgroups defined in advance, with the caution on contrasts; the time path, with attrition."],
    ["Reproducibility", "10.6", "Seeds, package versions and the order of scripts; the analysis plan and any deviations from it."],
  ],
  "Each row condenses the list at the end of the chapter cited, where the reasons for each item are given.",
  ["l", "l", "l"]
],

["h2", "10.8  Is this analysis ready to report?"],

["h3", "10.8.1  What this chapter found"],

["p", "The eleven points of bias that survived the design chapters had three sources. Almost four points came from how the covariates entered the propensity model, chiefly the form of 2016 earnings, and a likelihood-ratio test on the assignment model would have detected the missing term in most draws. Four points came from employability, a confounder that no dataset recorded, and the pre-programme earnings shock that Chapter 2 introduced as the archetypal confounder contributed almost nothing, because its effect passes through observed earnings. About three points remained, of the same order as the bias of weighting by the true score. Both standard sensitivity analyses, checked against the truth, placed the missing confounder within the range a careful reader would have judged plausible, and both separated the robust conclusion that the programme raised earnings from the fragile one that it raised them by more than $5,000; neither could supply the direction of the bias, which ran against the usual assumption. Rosenbaum's Γ, compared with the dispersion of the true score, would have suggested that the matched design was worthless, because a near-instrument that changes the odds of treatment enormously changes the outcome hardly at all. For policy, the estimates translate into a break-even cost that depends far more on how long the gain lasts than on the choice of estimator; the subgroup estimates point the right way but exaggerate the contrasts; and the time path shows a lock-in loss in the first year and an estimated recovery slower than the true one."],

["h3", "10.8.2  Recommendations"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, we would test the functional form of every continuous confounder in the propensity model against a richer alternative before the outcome is examined, and keep the terms the test supports. We would report a sensitivity analysis for the conclusion that matters to the decision: Cinelli and Hazlett's robustness value and benchmarked bounds for a regression or weighting estimate, and Rosenbaum's critical Γ for a matched design, with the benchmarks chosen in advance. We would express the estimate in dollars of a named year, per participant and per 1,000 participants, with a break-even cost for the programme rather than an invented one, and we would report subgroup and time-path estimates with the cautions of Sections 10.4.2 and 10.4.3."],

["p", "One recommendation needs reconciling across the book. Chapter 3 recommends the logistic score, and Chapter 6 recommends odds weighting on the boosted score once the sample has been trimmed. The two are consistent once it is recognised that the better score depends on how it is used. Matching needs a score that places comparable persons next to one another, and the logistic score did that better (Section 3.6); weighting on a trimmed sample gave the smaller bias with the boosted score in these data (Section 6.11.3). Chapters 7 to 10 use the logistic score throughout so that their results can be compared with those of Chapters 5 and 6, not because it is the better score for every method. A researcher should choose the score for the method, report the other beside it, and fix both choices before the outcome is examined."],

["p", "The recommendation most worth carrying to other data is the one this chapter shares with Chapter 9. The case for believing an observational estimate cannot rest on its standard error, or on its balance diagnostics, or on the agreement of several methods; it rests on a design that was fixed before the outcome was seen, on specification checks that address what can be checked, and on a sensitivity analysis that states plainly what would have to be true for the conclusion to fail."],

["h3", "10.8.3  Scripts for this chapter"],

["tab", "10.7", "Scripts for Chapter 10. All available from the companion website.",
  [1100, 3700, 2900, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["10.1", "ch10/10_01_sources_of_bias.py", "Tables 10.1 and 10.5; the figures of Sections 10.2.1 and 10.4.3", "20 min"],
    ["10.2", "ch10/10_02_sensitivity.py", "Tables 10.2, 10.3 and 10.4; Figure 10.1", "1 min"],
  ],
  "Script 10.1 generates its own 40 draws and ignores --datadir; --quick runs the first draw only. Script 10.2 runs on the primary dataset and writes the numbers it prints to figures/sensitivity_primary.csv, from which the audit checks the chapter.",
  ["l", "l", "l", "r"]
],

["h3", "10.8.4  Further reading"],

["p", "Cinelli and Hazlett set out the omitted-variable framework of Section 10.3.1, including the robustness value and benchmarking against observed covariates, and their sensemakr package for R and Stata implements it with the contour plots of Figure 10.1, and a separately maintained port, PySensemakr, brings it to Python. Rosenbaum's Observational Studies and Design of Observational Studies develop the sensitivity analysis of Section 10.3.2 in full, including its extension to matching with several controls and to tests other than the signed-rank test. VanderWeele and Ding's E-value is a simpler summary of the same question for risk ratios and is widely reported in epidemiology; it is a useful point of comparison, though its assumptions suit binary outcomes better than earnings."],

["p", "For readers working in Python beyond the scripts of this book, the DoWhy library organises an analysis around an explicit causal model and includes several refutation tests, among them the addition of a simulated confounder, and EconML implements estimators of heterogeneous effects with the cross-fitting that Section 8.8 used. Both are worth knowing, and both are better used once the design questions of this book have been settled than as a substitute for them."],

["h3", "10.8.5  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Test the functional form of 2016 earnings in Chapter 3's propensity model by the likelihood-ratio test of Fragment 10.1. Repeat for age and for fortnights on payment, and report which terms you would add and what each does to overlap.",
  "Compute the robustness value of the regression estimate and the bounds for confounders one and three times as strong as highest education. How many times as strong as education would a confounder have to be to halve the estimate?",
  "Compute the critical Γ for Mahalanobis matching for an effect above $0 and above $2,500. Then compute the Hodges–Lehmann estimate and explain why it differs from the mean difference.",
  "Build the break-even table of Table 10.4 with discount rates of three and seven per cent. Which assumption changes the answer more, the discount rate or the years the gain lasts?",
  "Estimate the ATT separately for persons with and without an earnings dip in 2016. Write two sentences for a policy brief describing the difference, with the caution you would attach.",
]],

["h3", "10.8.6  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Why could a likelihood-ratio test of the propensity model be run before the outcome is examined, and why is a better-fitting propensity model not always a better one?",
  "The pre-programme earnings shock is a confounder, yet omitting it causes almost no bias. Why?",
  "What does a robustness value of 0.087 mean, and why is it more useful when benchmarked against an observed covariate?",
  "A sensitivity analysis bounds the size of the bias from a missing confounder but not its direction. Why does the direction matter, and what might a researcher use to judge it?",
  "Why can a design whose pairs differ greatly in their true odds of treatment still produce an almost unbiased estimate?",
  "A subgroup contrast is more biased than either subgroup estimate. How can that happen, and what should a report say about it?",
]],

];
