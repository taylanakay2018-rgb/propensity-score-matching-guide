// Chapter 6 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "6  Creating Balanced Datasets with Inverse Probability Weighting"],

["h2", "6.1  Purpose and scope of this chapter"],

["p", "Chapter 5 balanced the treated and control groups by selecting, for each treated person, one or more controls who resembled them, and discarding everyone else. This chapter balances the two groups in a different way: it keeps every person in the eligible population and gives each of them a weight, chosen so that the weighted control group resembles the treated group, or so that both groups resemble the population as a whole. Weighting is the second of the major propensity score methods, and in applied work it is often preferred to matching, largely because it discards nobody and generalises directly to both of the estimands this book is concerned with."],

["p", "The chapter's central finding is that most of what goes wrong with weighting, and most of what goes right, happens before any weight is computed. On the logistic score of Chapter 3, weighting estimates the average treatment effect (ATE) with a bias of −22.7 per cent across six draws. After the trimming rule of Chapter 4 the bias is −12.1 per cent, and on the boosted score with the same trimming it is +2.6 per cent. The choice among weighting estimators, by contrast, matters much less than the literature's attention to it would suggest, with one exception: capping the largest weights, which is often recommended as a remedy for extreme weights, is in these data the most damaging of the weighting decisions examined in this book."],

["p", "By the end of the chapter, readers should be able to construct weights for the ATE and for the average treatment effect on the treated (ATT), and to report the diagnostics that should accompany any weighted estimate. They should also be able to recognise why trimming the sample and capping the weights are not interchangeable, and to combine a weighting model with an outcome model in the doubly robust estimator. Readers will also meet the chapter's most uncomfortable result, which is a plain outcome regression that recovers the ATT almost exactly for reasons that have nothing to do with its merits, and which is the subject of the box in Section 6.9."],

["p", "Two scoping notes. The first is that this chapter keeps the conventions of Chapter 5: the six draws are the same six, every estimate is scored against the true effect for the persons it describes, and the standard errors quoted are the naive ones, which Section 6.10 examines and Chapter 9 corrects. The second is that the outcome model introduced in Section 6.8 is where occupation_group, the pure outcome predictor that Chapter 2 identified and Chapter 3 held back, finally enters the analysis."],

["h2", "6.2  What weighting does"],
["h3", "6.2.1  Weights for the ATE"],

["p", "The logic of weighting is most easily seen through the question it answers. In a randomised trial every person has the same probability of assignment, so the treated and control groups are each a random sample of the whole population and their means can be compared directly. In an observational study the probability of treatment differs from person to person, and it differs systematically: in PLIDA-SIM, persons who are older, better educated or living in less disadvantaged areas are less likely to commence the programme. The treated group therefore over-represents some kinds of person and the control group over-represents others, which is the selection bias defined in Chapter 2."],

["p", "Inverse probability weighting corrects for this by weighting each person by the inverse of the probability of the condition they were observed in. A treated person with a propensity score of 0.05 (i.e., a person of a kind that rarely commences the programme) receives a weight of 20, because they stand for twenty persons of their kind, nineteen of whom were not treated. A control with a score of 0.05 receives a weight of about 1.05, because controls of that kind are plentiful. After weighting, each group represents the whole eligible population, and the difference between their weighted means estimates the ATE."],

["p", "The weakness of the method is visible in the same example. A treated person with a score of 0.02 receives a weight of 50, and a handful of such persons can dominate the weighted treated mean. The weights are largest precisely where the data are thinnest, which is why Chapter 4's discussion of common support is a precondition for weighting rather than a separate topic."],

["h3", "6.2.2  Weights for the ATT"],

["p", "When the question concerns the effect of the programme on those who received it, the treated group is already the population of interest and needs no reweighting. Every treated person therefore receives a weight of one, and each control receives a weight equal to their odds of treatment, ps / (1 − ps), which reweights the control group to resemble the treated group. This is odds weighting, which Chapter 4 used without developing and which this chapter treats as the principal weighting estimator of the ATT."],

["p", "Odds weights behave very differently from inverse probability weights, and the difference matters in practice. Because the treated are unweighted, there is no treated person whose weight can explode; the largest weights fall on controls with high scores, who are the controls most like the treated, and in these data those weights are modest. The price is that controls with low scores receive weights close to zero, so a large share of the control group contributes almost nothing, and the effective size of the control sample is correspondingly smaller than its nominal size."],

["frag", [
  "ate_w = np.where(D == 1, 1 / ps, 1 / (1 - ps))      # both groups toward the population",
  "att_w = np.where(D == 1, 1.0, ps / (1 - ps))        # controls toward the treated",
  "",
  "def kish(w):                                        # effective sample size",
  "    return w.sum() ** 2 / (w ** 2).sum()",
], "Fragment 6.1  The two sets of weights, and the effective sample size. Full script: ch06/06_01_build_weights.py"],

