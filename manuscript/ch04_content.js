// Chapter 4 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "4  Initial Dataset Trimming"],

["h2", "4.1  Purpose and scope of this chapter"],

["p", "Chapter 3 produced a fitted propensity score and four counts: how many treated persons lie above the highest control score, how many controls lie below the lowest treated score, how many persons have a score above 0.5, and how the score distributes across deciles. This chapter decides what to do about the persons those counts identify."],

["p", "The operation is called trimming, and it consists of removing from the analysis any person whose propensity score falls in a region where the other condition is thinly represented or absent (i.e., where no comparison is possible). The case for it is straightforward: a treated person with no comparable control cannot be matched, and an estimate that includes them is extrapolating rather than comparing. The case against it is equally straightforward, and this chapter gives it a section of its own, because the literature is genuinely divided and a reader who is told only the case for trimming will trim too much."],

["p", "Two things make the decision harder than it first appears. The first is that how much trimming is needed depends on which estimator produced the score, not only on the data; Chapter 3 established that the same covariates fitted by logistic regression and by gradient boosting hand this chapter very different problems. The second is that trimming changes the population the estimate describes, which is the fourth time in this book that a defensible technical step has done so, and the only defence remains the one Chapter 2 identified: knowing it happened and writing it down."],

["p", "By the end of the chapter, readers should be able to assess common support on a fitted score, apply and compare the standard trimming rules, state how far each moves the estimand as well as the estimate, choose a rule appropriate to the quantity being estimated, and report the decision in a way that lets a reader judge it. Readers will also see one rule that sounds entirely reasonable and is catastrophic, which is Section 4.6."],

["h2", "4.2  Common support"],
["h3", "4.2.1  What common support means"],

["p", "Common support is the region of the propensity score in which both conditions are represented. Formally it is the set of score values at which the probability of observing a treated person and the probability of observing a control are both non-zero; practically it is the overlap of the two fitted distributions, and its complement is the set of persons for whom no counterpart exists."],

["p", "The assumption that every person has a non-zero probability of either condition is usually called positivity or overlap, and it is one of the conditions under which a propensity score analysis identifies a causal effect at all. It is worth separating two ways in which it can fail. Structural non-positivity means that some persons could not possibly have been treated, which in this dataset was handled in Chapter 2 by the eligibility rule and is not a trimming question. Practical non-positivity means that some persons could in principle have been treated but that none like them was, which is what trimming addresses and what the score reveals."],

["p", "The distinction matters because the two call for different responses. A structural violation is a definition problem and should be fixed by defining the population, once, at the start. A practical violation is a data problem and can only be managed, either by removing the affected persons or by accepting that the estimate for them rests on extrapolation from the model rather than on comparison with anybody."],

["p", "In PLIDA-SIM both kinds are present and were handled at different points. The 7,425 persons excluded by the eligibility rule of Section 2.2.4 are a structural violation: they were never candidates for referral, so no propensity model can sensibly assign them a probability of treatment and no trimming rule should be asked to find them. The persons this chapter removes are a practical violation within the eligible population, and the difference between the two is the difference between a definition and a measurement."],
["h3", "4.2.2  Assessing overlap on a fitted score"],

["p", "Four counts and one picture are usually enough, and we take them in turn. The counts are those Chapter 3 produced, and Table 4.1 carries them forward for both scores so that the difference between the two is visible in one place."],

["tab", "4.1", "Overlap under the two scores of Chapter 3, on the eligible population.",
  [3300, 1500, 1500, 2626],
  ["", "Logistic", "Boosting", "What it bears on"],
  [
    ["Score range", "0.022 to 0.573", "0.016 to 0.896", "Whether any weight can become extreme"],
    ["Treated above the highest control", "5", "39", "Treated persons with no counterpart"],
    ["Controls below the lowest treated", "17", "228", "Controls with no counterpart"],
    ["Persons with a score above 0.5", "14", "106", "The thin end of the distribution"],
    ["Persons with a score above 0.7", "0", "16", "Where weights begin to misbehave"],
    ["Smallest decile treated cell", "160 of 4,258", "110 of 4,258", "Whether any stratum is unusable"],
  ],
  "Primary dataset, seed 20260808, 42,575 eligible persons. The two scores use the same covariates and differ only in estimator.",
  ["l", "r", "r", "l"]
],

["p", "Read across the table and the practical conclusion is immediate. Under the logistic score the overlap problem is small: five treated persons out of 4,867 have no counterpart, and nobody at all scores above 0.7. Under the boosted score the same quantities are eight times larger, and sixteen persons sit in the region where an inverse probability weight starts to behave badly. The data are identical. The estimator is not."],

["frag", [
  "tr, ct = ps[D == 1], ps[D == 0]",
  "",
  "print(f\"treated above the highest control  {(tr > ct.max()).sum():,}\")",
  "print(f\"controls below the lowest treated  {(ct < tr.min()).sum():,}\")",
  "print(f\"common support region              {max(tr.min(), ct.min()):.3f}\"",
  "      f\" to {min(tr.max(), ct.max()):.3f}\")",
], "Fragment 4.1  The common support region and who falls outside it. Full script: ch04/04_01_assess_overlap.py"],

["p", "The picture is a pair of histograms on a common axis, one per condition, which Chapter 3 produced as Figure 3.2 and which should be drawn on a logarithmic count scale. On a linear scale a group of five persons is invisible beside a mode of four thousand, and the whole point of the figure is the handful of persons in the tail."],
["h3", "4.2.3  How large is the problem here?"],

["p", "Small, on the logistic score, and we think that answer deserves to be stated plainly rather than buried, because a chapter about trimming has an obvious incentive to find trimming necessary. Restricting the logistic score to the strict common support region removes 22 persons of 42,575, or one in two thousand, and moves the estimated average treatment effect by under two percentage points."],

["p", "On the boosted score the same restriction removes 267 persons and moves the estimate by thirteen percentage points. A reader who followed Chapter 3 with logistic regression may reasonably conclude that this chapter's machinery is not needed for their analysis, and should record that they checked rather than that they trimmed. A reader who used a flexible estimator will find the rest of the chapter necessary."],

["h2", "4.3  Seven trimming rules"],
["h3", "4.3.1  The rules in common use"],

["p", "Trimming rules differ in what they take as the boundary of the acceptable region. Seven are in common use, and we apply all seven here, and they fall into three families."],

["p", "The first family defines the region from the data. The strict common support rule keeps persons whose score lies between the highest of the two minima and the lowest of the two maxima, which is the smallest region in which both conditions are certainly present. A softer version uses the first and ninety-ninth percentiles of the treated distribution instead of its extremes, on the grounds that a single extreme observation should not set the boundary for everybody."],

["p", "The second family imposes fixed thresholds, most often keeping scores between 0.05 and 0.95 or between 0.10 and 0.90. These generally have the advantage of being stated in advance and the disadvantage of being arbitrary: a threshold of 0.10 removes almost nobody in a setting where treatment is common and more than half the sample in a setting where it is rare, and PLIDA-SIM is the second kind of setting."],

["p", "The third family derives the boundary from a criterion. The best known keeps scores in a symmetric interval chosen to minimise the variance of the estimator, which yields an explicit rule rather than a convention and adapts to the data. Finally there are asymmetric rules, which trim one condition and not the other, on the reasoning that an estimator of the effect on the treated needs comparable controls but does not need comparable treated persons."],