["h3", "6.2.3  Matching as a form of weighting"],

["p", "It is worth recognising before going further that matching, stratification and weighting are not three unrelated methods. One-to-one matching without replacement gives each matched person a weight of one and each unmatched person a weight of zero, and matching with replacement gives a reused control a weight equal to the number of times it was used. Stratification, which Chapter 7 develops, gives every person in a stratum the weight that makes the stratum's two groups equal in size. Weighting by the propensity score is the limiting case in which the weights vary continuously rather than in steps."],

["p", "The unifying view has a practical consequence, which is that the diagnostics developed for one method transfer to the others. The count of distinct controls that Chapter 5 recommended reporting under matching with replacement is a crude effective sample size, and the effective sample size of this chapter is its continuous counterpart. A reader who has understood why Chapter 5 recorded the one will find the other familiar."],

["h2", "6.3  Building the weights"],

["p", "Table 6.1 reports the two sets of weights on the primary dataset, for both scores of Chapter 3, together with the diagnostics that should be reported beside any weighted estimate. None of these quantities involves the outcome; they describe the design, in the sense that Chapter 5 used the term, and they can be computed and reported before any estimate is seen."],

["tab", "6.1", "The weights, and what to report beside them.",
  [3000, 3013, 3013],
  ["", "Logistic", "Boosting"],
  [
    ["Largest ATE weight", "36.8", "38.6"],
    ["Largest stabilised ATE weight", "4.2", "4.4"],
    ["Effective treated sample, ATE", "3,724 of 4,867", "3,615 of 4,867"],
    ["Effective control sample, ATE", "37,461 of 37,708", "37,465 of 37,708"],
    ["Largest control odds weight", "1.23", "1.59"],
    ["Effective control sample, ATT", "25,057 of 37,708", "24,790 of 37,708"],
    ["Heaviest 1% of controls, ATT", "4.7% of the weight", "5.0% of the weight"],
  ],
  "Primary dataset, seed 20260808, eligible population. The effective sample size is the Kish formula of Fragment 6.1. A stabilised weight is the ordinary weight multiplied by the share of the sample in the person's condition; Section 6.4 explains why this changes the size of the weights and not the estimate.",
  ["l", "r", "r"]
],

["p", "The table shows the asymmetry described in Section 6.2. Under the ATE weights the treated group loses about a quarter of its information, since 4,867 treated persons carry the information of 3,724, while the control group loses almost none; under the odds weights the position is reversed, and 37,708 controls carry the information of about 25,000. The largest ATE weight is 36.8, which means that a single treated person counts as nearly thirty-seven, whereas the largest odds weight is 1.23. The heaviest one per cent of controls carry under five per cent of the total control weight, so no small group of controls dominates the ATT."],

["p", "Two features of the table deserve comment. The first is that the two scores produce very similar weights, although Chapter 3 showed them to produce very different matched estimates; weight diagnostics of this kind are therefore necessary and not sufficient, which is a point Chapter 8 develops for balance diagnostics generally. The second is that none of these weights is extreme by the standards of the applied literature, where largest weights in the hundreds are not unusual. PLIDA-SIM has good overlap under the logistic score, and adequate overlap under the boosted score once it is trimmed, as Chapter 4 established, and the difficulties that follow arise in spite of that rather than because of its absence."],

["frag", [
  "ate = (np.average(y[D == 1], weights=ate_w[D == 1])",
  "       - np.average(y[D == 0], weights=ate_w[D == 0]))",
  "",
  "att = y[D == 1].mean() - np.average(y[D == 0], weights=att_w[D == 0])",
], "Fragment 6.2  The two weighted estimates, as differences in weighted means. Full script: ch06/06_02_compare_weighting.py"],

["h2", "6.4  Normalisation, not stabilisation"],

["p", "Two refinements of the basic estimator are routinely recommended, and applied papers frequently report having used one or both. Stabilisation multiplies each weight by the share of the sample in the person's condition, so that the weights have a mean of about one rather than a mean of about two, and the largest weight in Table 6.1 falls from 36.8 to 4.2. Normalisation divides each group's weighted sum by the sum of its weights rather than by the number of persons, which is what Fragment 6.2 does when it computes weighted means; the alternative, which divides by the sample size, is usually called the Horvitz–Thompson estimator."],

["p", "The two refinements are often described together and sometimes treated as the same thing. They are not, and Table 6.2 shows how different their consequences are."],

["tab", "6.2", "Normalisation and stabilisation, ATE, six draws.",
  [2600, 1600, 1600, 1600, 1626],
  ["Estimator", "Logistic", "Boosted", "Logistic, trimmed", "Boosted, trimmed"],
  [
    ["Unnormalised (Horvitz–Thompson)", "−25.7%", "−90.1%", "−8.7%", "−30.2%"],
    ["Normalised", "−22.7%", "−31.6%", "−12.1%", "+2.6%"],
    ["Normalised, stabilised weights", "−22.7%", "−31.6%", "−12.1%", "+2.6%"],
  ],
  "Means across six draws. Bias is against the true ATE for the persons each estimate describes. Trimmed is the variance-minimising rule of Chapter 4. The normalised estimates with and without stabilisation agree to ten decimal places in every draw.",
  ["l", "r", "r", "r", "r"]
],