["frag", [
  "gamma = 1.0 / (ps * (1 - ps))            # the variance criterion",
  "g = np.sort(gamma)",
  "meets = g >= 2 * np.cumsum(g) / np.arange(1, len(g) + 1)",
  "lam = g[np.argmax(meets)] if meets.any() else None",
  "",
  "alpha = 0.0 if lam is None or lam <= 4 else (1 - np.sqrt(1 - 4 / lam)) / 2",
  "keep = (ps >= alpha) & (ps <= 1 - alpha)",
], "Fragment 4.2  Variance-minimising trimming, which chooses its own threshold. Full script: ch04/04_02_trimming_rules.py"],
["h3", "4.3.2  What each rule removes"],

["p", "Table 4.2 applies all seven to the logistic score and reports what each one takes out. The counts are from the primary dataset, so that they describe the same sample as Table 4.5; the rules that use a percentile remove slightly different numbers in other draws."],

["tab", "4.2", "What each trimming rule removes from the logistic score.",
  [3400, 1300, 1300, 1300, 1826],
  ["Rule", "Removed", "Treated", "Controls", "Share of the eligible"],
  [
    ["0  No trimming", "0", "0", "0", "0.0%"],
    ["1  Strict common support", "22", "5", "17", "0.1%"],
    ["2  1st to 99th percentile of treated", "1,794", "98", "1,696", "4.2%"],
    ["3  Fixed, 0.05 to 0.95", "4,053", "151", "3,902", "9.5%"],
    ["4  Fixed, 0.10 to 0.90", "22,397", "1,501", "20,896", "52.6%"],
    ["5  Variance-minimising (alpha = 0.044)", "2,303", "75", "2,228", "5.4%"],
    ["6  Asymmetric, below the lowest treated", "17", "0", "17", "0.0%"],
    ["7  Asymmetric, below the treated 5th percentile", "5,762", "0", "5,762", "13.5%"],
  ],
  "Primary dataset, seed 20260808, logistic score, 42,575 eligible persons. Rules 6 and 7 remove controls only, which is why their treated column is zero. Table 4.5 describes the persons rule 3 removes.",
  ["l", "r", "r", "r", "r"]
],

["p", "Two features of the table are worth pausing on before any bias is calculated. The first is the enormous range: the rules span from removing one person in a thousand to removing more than half the sample. They are all described in the literature as trimming, and a report that says only that the sample was trimmed has said almost nothing."],

["p", "The second is that the fixed 0.10 to 0.90 rule removes 52.6 per cent of the eligible population. That is not a trimming rule in any useful sense; it is a redefinition of the study population, and Section 4.4.3 shows what it does to the quantity being estimated. The rule is included here because it is in common use and because readers will meet it."],

["frag", [
  "RULES = {                                   # declared before anything is fitted",
  "    \"strict common support\": lambda e, d: (e >= max(e[d==1].min(), e[d==0].min()))",
  "                                          & (e <= min(e[d==1].max(), e[d==0].max())),",
  "    \"1st-99th of treated\":   lambda e, d: (e >= np.percentile(e[d==1], 1))",
  "                                          & (e <= np.percentile(e[d==1], 99)),",
  "    \"fixed 0.05-0.95\":       lambda e, d: (e >= 0.05) & (e <= 0.95),",
  "}",
  "keep = RULES[CHOSEN_RULE](ps, D)            # CHOSEN_RULE fixed in advance",
], "Fragment 4.3  The rules as named functions, chosen before the estimate is seen. Full script: ch04/04_02_trimming_rules.py"],

["h2", "4.4  What trimming buys, and what it costs"],
["h3", "4.4.1  Bias"],

["p", "Table 4.3 is the central exhibit of this chapter, and we read it in three passes. It reports, for each rule and for each of the two scores, the bias of the estimated average treatment effect (ATE) and of the estimated effect on the treated (ATT), both scored against the truth for the sample that the rule retains."],

["tab", "4.3", "Bias under each trimming rule, by score and by estimand.",
  [3400, 1250, 1250, 1250, 1250],
  ["Rule", "ATE logit", "ATT logit", "ATE boost", "ATT boost"],
  [
    ["0  No trimming", "\u221221.1%", "\u221210.4%", "\u221229.1%", "\u221211.0%"],
    ["1  Strict common support", "\u221219.3%", "\u22129.9%", "\u221216.2%", "\u22127.1%"],
    ["2  1st to 99th percentile", "\u221211.9%", "\u22127.8%", "+3.7%", "+0.0%"],
    ["3  Fixed, 0.05 to 0.95", "\u22129.2%", "\u22126.7%", "+5.2%", "\u22120.1%"],
    ["4  Fixed, 0.10 to 0.90", "\u22123.3%", "\u22123.7%", "+9.8%", "+7.9%"],
    ["5  Variance-minimising", "\u22129.1%", "\u22126.8%", "+4.5%", "\u22121.3%"],
    ["6  Asymmetric, below lowest treated", "\u221219.4%", "\u221210.1%", "\u221216.7%", "\u22128.8%"],
    ["7  Asymmetric, treated 5th percentile", "+66.2%", "+23.7%", "+80.6%", "+30.3%"],
  ],
  "Means across five independent draws. The ATE is estimated by inverse probability weighting and the ATT by odds weighting, which Chapter 6 develops. Each is scored against the true effect for the persons the rule retains, not against the effect for the original sample. Table 4.2 reports how many persons each rule removes.",
  ["l", "r", "r", "r", "r"]
],

["p", "The first result is the one Chapter 3 predicted. Trimming does most for the score that needs it most: the boosted ATT moves from \u221211.0 per cent untrimmed to essentially exact under three of the rules, whereas the logistic estimate improves from \u221210.4 to \u22126.7 per cent and no further without removing half the sample. A reader who used a flexible estimator has more to gain here than a reader who did not, which is the same finding from the other side."],

["p", "The second is that the variance-minimising rule performs about as well as the best fixed threshold while removing a third to a half as many persons. It also requires no choice, which removes one opportunity for a specification search. On these data it is the rule we would recommend, and Section 4.7 says so."],

["p", "The third is row 7, which is the subject of Section 4.6."],
["h3", "4.4.2  Precision"],

["p", "The argument for trimming is usually made in terms of bias, but its more reliable benefit is probably precision. Persons with extreme propensity scores (e.g., those the boosted model places above 0.9) carry extreme weights, extreme weights inflate the variance of any weighted estimator, and removing them shrinks it. Table 4.4 reports the effect on the standard error."],

["tab", "4.4", "What trimming does to precision, logistic score, one draw.",
  [3200, 1500, 1500, 1500, 1826],
  ["Rule", "Retained", "SE of the ATE", "SE of the ATT", "Change in SE(ATE)"],
  [
    ["0  No trimming", "42,575", "606", "366", "\u2014"],
    ["2  1st to 99th percentile", "40,781", "533", "356", "\u221212%"],
    ["3  Fixed, 0.05 to 0.95", "38,522", "464", "337", "\u221223%"],
    ["4  Fixed, 0.10 to 0.90", "20,178", "364", "310", "\u221240%"],
  ],
  "Primary dataset, seed 20260808. The standard errors fall as the sample shrinks, which is the opposite of the usual relationship and is the point: the persons removed were contributing variance rather than information.",
  ["l", "r", "r", "r", "r"]
],

["p", "The standard error of the ATE falls by 40 per cent while the sample falls by 53 per cent, which is worth stating carefully because it inverts the usual intuition. Removing half a sample normally costs precision. Here it buys precision, because the persons removed were carrying weights large enough that their contribution to the variance exceeded their contribution to the information. That is a genuine benefit and it does not depend on any of the contested claims about bias."],
["h3", "4.4.3  The estimand, for the fourth time"],

["p", "The bias figures in Table 4.3 are scored against the truth for the sample each rule retains, and that phrase carries the weight of this section. Trimming does not only change the estimate; it changes what the estimate is of."],