["p", "Stabilisation changes nothing about the estimate. A normalised estimator divides by the sum of the weights, so multiplying every weight in a group by the same constant cancels exactly, and the two rows agree to ten decimal places in every draw. What stabilisation changes is the appearance of the weights, which is useful when they are inspected or reported and when they are carried into a weighted regression, but it is not a correction of any kind."],

["p", "Normalisation, on the other hand, changes a great deal. On the boosted score the unnormalised estimator is out by −90.1 per cent, which is to say it has lost almost the entire effect, while the normalised estimator on the same weights is out by −31.6 per cent. The unnormalised estimator is sensitive to whether the weights in each group happen to sum to the group's size, which they do only in expectation; when a few large weights push the sum away from that value, the estimate moves with it. Normalisation removes that sensitivity at no cost, and it is the version this chapter uses throughout."],

["p", "The practical recommendation is therefore to normalise always, and to stabilise when the weights are to be reported or used in a model, while recognising that the second is a matter of presentation. A methods section that reports stabilised weights has told the reader how the weights were scaled; it has not told them how the estimate was computed, and the second is the statement that matters."],

["h2", "6.5  Weighting across six draws"],

["p", "Table 6.3 reports the two principal weighting estimators across the six draws of Chapter 5, on both scores, with and without Chapter 4's variance-minimising trimming rule. The standard deviation across draws is given beside each mean, because Chapter 5 established that the draw-to-draw variability of an estimate can exceed the differences between methods, and a comparison that omits it can mislead."],

["tab", "6.3", "Weighting across six draws: bias and its standard deviation.",
  [3400, 2813, 2813],
  ["Score", "ATE, inverse probability weights", "ATT, odds weights"],
  [
    ["Logistic", "−22.7% (9.6)", "−11.8% (5.4)"],
    ["Logistic, trimmed", "−12.1% (9.3)", "−8.6% (6.0)"],
    ["Boosted", "−31.6% (8.6)", "−12.6% (4.9)"],
    ["Boosted, trimmed", "+2.6% (6.1)", "−2.8% (4.3)"],
  ],
  "Means across six draws, with the standard deviation across draws in parentheses. Estimates are normalised. The true ATE is $5,417 for the whole eligible population and the true ATT $6,446, averaged over the six draws; trimmed estimates are scored against the truth for the persons the rule retains.",
  ["l", "r", "r"]
],

["p", "Three things in the table are worth separating. The first is that the ATT is recovered considerably better than the ATE on every score and under either condition, which is consistent with Section 6.2: odds weights never become large, whereas inverse probability weights place a great deal of weight on a few treated persons with low scores. The second is that trimming helps in every row, and helps most on the boosted score, where the ATE moves from −31.6 to +2.6 per cent and the ATT from −12.6 to −2.8 per cent."],

["p", "The third is the one that connects this chapter to Chapter 3. The boosted score was the worst score for matching, with a bias of +20.8 per cent against −12.5 per cent for the logistic score, and it is the best score for weighting once the sample has been trimmed. The most likely explanation is that boosting produces more extreme scores, which harms matching by leaving treated persons without close controls, and which harms weighting too until the extreme scores are trimmed away. Once they are, the more flexible estimator's better fit in the body of the distribution is what remains. The general lesson is that the choice of score cannot be made independently of the method that will use it, and that for weighting the trimming decision of Chapter 4 comes first."],

["h2", "6.6  Trimming the sample rather than capping the weights"],

["p", "When the weights include a few very large values, two remedies are commonly offered. The first is the one Chapter 4 developed, which is to trim the sample: persons whose scores lie outside a chosen region are removed, and the estimand is redefined as the effect for those who remain. The second is to cap the weights (i.e., to winsorise them): every weight above some percentile of the weight distribution is set equal to that percentile, and nobody is removed. Capping is attractive because it keeps the full sample and the original estimand, and it is probably used as widely as it is for that reason. Table 6.4 shows what it does in these data."],

["tab", "6.4", "Capping the weights against trimming the sample, logistic score.",
  [4000, 2513, 2513],
  ["", "ATE bias", "ATT bias"],
  [
    ["No cap", "−22.7%", "−11.8%"],
    ["Capped at the 99.9th percentile", "−26.2%", "−12.2%"],
    ["Capped at the 99.5th percentile", "−37.3%", "−13.5%"],
    ["Capped at the 99th percentile", "−47.9%", "−14.9%"],
    ["Capped at the 97.5th percentile", "−71.6%", "−18.6%"],
    ["Capped at the 95th percentile", "−99.3%", "−23.7%"],
    ["Capped at the 90th percentile", "−134.3%", "−32.4%"],
    ["Sample trimmed (Chapter 4)", "−12.1%", "−8.6%"],
  ],
  "Means across six draws, logistic score, normalised estimates. Under the ATE the cap applies to all weights; under the ATT it applies to the control odds weights, since the treated weights are all one. Figure 6.1 shows both scores.",
  ["l", "r", "r"]
],