["tab", "4.5", "Who the 0.05 to 0.95 rule removes, logistic score.",
  [2700, 1700, 1700, 3226],
  ["", "Retained", "Removed", "Reading"],
  [
    ["Persons", "38,522", "4,053", "9.5 per cent of the eligible population"],
    ["Mean age", "39.7", "47.4", "The removed are nearly eight years older"],
    ["Mean fortnights on payment", "12.8", "2.9", "They are barely on income support"],
    ["Mean 2016 earnings", "$28,187", "$72,642", "They earn two and a half times as much"],
    ["Mean SEIFA decile", "5.9", "8.1", "They live in less disadvantaged areas"],
    ["Commenced the programme", "12.2%", "3.7%", "They rarely participate"],
    ["True average effect", "$5,701", "$2,663", "The programme helps them far less"],
  ],
  "Primary dataset, seed 20260808. Trimming removes the persons least likely to be treated, who in these data are also the persons the programme benefits least.",
  ["l", "r", "r", "l"]
],

["p", "The persons we remove are older, better paid, barely on income support, and rarely participate. None of that is surprising, since a low propensity score means precisely that such a person was unlikely to be referred. What matters is the last row: their true effect is $2,663 against $5,701 for those retained, so removing them raises the average effect in the remaining sample by a quarter."],

["p", "The consequence is that part of the improvement in Table 4.3 is not the estimator getting closer to the truth. It is the truth moving towards the estimate. Under the 0.10 to 0.90 rule the true average treatment effect for the retained sample is $6,900 against $5,417 for the full eligible population, both averaged over the five draws, a shift of 27 per cent, and the apparent reduction in bias from \u221221.1 to \u22123.3 per cent has to be read against that."],

["frag", [
  "# Report the shift in the estimand, not only the shift in the estimate.",
  "print(f\"removed            {(~keep).sum():,} of {len(keep):,}\"",
  "      f\"  ({100 * (~keep).mean():.1f}%)\")",
  "print(f\"treated removed    {((~keep) & (D == 1)).sum():,}\")",
  "for col in DESCRIBE:                    # age, earnings, fortnights, SEIFA",
  "    print(f\"  {col:22s} kept {X[col][keep].mean():9.1f}\"",
  "          f\"   removed {X[col][~keep].mean():9.1f}\")",
], "Fragment 4.4  What every trimmed analysis should report. Full script: ch04/04_04_who_is_removed.py"],

["p", "This is the fourth appearance of the pattern Chapter 2 named in Section 2.5.2. The inner join found it, complete-case analysis found it, attrition arrived at it from a direction the analyst does not control, and trimming reaches it deliberately. Only the last of the four is a choice, which makes it the one where the reporting obligation is clearest: a trimmed analysis should state the rule, the number removed, how the removed differ from the retained, and which population the estimate now describes."],

["fig", "4.1", "What trimming buys, against what it removes. (a) Bias of the estimated average treatment effect against the share of the eligible population removed, for the seven rules of Table 4.2, under each of the two scores of Chapter 3. (b) The same for the effect on the treated. In both panels the horizontal line is zero bias and the rules are labelled by their number; rule 7 is omitted from the visible range and is the subject of Section 4.6. Produced by Script 4.3.",
  "figure_4_1_trimming_tradeoff.tif"],

["h2", "4.5  Trimming for the average effect is not trimming for the effect on the treated"],

["p", "A single trimming rule is usually applied to an analysis and reported once, as though it were a property of the data. Table 4.3 shows that it is not. The rule that is right for one estimand can be wrong for the other, and the reason is structural rather than incidental."],

["p", "Consider the ATT. The population of interest is the treated, so every treated person retained is a person the estimand is about, and a rule that removes treated persons narrows the estimand directly. Controls, by contrast, are present only as counterparts, so removing controls with no treated analogue costs nothing except sample size. Trimming for the ATT should therefore be conservative about treated persons and can be liberal about controls."],

["p", "For the ATE the population of interest is everybody, so removing anyone narrows the estimand, and the case for removing persons in the tails rests entirely on the extrapolation they would otherwise require. The calculation is different and so is the answer."],