["p", "Every cap makes the estimate worse, and the damage grows steadily as the cap is lowered. At the 99th percentile, which is a common choice, the bias of the ATE roughly doubles, from −22.7 to −47.9 per cent. At the 95th percentile the ATE estimate is out by −99.3 per cent, which is to say that it has lost the entire effect, and at the 90th percentile it has the wrong sign. Trimming the sample, by contrast, reduces the bias under both estimands."],

["fig", "6.1", "Capping the weights against trimming the sample. The bias of the weighted estimate, averaged over six draws, as the weights are capped at progressively lower percentiles, for (a) the ATE under inverse probability weights and (b) the ATT under odds weights. The dotted lines mark the bias after Chapter 4's trimming rule, with no cap. Produced by Script 6.2.",
  "figure_6_1_capping.tif"],

["p", "The mechanism is specific and worth following, because it is not the one usually assumed. The advice to cap rests on the view that the largest weights are errors (e.g., products of a misfitted score) whose influence should be limited. In these data the largest weights belong to treated persons with low scores and to controls with high scores, who are likely to be exactly the persons that make the two groups comparable. A treated person who resembles the typical control is the evidence about what the programme does for persons of that kind. Capping their weights shrinks that evidence while leaving the rest of the weighted sample unchanged, which reintroduces the imbalance the weights were built to remove. Trimming removes such persons entirely and redefines the estimand accordingly, which is an honest change; capping keeps them and quietly misweights them, which is not."],

["box", "Trap: capping the weights", [
  "Capping, truncating or winsorising the largest weights is often presented as a conservative repair for extreme weights, and a methods section that reports it may appear more careful than one that does not. In PLIDA-SIM it is the most damaging weighting decision examined in this book: a cap at the 95th percentile removes the entire ATE, and on the boosted score it reverses the sign.",
  "The test before capping is the same one Chapter 5 recommended before tuning a caliper: compare the estimate with and without the cap across resamples or draws, and report both. If the cap moves the estimate substantially, it is not a cosmetic repair, and the persons whose weights it reduces should be examined rather than suppressed. Where extreme weights are a genuine problem, trimming the sample by a stated rule, as Chapter 4 recommends, addresses it without misweighting anyone.",
]],

["frag", [
  "cap_at = np.percentile(w, 99)",
  "w_capped = np.minimum(w, cap_at)          # keeps everyone, misweights some",
  "",
  "keep = trimming_rules(ps, D)[CHOSEN_RULE]  # removes some, weights the rest correctly",
], "Fragment 6.3  Capping and trimming, which look alike and are not. Full script: ch06/06_02_compare_weighting.py"],

["h2", "6.7  The near-instrument, from the weighting side"],

["p", "Section 3.7 examined what happens when mutual_obligation_status, a variable that predicts treatment strongly and the outcome hardly at all, is added to the propensity model. The effect on matching was a larger number of unmatched treated persons and no dependable change in bias. Weighting is where the cost of such a variable is felt most directly, because a covariate that sharpens the prediction of treatment without bearing on the outcome pushes the scores towards zero and one, and the weights with them."],

["p", "Measured across the six draws of this chapter, adding the near-instrument raises the largest control odds weight from 1.5 to 21.7 and reduces the effective control sample under odds weighting from 24,271 to 3,458, so that six sevenths of the control information is spent. The bias of the odds-weighted ATT moves from −11.8 to −8.8 per cent, which is nominally better, but its standard deviation across draws rises from 5.4 to 9.3 and its naive standard error from 367 to 479. The improvement in bias is smaller than the draw-to-draw variation it sits inside; the loss of precision is not. The conclusion of Section 3.7 therefore holds from the weighting side as well, and more strongly: a near-instrument costs weighting more than it costs matching, because every weight feels it, whereas matching feels it only through the persons left unmatched."],

["h2", "6.8  Combining the two models: doubly robust estimation"],
["h3", "6.8.1  How the estimator works"],

["p", "Every estimator in this chapter so far has relied on one model, the propensity model, to remove the difference between the treated and control groups. An outcome model offers a second route to the same end: fit a regression of the outcome on the covariates among the controls, predict what each treated person would have earned without the programme, and compare. The doubly robust estimator combines the two. It begins with the outcome model's prediction and then uses the weights to correct the residual imbalance that the outcome model leaves behind, so that the estimate is consistent if either the propensity model or the outcome model is correctly specified, and it does not require both."],

["p", "For the ATT, which is the estimand of most interest in this book, the construction is short. The outcome model is fitted on the controls only, each person's residual from it is computed, and the ATT is estimated as the mean residual among the treated less the odds-weighted mean residual among the controls. If the outcome model were exact, the control residuals would average zero under any weights and the weighting term would vanish; if the weights were exact, the weighted control residuals would stand in for the treated persons' missing untreated outcomes and any error in the outcome model would cancel."],

["frag", [
  "m0 = LinearRegression().fit(Q[D == 0], y[D == 0]).predict(Q)   # untreated outcome model",
  "r = y - m0                                                     # residuals, everyone",
  "",
  "att_dr = r[D == 1].mean() - np.average(r[D == 0], weights=att_w[D == 0])",
], "Fragment 6.4  The doubly robust ATT: residuals from the control outcome model, odds-weighted. Full script: ch06/06_02_compare_weighting.py"],

["p", "The covariates of the outcome model, Q in Fragment 6.4, are the eighteen of the propensity model with occupation_group added. Chapter 2 identified occupation as a pure outcome predictor (i.e., a covariate that predicts earnings but not participation), and Chapter 3 held it back from the propensity model for that reason. The outcome model is where such a covariate belongs, and Section 6.8.3 reports what it adds."],

["h3", "6.8.2  What it achieves in these data"],

["p", "Table 6.5 sets the doubly robust estimator beside its two ingredients, the weighting estimator alone and the outcome regression alone, on the logistic score with and without trimming, and on the boosted score."],

["tab", "6.5", "The doubly robust estimator and its two ingredients.",
  [3800, 1300, 1000, 1300, 1626],
  ["Estimator", "ATE bias", "sd", "ATT bias", "sd"],
  [
    ["Weighting alone", "−22.7%", "9.6", "−11.8%", "5.4"],
    ["Weighting alone, trimmed", "−12.1%", "9.3", "−8.6%", "6.0"],
    ["Outcome regression alone", "−27.0%", "9.4", "+0.5%", "5.2"],
    ["Outcome regression alone, trimmed", "−17.3%", "9.2", "−4.9%", "5.8"],
    ["Doubly robust", "−16.5%", "8.9", "−12.6%", "5.8"],
    ["Doubly robust, trimmed", "−11.7%", "9.7", "−11.5%", "6.1"],
    ["Doubly robust, boosted score", "−22.7%", "7.8", "−4.9%", "5.0"],
    ["Doubly robust, boosted score, trimmed", "−5.3%", "5.8", "−2.6%", "4.6"],
  ],
  "Means across six draws, with the standard deviation across draws. Logistic score unless stated. The outcome regression is linear in the eighteen propensity covariates and occupation_group, fitted separately on each condition; the ATT uses only the model fitted on the controls.",
  ["l", "r", "r", "r", "r"]
],

["p", "For the ATE the doubly robust estimator does what its name promises, if modestly. On the logistic score it is less biased than either ingredient, at −16.5 per cent against −22.7 per cent for weighting alone and −27.0 per cent for the outcome regression alone, and on the boosted score after trimming it reaches −5.3 per cent. Neither ingredient is correctly specified here, so the estimator's formal guarantee does not apply, and the improvement is the practical benefit of combining two imperfect models whose errors partly offset."],

["p", "For the ATT the picture is different and requires more care. The doubly robust estimate on the logistic score, at −12.6 per cent, is no better than weighting alone at −11.8 per cent, and it is very much worse than the outcome regression alone, which is out by only +0.5 per cent. On the boosted score the doubly robust ATT improves to −4.9 per cent untrimmed and −2.6 per cent trimmed. A reader who took the table at face value would conclude that, for the ATT on these data, the outcome regression is the method to use and the doubly robust estimator adds nothing to it. Section 6.9 explains why that conclusion would be wrong, and the explanation is the most important result in this chapter."],

["h3", "6.8.3  What occupation_group adds"],

["p", "Section 2.4.2 stated in advance what occupation would buy when it entered an outcome model, and the statement was deliberately modest: a standard error about one per cent smaller, with no detectable effect on bias. That is what it delivers. Across the six draws, adding occupation_group to the outcome model reduces the naive standard error of the doubly robust ATE by a ratio of 0.992 and of the doubly robust ATT by 0.993, and the reduction occurs in all six draws in both cases. The bias is unchanged to the first decimal place."],

["p", "The result is small, and it is probably best reported as small. A pure outcome predictor that explains 8 per cent of the variance in untreated earnings, as occupation does, cannot remove much of the variance of an estimate whose uncertainty is dominated by the weights and by the draw. The general point stands, which is that such a covariate belongs in the outcome model and not in the propensity model; the specific benefit in PLIDA-SIM is a consistent and minor gain in precision, and a researcher with a stronger outcome predictor may reasonably expect more."],

["h2", "6.9  Weighting against matching"],