["p", "The boosted score shows the divergence. The ATT is estimated essentially exactly at the first to ninety-ninth percentile rule and at the 0.05 to 0.95 rule, and then deteriorates to +7.9 per cent at 0.10 to 0.90, because that rule begins removing high-propensity treated persons, who are the estimand. The ATE over the same three rules moves from +3.7 to +5.2 to +9.8 per cent, worsening throughout. Trimming further does not converge on the right answer; past a point it overshoots, and it overshoots first for the estimand that includes the persons being removed."],

["box", "Trap: one rule, two estimands", [
  "An analysis that reports both an average treatment effect and an effect on the treated, trimmed once at a threshold chosen for whichever was computed first, will be wrong about at least one of them. On the boosted score, the 0.10 to 0.90 rule leaves the ATE out by 9.8 per cent and the ATT out by 7.9 per cent, where a milder rule leaves the second essentially exact.",
  "The practical response is to trim separately for each estimand, to report the rule alongside each estimate rather than once in a methods section, and to treat a change of estimand as a reason to revisit the trimming decision rather than to carry it over.",
]],

["h2", "4.6  Two rules that sound alike"],

["p", "Rules 6 and 7 of Table 4.2 are both asymmetric: both remove controls and no treated persons, on the reasoning of Section 4.5 that an estimator of the effect on the treated needs comparable controls but not comparable treated. Rule 6 removes controls whose score falls below the lowest treated score. Rule 7 removes controls whose score falls below the fifth percentile of the treated distribution. The descriptions differ by a few words."],

["p", "Rule 6 removes 17 controls and changes the estimate by less than half a percentage point. Rule 7 removes 5,762 controls and produces a bias of +66.2 per cent on the ATE and +23.7 per cent on the ATT, the largest errors anywhere in this chapter and the wrong sign as well as the wrong magnitude."],

["p", "The mechanism is worth following because it generalises. Controls with low propensity scores are, in these data, typically high earners (e.g., the $72,642 mean of Table 4.5) who were never likely to be referred. Under odds weighting they receive small weights, so they contribute little; but they are numerous, and collectively they anchor the control mean. Removing 5,762 of them raises the weighted control mean sharply, and since the estimate is the difference between the treated mean and the control mean, the estimate rises with it."],

["p", "The general lesson we would draw is that a trimming rule should usually be defined by where the other condition is absent, not by a quantile of the condition being retained. The lowest treated score is a fact about overlap. The fifth percentile of the treated distribution is a fact about the treated alone, and using it to remove controls discards comparison cases that were doing useful work. Two rules that read almost identically differ in that one is a statement about the region where comparison is possible and the other is not."],

["h2", "4.7  The argument against trimming"],

["p", "Everything we have written so far assumes that trimming is worth doing. That assumption is contested, and a reader who meets only the case for it will trim too readily, so this section puts the other side as its proponents put it."],

["p", "The case for respecting common support is the one the matching tradition makes, and Lechner sets out the problem clearly: estimating a treatment effect for persons who have no counterpart is extrapolation from the model rather than comparison with anybody, and presenting it as a comparison misrepresents what was done. Lechner does not conclude that such persons should simply be discarded; he proposes bounds that use them, so that a reader can see how far the answer depends on the region the data cannot reach. On this view the region of common support is not a nuisance to be minimised but the boundary of what the data can answer, and an estimate that respects it is honest about its own reach."],

["p", "The case against is put by Basu, Polsky and Manning, and it is aimed at applied researchers rather than at theoreticians. The persons trimmed away are not a random subset, as Table 4.5 demonstrates, so the estimate that survives describes a population nobody chose and that no policy question was asked about; in their view some extrapolation is often necessary, and an estimate presented without it can mislead. Two further objections are commonly added, and we share them. The first is that a trimming threshold is usually arbitrary, which is the motivation Crump and colleagues give for the variance-minimising rule, and a result that moves with an arbitrary choice has not been established. The second, and most uncomfortable, is that trimming can be applied repeatedly until the estimate looks reasonable, and nothing in the output distinguishes principled trimming from that."],