["p", "Section 5.12 anticipated this comparison, stating that the doubly robust estimator improves on regression adjustment of the propensity score matched sample but not on weighting alone or on Mahalanobis matching. Table 6.6 sets out the evidence, for the ATT on the logistic score, with the matching estimates of Chapter 5 recomputed on the same six draws."],

["tab", "6.6", "Weighting against matching for the ATT, logistic score.",
  [4600, 2213, 2213],
  ["Estimator", "Bias", "sd"],
  [
    ["Odds weighting", "−11.8%", "5.4"],
    ["Doubly robust", "−12.6%", "5.8"],
    ["Propensity score matching (Chapter 5)", "−14.4%", "8.5"],
    ["Propensity score matching with regression adjustment", "−15.4%", "7.3"],
    ["Mahalanobis matching within a caliper (Chapter 5)", "+0.7%", "8.6"],
  ],
  "Means across six draws, with the standard deviation across draws. The matched estimates use one-to-one matching without replacement inside a 0.1 standard deviation caliper, as in Table 5.2, and are scored against the true ATT for the treated persons matched.",
  ["l", "r", "r"]
],

["p", "The four estimators that rely on the logistic propensity score cluster between −11.8 and −15.4 per cent, and the differences among them are smaller than the draw-to-draw standard deviation of any one of them. Weighting is somewhat more precise than matching, with a standard deviation of 5.4 against 8.5, which is the benefit of keeping every control; it is not less biased in any dependable sense. The estimator that stands apart is Mahalanobis matching, which Chapter 5 found to be the one procedural choice that clears its own noise, and which relies on the propensity score only to exclude implausible pairs."],

["fig", "6.2", "Where the ATT estimates land. The bias of five estimators of the ATT in each of the six draws, with the mean marked by a bar. The three estimators that rely on the logistic propensity score lie together below zero; Mahalanobis matching and the outcome regression lie around it. Produced by Script 6.2.",
  "figure_6_2_att_estimators.tif"],

["p", "Figure 6.2 shows the pattern draw by draw, and it raises the question that the rest of this section answers. If every method that relies on the propensity score is about twelve per cent low, and a plain linear regression of the outcome is almost exactly right, the obvious inference is that the propensity score is the weak link and the regression the better tool. The inference is natural, and in these data it is wrong."],

["box", "Right for the wrong reason", [
  "A simulated dataset allows a diagnosis that real data never can. Script 6.3 uses the generator's truth file beyond the true effect, which no analysis in this book is otherwise permitted to do, to ask why the propensity score methods are low and why the regression is not. Table 6.7 reports what it finds.",
  "Weighting by the true propensity score, which the generator records, removes the bias entirely: the odds-weighted ATT is out by +0.4 per cent, although with a standard deviation of 11.6 across draws. The weighting method is therefore sound, and the bias comes from the fitted score, which correlates with the true score at only 0.44. The true score depends on two variables that the analysis file does not contain, a pre-programme earnings shock and a latent employability. Adding both to the logistic model reduces the bias from −11.8 to −7.6 per cent, and Chapter 10 shows that nearly all of that reduction is due to employability, since the observed fall in 2016 earnings already stands in for the shock, and that most of the remainder comes from the functional form in which 2016 earnings entered the model.",
  "The regression tells the opposite story. Given the same two unobserved confounders, which should improve it, the regression's estimate moves away from the truth, from +0.5 to +5.4 per cent. Its accuracy with the observed covariates is therefore a cancellation: the omitted confounders bias it downward by about five per cent, its misspecification biases it upward by about five per cent, and the two happen to offset in this dataset. Nothing in the observed data could reveal this, and a different dataset would break the coincidence in either direction.",
  "The lesson is not that the regression is bad or the propensity score good. It is that agreement with the truth, and a fortiori agreement between methods, is not evidence that a method is sound; a method can be right for the wrong reason, and the reason is what transfers to the next dataset. Chapter 10 separates these sources of the bias.",
]],

["tab", "6.7", "Right for the wrong reason: the ATT under Chapter 3's model and under the truth.",
  [5800, 1613, 1613],
  ["Estimator", "Bias", "sd"],
  [
    ["Odds weighting, Chapter 3's propensity score", "−11.8%", "5.4"],
    ["Odds weighting, the true propensity score", "+0.4%", "11.6"],
    ["Odds weighting, both unobserved confounders added", "−7.6%", "5.4"],
    ["Outcome regression, the observed covariates", "+0.5%", "5.2"],
    ["Outcome regression, both unobserved confounders added", "+5.4%", "5.2"],
  ],
  "Means across six draws, with the standard deviation across draws. The true propensity score and the two unobserved confounders, earnings_shock_2016 and u_employability, are read from the generator's truth file by Script 6.3, which is the only use of that file in this chapter beyond scoring. Chapter 3's score correlates with the true score at 0.44.",
  ["l", "r", "r"]
],

["p", "The practical consequence for a real analysis, where the truth file does not exist, is that the choice between these estimators cannot be made by comparing their results. Researchers are sometimes advised to prefer the estimate on which several methods agree, or to regard the doubly robust estimate as a tiebreaker. In these data the three propensity score methods agree with one another and are all wrong in the same direction, and the method that disagrees with them is right by accident. What a real analysis can do is what the earlier chapters recommended: choose the method before seeing the estimate, report the diagnostics that do not involve the outcome, and treat the sensitivity analysis of Chapter 10 as part of the result rather than an appendix to it."],

["h2", "6.10  The naive standard errors"],

["p", "Each weighted estimate in this chapter has been reported with a naive standard error, computed from the estimator's influence function as though the propensity score and, where there is one, the outcome model were known rather than estimated. Chapter 9 develops the correct variance estimators. What this chapter can do is compare the naive standard error with the actual spread of the estimation error across the six draws, which a real analysis cannot observe and a simulation can."],

["tab", "6.8", "Naive standard errors against the spread of the error across draws.",
  [3400, 1900, 1900, 1826],
  ["Estimator", "Naive standard error", "Spread across draws", "Ratio"],
  [
    ["Normalised IPW, ATE", "$625", "$517", "1.21"],
    ["Odds weighting, ATT", "$367", "$347", "1.06"],
    ["Doubly robust, ATE", "$431", "$480", "0.90"],
    ["Doubly robust, ATT", "$267", "$373", "0.72"],
  ],
  "Logistic score, untrimmed, six draws. The naive standard error is the mean across draws; the spread is the standard deviation of the estimate less the truth across draws. A ratio above one means the naive standard error overstates the uncertainty.",
  ["l", "r", "r", "r"]
],

["p", "The ratios in the table run from 0.72 to 1.21, and six draws cannot establish whether any of them differs from one, since a standard deviation estimated from six values is uncertain by about a third of its size. Chapter 9 repeats the comparison over 200 draws (Section 9.4). It finds that the naive standard errors of the two weighting estimators are conservative, by about half for odds weighting and a fifth for the normalised ATE, which is the direction theory predicts, since estimating the propensity score, rather than knowing it, usually reduces the variance of an inverse probability weighted estimator. The doubly robust standard errors are close to right; the apparent understatement for the doubly robust ATT in Table 6.8 arises because its spread across these six draws was, by chance, unusually large."],

["p", "Two cautions attach to the table. The first is the one just stated: Table 6.8 demonstrates the calculation rather than settling the question, and its ratios should not be read to more than one decimal place. The second is that the comparison is with the spread across draws of a data-generating process, which is the right benchmark for a simulation and not one a real analysis can compute; Chapter 9 describes the bootstrap and sandwich estimators that approximate it from a single sample."],

["box", "In the DataLab: weights and the output checker", [
  "A weight is a function of a person's propensity score, and an extreme weight therefore identifies an extreme person. Output checkers are likely to treat the largest weight in a weighted analysis as they would the maximum of any continuous variable, which in many settings means it cannot be released as a single value. Reporting the 99th percentile of the weights and the effective sample size, as Table 6.1 does, conveys what a reader needs to know about the weights without disclosing any individual.",
  "The effective sample size raises a second question. A weighted analysis in which the effective sample is much smaller than the nominal one is, for disclosure purposes, closer to an analysis of the smaller number, and a checker may apply the minimum cell size rules to it. Where the effective control sample falls sharply, as it does when the near-instrument of Section 6.7 is included, this is worth anticipating before the output is submitted rather than after it is returned.",
]],

["h2", "6.11  Is this weighted analysis ready?"],
["h3", "6.11.1  What to record about a weighted analysis"],

["p", "Seven things should be recorded about any weighted analysis before its estimate is carried into Chapter 8 for balance assessment and Chapter 9 for variance estimation. As in Chapter 5, they describe what was constructed, and without them no diagnostic can be interpreted."],

["list", [
  "The estimand, ATE or ATT, and therefore which weights were used.",
  "Whether the estimator was normalised, stated separately from whether the weights were stabilised.",
  "The trimming rule applied to the sample, if any, and how many treated persons and controls it removed.",
  "Whether any weights were capped, and if so the estimate without the cap beside it.",
  "The effective sample size in each condition, and a high percentile of the weights rather than their maximum.",
  "For a doubly robust estimate, the covariates of the outcome model, and which of them do not appear in the propensity model.",
  "Which of the reported standard errors are naive, and that they are to be replaced by the estimates of Chapter 9.",
]],
["h3", "6.11.2  What this chapter cost"],

["p", "The accounting for weighting differs from Chapter 5's in one respect, which is that a single decision dominates it. Capping the weights at the 95th percentile cost 77 percentage points of bias on the ATE, against the uncapped estimate, and no other weighting decision comes close. Among the defensible decisions, trimming the sample was worth 11 percentage points on the logistic score and 29 on the boosted score. Normalisation was worth 3 on the logistic score and 58 on the boosted. The doubly robust estimator was worth 6 on the ATE and nothing on the ATT, and occupation_group was worth a standard error about one per cent smaller."],