["p", "Both positions may be correct about different things, and the disagreement is not really about statistics. It is about which error is worse: an estimate that extrapolates beyond the data, or an estimate that is about a population nobody asked about. Chapter 2 encountered the same trade in the argument over listwise deletion, and resolved it on the same principle as this chapter: report which population the estimate describes."],

["p", "Our recommendation is therefore a narrow one. Use the variance-minimising rule, which is not arbitrary and does not require a threshold to be chosen; report the untrimmed estimate alongside the trimmed one, so that a reader can see what the rule did; describe the persons removed, in the form of Table 4.5; and never adjust the rule after seeing the estimate. The last of these is the one that matters most and the only one that cannot be verified by a reader, which is why it should be recorded in advance."],

["frag", [
  "trimmed   = estimate(ps[keep], D[keep], y[keep])",
  "untrimmed = estimate(ps,       D,       y)",
  "",
  "print(f\"untrimmed  {untrimmed:>9,.0f}   n {len(D):,}\")",
  "print(f\"trimmed    {trimmed:>9,.0f}   n {keep.sum():,}\"",
  "      f\"   rule: {CHOSEN_RULE}\")",
], "Fragment 4.5  Both estimates, always reported together. Full script: ch04/04_03_compare_rules.py"],

["p", "Reporting both estimates is the single practice that makes the rest checkable. A reader who sees only the trimmed figure cannot tell whether the rule moved the estimate by half a percentage point or by thirty, and therefore cannot tell whether the trimming decision was consequential enough to deserve scrutiny. Where the two figures are close, as they are on the logistic score here, reporting both also saves the analyst from an argument they do not need to have."],

["box", "In the DataLab: trimming and the disclosure rules", [
  "Trimming interacts awkwardly with output checking. A trimmed analysis reports a sample size, and the difference between the trimmed and untrimmed counts can in a small cell reveal how many persons occupy a narrow region of the score, which is the kind of residual disclosure the rules are designed to prevent. Analyses that report several trimming thresholds in one table are refused more often than those that report one.",
  "The practical approach is to decide the rule before requesting output, to report the retained count rather than the removed count, and to round both. Where a sensitivity analysis across thresholds is genuinely needed, request it as a single table with rounded counts rather than as a series of separate outputs.",
]],

["h2", "4.8  Is this sample ready to analyse?"],
["h3", "4.8.1  What to record about a trimmed sample"],

["p", "Five things should be true and documented before a trimmed sample is carried into Chapter 5. Each corresponds to a decision made somewhere in this chapter."],

["list", [
  "The rule was chosen before the estimate was seen, and is stated in a form another analyst could apply to the same data and reproduce.",
  "The untrimmed estimate is reported alongside the trimmed one, so that a reader can see the size and direction of what the rule did.",
  "The number of persons removed is reported separately for the treated and the controls, since a rule that removes treated persons changes the estimand of an effect on the treated and a rule that removes only controls does not.",
  "The removed persons are described on the covariates, in the form of Table 4.5, and the description is reported rather than held in the analyst's notes.",
  "Where more than one estimand is reported, the trimming decision is revisited for each, and the rule is stated beside each estimate rather than once in a methods section.",
]],
["h3", "4.8.2  What this chapter cost"],

["p", "The accounting we can offer here is smaller than Chapter 2's and sharper than Chapter 3's. Of the seven rules examined, one is catastrophic, one removes more than half the eligible population and redefines the study, two do essentially nothing on the score we recommend, and three land within a few percentage points of each other. The distance between the best and worst defensible choice is about six percentage points of bias on the logistic score and about fourteen on the boosted one."],