["p", "Set against the rest of the book, the ordering is again consistent with the principle that the early decisions are the expensive ones. The score and the trimming rule, which Chapters 3 and 4 settled, determine most of what weighting can achieve; the choice among weighting estimators, which receives most of the attention in the methodological literature, determines comparatively little."],

["h3", "6.11.3  Recommendations"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, we would estimate the ATT by odds weighting on the boosted score of Chapter 3, on a sample trimmed by Chapter 4's variance-minimising rule, with a normalised estimator and no cap. We would report the doubly robust estimate beside it, with occupation_group in the outcome model. These give −2.8 and −2.6 per cent respectively, which are the closest estimates of the ATT that weighting achieves in this chapter. We would not choose between the propensity score methods and the outcome regression by comparing their results, for the reason set out in Section 6.9."],

["p", "The recommendation most worth carrying to other data is the negative one: do not cap the weights. If the weights are extreme, the data are telling the researcher something about overlap, and Chapter 4's remedy of trimming by a stated rule addresses it honestly, whereas capping conceals it at a cost this chapter has shown can exceed the entire effect."],

["h3", "6.11.4  Scripts for this chapter"],

["tab", "6.9", "Scripts for Chapter 6. All available from the companion website.",
  [1100, 3400, 3200, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["6.1", "ch06/06_01_build_weights.py", "Table 6.1; the weights", "20 s"],
    ["6.2", "ch06/06_02_compare_weighting.py", "Tables 6.2 to 6.6 and 6.8; Figures 6.1 and 6.2", "4 min"],
    ["6.3", "ch06/06_03_right_for_the_wrong_reason.py", "Table 6.7", "1 min"],
  ],
  "Scripts 6.2 and 6.3 generate their own draws, the six of Chapter 5, and ignore --datadir for that reason. Script 6.3 reads the truth file beyond the true effect, and its docstring says so.",
  ["l", "l", "l", "r"]
],
["h3", "6.11.5  Further reading"],

["p", "Leite (2017) treats weighting at length, including odds weighting for the ATT and doubly robust estimation, with worked examples in R and a practical emphasis on diagnostics that suits this chapter. Bai and Clark (2019) set weighting within the family of propensity score methods in a way that complements Section 6.2.3's view of matching as a form of weighting."],

["p", "On the question this chapter raises in Section 6.9, readers should return to Basu, Polsky and Manning, whose argument that no single estimator is consistent under all data-generating mechanisms, and that inverse probability weighting in particular is often inefficient, is borne out by Table 6.5. For the variance of weighted estimators and the estimated propensity score, Holmes (2014) leads directly into Chapter 9."],

["h3", "6.11.6  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Reproduce Table 6.3 on PLIDA-SIM B. Does the boosted score, trimmed, remain the best weighting score for both estimands?",
  "Reproduce Table 6.4 on PLIDA-SIM B and find the cap at which the ATE estimate first loses half the effect. Explain, in terms of which persons carry the largest weights, why the ATT is less sensitive to capping than the ATE.",
  "Compute the unnormalised and normalised ATE estimates on the boosted score with and without trimming, and explain why trimming narrows the gap between them.",
  "Add mutual_obligation_status to the propensity model and report the effective control sample under odds weighting. Say what the result implies for a researcher who includes every available predictor of treatment.",
  "Fit the doubly robust ATT with and without occupation_group in the outcome model, and compare the standard error ratio with the one reported in Section 6.8.3.",
  "Estimate the ATT on PLIDA-SIM B by odds weighting, by the outcome regression alone, and by Mahalanobis matching. Without using the truth file, write the paragraph that would justify the estimate you would report.",
]],
["h3", "6.11.7  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Why does a treated person with a low propensity score receive a large weight under inverse probability weighting, and why does the same person receive a weight of one under odds weighting?",
  "Stabilising the weights leaves a normalised estimate unchanged, while normalising can change it by more than half the effect. Explain both facts.",
  "Capping the weights keeps every person and the original estimand, and trimming the sample does neither. Why is capping nonetheless the more damaging of the two in these data?",
  "In what sense is one-to-one matching a form of weighting, and what does the effective sample size of a weighted analysis correspond to under matching?",
  "The doubly robust estimator is consistent if either of its two models is correct. Why does that guarantee say little about its performance in these data?",
  "An outcome regression recovers the ATT almost exactly while three propensity score methods are about twelve per cent low. What would a researcher need to know to decide which to trust, and which of those things could a real analysis observe?",
  "Table 6.8 suggests that the naive standard error of the doubly robust ATT is about a quarter too small, and Chapter 9, with 200 draws, finds that it is not. Why can six draws not settle a question of this kind, and roughly how many would be needed to estimate a standard deviation to within ten per cent?",
]],

];