["p", "Set against the rest of the book, trimming is a second-order decision made to look first-order by the boosted score. On the logistic score the entire chapter moves the estimate by less than the choice of missing-data strategy moved it in Chapter 2, and by much less than the choice of propensity model moved it in Chapter 3. That ordering is worth carrying forward: the preparation decisions dominate, the estimation decisions matter, and the adjustments made afterwards are mostly repairs to damage done earlier."],
["h3", "4.8.3  Scripts for this chapter"],

["tab", "4.6", "Scripts for Chapter 4. All available from the companion website.",
  [1100, 3400, 3200, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["4.1", "ch04/04_01_assess_overlap.py", "Table 4.1; the common support region", "15 s"],
    ["4.2", "ch04/04_02_trimming_rules.py", "Table 4.2; the seven trimmed samples", "20 s"],
    ["4.3", "ch04/04_03_compare_rules.py", "Tables 4.3 and 4.4; Figure 4.1", "5 min"],
    ["4.4", "ch04/04_04_who_is_removed.py", "Table 4.5", "15 s"],
  ],
  "Script 4.3 generates its own draws, because a single draw cannot separate the differences between rules from sampling variability, and it ignores --datadir for that reason.",
  ["l", "l", "l", "r"]
],
["h3", "4.8.4  Further reading"],

["p", "The case for respecting common support is made in the matching literature and is set out clearly by Lechner, whose bounds use the persons off support rather than discarding them; the case against restricting an analysis to common support is made by Basu, Polsky and Manning, whose discussion of it is short and worth reading in full before adopting any rule. The variance-minimising rule used here is due to Crump and colleagues, and the derivation is more approachable than its reputation suggests. Leite (2017) covers the practical mechanics in R, in the chapters on estimating the score and on weighting, including the interaction between trimming and weighting that Chapter 6 takes up."],

["p", "For the asymmetric rules, the literature is thinner than the topic deserves, and readers should treat published rules with the caution Section 4.6 illustrates: check what a rule removes on their own data before adopting it, since a rule that is sensible in a setting where treatment is common may be destructive where it is rare."],
["h3", "4.8.5  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Fit the logistic score on PLIDA-SIM B and apply all seven rules of Table 4.2. Report how many persons each removes, and say whether the ordering matches the primary dataset.",
  "Reproduce Table 4.5 for the variance-minimising rule rather than the 0.05 to 0.95 rule. Are the persons it removes the same kind of persons, and is the shift in the true effect larger or smaller?",
  "Apply rule 7 to the boosted score and confirm the direction of the failure. Then explain, in two sentences and without running anything further, why removing low-propensity controls raises the estimate.",
  "Trim once for the average treatment effect and once for the effect on the treated, choosing each threshold on its own merits, and report how far the two thresholds differ.",
  "Report the untrimmed and trimmed estimates together, as Section 4.8.1 requires, and write the two-sentence description of the removed persons that would accompany them in a report.",
]],
["h3", "4.8.6  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Distinguish structural from practical non-positivity, and say which one trimming is for and which one the eligibility rule of Chapter 2 was for.",
  "Trimming at 0.10 to 0.90 reduced the bias of the average treatment effect from \u221221.1 to \u22123.3 per cent. Explain why this is not straightforwardly an improvement.",
  "The standard error falls as the trimmed sample shrinks, which inverts the usual relationship between sample size and precision. Why?",
  "Why should trimming for the effect on the treated be conservative about treated persons and liberal about controls, while trimming for the average effect cannot be either?",
  "Rules 6 and 7 differ by a few words of description and by 90 percentage points of bias. What distinguishes them, and what general principle does the difference suggest for defining a trimming rule?",
  "Section 4.7 notes that trimming can be applied until the estimate looks reasonable. What single reporting practice makes that objection checkable by a reader?",
  "Under the logistic score, trimming changes very little; under the boosted score it changes a great deal. Both scores were fitted to the same covariates on the same persons. What does that imply about where the decision to trim is actually made?",
]],

];
