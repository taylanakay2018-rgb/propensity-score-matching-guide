// Chapter 5 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "5  Creating Balanced Datasets with Propensity Score Matching"],

["h2", "5.1  Purpose and scope of this chapter"],

["p", "Chapters 2 to 4 built an analysis file, fitted a propensity score to it, and decided which persons lie in the region where comparison is possible. This chapter uses the score to construct a matched dataset: a set of treated persons paired with controls who resemble them, on which the comparison the study exists to make can finally be drawn."],

["p", "Matching is the most widely used of the propensity score methods and the one readers are most likely to have seen applied. It is also the one surrounded by the largest number of tuning decisions, and this chapter's central finding concerns which of them matter. We will construct nine matched datasets from the same score, differing in the distance measure, the caliper, whether controls are reused, and how many controls each treated person receives, and we will score all nine against the known effect across six independent draws of the data."],

["p", "The result is not the one the literature's emphasis would predict. The caliper, which receives more attention in applied papers than any other matching parameter, moves the estimate by less than a fifth of a percentage point across the full range from 0.02 to 0.2 standard deviations, while the draw-to-draw standard deviation is 8.5 percentage points. The distance measure, which is usually chosen by default and rarely discussed, roughly halves the mean absolute bias across twelve draws, from 12.4 per cent to 5.8 per cent."],

["p", "By the end of the chapter, readers should be able to construct a matched dataset with each of the common procedures, report what each one did to the sample, recognise which of the available tuning decisions are worth spending time on, and hand a matched dataset to Chapter 8 for balance assessment and to Chapter 9 for variance estimation. Readers will also see two matched samples that pass every balance diagnostic in ordinary use while producing estimates fifteen points apart, which is the subject of Section 5.15 and the reason Chapter 8 exists."],

["p", "One scoping note. This chapter constructs matched datasets and reports what they recover, but it is not the chapter on estimating the treatment effect properly; the standard errors quoted here are the naive ones, and Chapter 9 explains why they are wrong and what to use instead. Where an estimate is reported, it is the average treatment effect on the treated (ATT), and it is reported as a way of scoring a construction rather than as a result."],

["h2", "5.2  What matching does"],
["h3", "5.2.1  Matching is a design step"],

["p", "The most useful way to think about matching is that it is part of the design of the study rather than part of the analysis of it. A randomised trial achieves comparability by assigning treatment independently of everything else; matching attempts to reconstruct comparability after the fact, by selecting from the available controls a subset that resembles the treated on the covariates that matter."],

["p", "The practical consequence is the one Chapter 2 introduced and this chapter enforces: the outcome takes no part in it. Every decision in this chapter, including all nine variants, is made and evaluated without reference to the 2019 earnings that the study is about. That is what makes the procedure honest, since a matched sample chosen to produce a particular estimate is not a design at all, and it is also what makes the diagnostics of Chapter 8 meaningful."],

["p", "This is worth stating because the discipline is easy to lose. The outcome sits in the analysis file, a single line of code will produce the estimate at any point, and there is no technical obstacle to looking. The obstacle has to be procedural, and the recommendation of Section 2.6.6 holds here: keep the outcome in a separate file and join it only in the final script."],
["h3", "5.2.2  The matched sample is a constructed dataset"],

["p", "Matching produces a new dataset, and it is worth being explicit about what that dataset contains, because several of this chapter's results follow from it rather than from anything statistical."],

["p", "A one-to-one matched sample without replacement contains each matched treated person once and each matched control once. A sample constructed with replacement contains each matched treated person once and each selected control as many times as it was chosen, so the number of rows exceeds the number of distinct persons. A one-to-three sample contains each treated person once and three controls for each. In every case the treated persons who could not be matched are absent, which changes the population the estimate describes, and Section 5.11 measures by how much."],

["p", "These are different datasets, and the differences show up in every later chapter. Chapter 8 assesses balance on whichever of them is produced here; Chapter 9 has to account for how the matched sample was built, including any control that appears more than once. The matched dataset is therefore the interface between this chapter and the rest of the book, and the recommendation at the end of the chapter is as much about recording what was constructed as about which construction to choose."],

["h2", "5.3  The choices in a matching procedure"],

["p", "Five decisions have to be made before any matching can run, and Table 5.1 sets them out with the options in common use. They are presented together because the literature tends to treat them separately, and because the main finding of this chapter is about their relative importance rather than about any one of them."],

["tab", "5.1", "The five decisions in a matching procedure.",
  [2200, 3400, 3326],
  ["Decision", "Options in common use", "What it controls"],
  [
    ["Distance", "Propensity score; linear predictor of the score; Mahalanobis distance on selected covariates; Mahalanobis within a propensity caliper", "What \u201csimilar\u201d means"],
    ["Caliper", "None; 0.2, 0.1, 0.05 or 0.02 standard deviations of the linear predictor", "How close a match has to be before it is accepted"],
    ["Replacement", "Without replacement, each control used once; with replacement, controls reusable", "Whether the best available control can serve more than one treated person"],
    ["Ratio", "1:1; 1:2; 1:3; variable", "How many controls each treated person receives"],
    ["Order", "Greedy, usually highest propensity first; optimal, minimising total distance", "Which treated person gets first choice of the controls"],
  ],
  "The five are not independent: a tight caliper without replacement leaves more treated persons unmatched than the same caliper with replacement, and a higher ratio needs a looser caliper to fill.",
  ["l", "l", "l"]
],
["h3", "5.3.1  The distance"],

["p", "The distance decides what similar means, and it is the decision most often made by default. Matching on the propensity score itself treats two persons as similar when they had the same estimated probability of treatment, which is the property Chapter 3 established as sufficient for balance in principle. Matching on the linear predictor rather than the probability is usually preferred, because the score is compressed near 0 and 1 and a difference of 0.01 means something different at the middle of the range than at the end."],

["p", "The alternative is to match on the covariates directly, using the Mahalanobis distance, which measures separation in covariate space after accounting for the scale and correlation of the covariates. This can be applied to all covariates or, more usefully, to the few that carry most of the confounding, and it is commonly combined with a propensity caliper so that no pair is accepted whose treatment probabilities were very different. Section 5.6 shows what that combination is worth here, and the answer is a great deal more than we expected."],
["h3", "5.3.2  The caliper"],

["p", "The caliper is the maximum distance at which a pair will be accepted, usually expressed in standard deviations of the linear predictor. A common recommendation is 0.2 standard deviations, and tighter values of 0.1 or 0.05 appear frequently. The reasoning is that a loose caliper accepts poor matches and therefore leaves bias in the comparison, while a tight caliper rejects them and leaves treated persons unmatched instead."],

["p", "That reasoning is sound and the effect it describes is real. Section 5.5 measures how large it is in these data, and the answer is that it is smaller than almost anyone would guess."],
["h3", "5.3.3  With or without replacement"],

["p", "Matching without replacement uses each control at most once, which produces a matched sample of distinct persons and a straightforward interpretation. Matching with replacement allows the same control to serve several treated persons, which improves the quality of individual matches, particularly where good controls are scarce, and complicates everything downstream."],

["p", "The complication is that the matched sample now contains repeated observations, so the pairs are not independent, and a standard error computed as though they were ignores the dependence; where reuse is heavy, it will be too small. Chapter 9 measures how much this matters here, and Section 5.10 measures how much reuse actually occurs here so that the later chapter has something concrete to work with."],
["h3", "5.3.4  How many controls per treated person"],

["p", "One-to-one matching is the default, but nothing requires it. Where controls are plentiful, matching each treated person to two or three of them uses more of the available information and should reduce the variance of the estimate, at the cost of accepting some matches that are worse than the best available. In PLIDA-SIM the control group is roughly eight times the size of the treated group, so the arithmetic is comfortable, and Section 5.7 measures the trade."],
["h3", "5.3.5  The order in which pairs are formed"],

["p", "Greedy matching takes the treated persons in some order and gives each the closest available control, so the order matters: a treated person matched early gets a better control than one matched late. Sorting by descending propensity score is the usual convention, on the grounds that the hardest persons to match should choose first. Optimal matching instead minimises the total distance across all pairs simultaneously, which is a solvable assignment problem and is available in several packages."],

["p", "This chapter uses greedy matching in descending propensity order throughout, except in Section 5.8, which compares it with the optimal solution; Exercise 5.4 asks readers to vary the order itself. We should record in advance that both comparisons belong to the same family as the caliper comparison of Section 5.5, and readers may wish to predict the results before seeing them."],

["frag", [
  "order = np.argsort(-ps[treated])       # hardest to match choose first",
  "",
  "for t in treated[order]:",
  "    d = np.abs(lp[available] - lp[t])  # distance on the linear predictor",
  "    j = d.argmin()",
  "    if d[j] <= caliper * lp.std():     # accept only inside the caliper",
  "        pairs.append((t, available[j]))",
  "        available = np.delete(available, j)      # without replacement",
], "Fragment 5.1  Greedy one-to-one matching. Full script: ch05/05_02_match_variants.py"],
["h3", "5.3.6  Putting the five together"],

["p", "With the five decisions made, a matched sample is four lines of work and one line of checking. The sequence below is the one Script 5.1 runs, and it is worth walking through because the order matters: the score is fitted once, the trimming rule of Chapter 4 is applied to it, the matching is performed on what survives, and only then is anything checked. The comparisons from Section 5.4 onwards omit the trimming step, for the reason given at the start of that section."],

["frag", [
  "E  = eligible_only(analysis)              # Chapter 2's flag, applied once",
  "ps = fit_propensity(design_matrix(E), E[\"treated\"])      # Chapter 3",
  "keep = trimming_rules(ps, D)[CHOSEN_RULE]                # Chapter 4",
  "",
  "treated, control = match(ps[keep], D[keep],              # this chapter",
  "                         distance=\"mahalanobis\", caliper=0.1,",
  "                         replace=False, ratio=3)",
], "Fragment 5.2  Four chapters in five lines. Full script: ch05/05_01_match_basics.py"],

["p", "The matched dataset is then assembled by taking the treated rows and the selected control rows, and it is at this point that the choices of Section 5.3.3 become visible in the data rather than in the code. Under matching without replacement the two index arrays contain no repeats. Under matching with replacement the control array does, and a reader who builds the matched frame with a plain join rather than by position will silently collapse those repeats and lose the weighting they represent."],

["frag", [
  "matched = pd.concat([E.iloc[treated].assign(arm=1, pair=range(len(treated))),",
  "                     E.iloc[control].assign(arm=0, pair=range(len(control)))])",
  "",
  "assert len(matched) == 2 * len(treated)   # repeats must survive the assembly",
  "assert matched.groupby(\"pair\").size().eq(2).all()",
], "Fragment 5.3  Assembling the matched frame, with the two assertions worth making. Full script: ch05/05_01_match_basics.py"],

["p", "The two assertions are the equivalent, for this chapter, of the merge guards of Section 2.5.4. Neither failure they catch produces an error on its own: a matched frame that has quietly deduplicated its controls looks entirely normal, has a sensible row count, and gives an estimate that is wrong by an amount nobody can reconstruct later."],

["h2", "5.4  Nine matched datasets"],

["p", "The nine variants below are constructed from the same propensity score, on the same eligible population, and scored against the true ATT for the treated persons each one actually matches. Six independent draws are used, because a single draw cannot separate the differences between variants from the differences between samples, and separating those two things is the main business of this chapter."],

["p", "One departure from the sequence of Fragment 5.2 should be stated before the results. The nine variants are matched on the whole eligible population, without the variance-minimising rule that Chapter 4 recommended, and there are three reasons for doing so. The first is that the rule was derived to minimise the variance of a weighting estimator of the average treatment effect, and it trims both tails of the score. In these data no score approaches the upper threshold, so the whole effect falls on the lower tail, where the rule removes, on average across the six draws, 89 treated persons with scores below 0.045, together with 2,649 controls. Every one of those 89 treated persons finds a control inside the caliper when the rule is not applied. For an effect on the treated, the trim therefore resolves no failure of overlap; it narrows the population the estimate describes, and raises the true ATT by 1.1 per cent. The restriction to common support that matching requires is performed by the caliper, which discards about five treated persons rather than 89."],

["p", "The second reason is that this chapter compares matching procedures, and the comparison is cleanest when everything except the procedure is held fixed. The third is that the choice changes none of the chapter's findings. Applying the rule moves the bias of propensity score matching from \u221214.4 to \u221212.6 per cent and that of Mahalanobis matching from +0.7 to \u22120.4 per cent, and the ordering of the variants, and every comparison that follows, is the same either way. Reporting both figures is what Chapter 4 advised, and Script 5.3 reproduces them. A reader whose score resembles the boosted score of Chapter 4, where overlap does fail, should trim before matching, as Fragment 5.2 does."],

["tab", "5.2", "Nine matching variants, six draws.",
  [3200, 1050, 900, 950, 1050, 1050, 1100],
  ["Variant", "Bias", "sd", "Std. error", "Pairs", "Unmatched", "Max reuse"],
  [
    ["NN 1:1, no caliper", "\u221214.4%", "8.5", "443", "4,823", "0", "1"],
    ["NN 1:1, caliper 0.2", "\u221214.4%", "8.5", "444", "4,820", "3", "1"],
    ["NN 1:1, caliper 0.1", "\u221214.4%", "8.5", "444", "4,818", "5", "1"],
    ["NN 1:1, caliper 0.05", "\u221214.4%", "8.5", "444", "4,816", "8", "1"],
    ["NN 1:1, caliper 0.02", "\u221214.4%", "8.5", "445", "4,807", "16", "1"],
    ["NN 1:1 with replacement, caliper 0.1", "\u221213.9%", "7.6", "444", "4,822", "2", "5.7"],
    ["NN 1:2, caliper 0.1", "\u221213.2%", "6.5", "313", "9,596", "16", "1"],
    ["NN 1:3, caliper 0.1", "\u221213.4%", "5.1", "260", "14,123", "63", "1"],
    ["Mahalanobis within caliper 0.1", "+0.7%", "8.6", "337", "4,818", "5", "1"],
  ],
  "Means across six draws. Bias is against the true ATT for the treated persons each variant matches, so a variant that leaves treated persons unmatched is scored against its own estimand. Standard errors are the naive ones; Chapter 9 explains why they are wrong for the variants with reuse.",
  ["l", "r", "r", "r", "r", "r", "r"]
],

["p", "Two things in that table are worth separating before anything else is said. The first eight rows differ from one another by about one percentage point of bias. The ninth differs from them by fifteen. Everything in the rest of this chapter follows from that contrast."],

["fig", "5.1", "Where the variation actually is. (a) The bias of each of the nine variants of Table 5.2, in each of the six draws, plotted as one column per draw; the vertical spread within a column is the difference between variants and the horizontal spread between columns is the difference between draws. (b) The four calipers alone, on the same vertical scale, showing that the lines for 0.02, 0.05, 0.1 and 0.2 standard deviations are indistinguishable. Produced by Script 5.3.",
  "figure_5_1_variation.tif"],

["h2", "5.5  The caliper does not matter"],

["p", "Table 5.3 reports the four one-to-one calipers separately, by draw, because the comparison only makes sense within a draw. Comparing a 0.2 caliper in one sample with a 0.02 caliper in another confounds the two sources of variation this chapter is trying to separate."],

["tab", "5.3", "The same four calipers, in each of six draws.",
  [1500, 1550, 1550, 1550, 1550, 1326],
  ["Draw", "0.02", "0.05", "0.10", "0.20", "Spread"],
  [
    ["20260808", "\u221223.17%", "\u221223.13%", "\u221223.16%", "\u221223.18%", "0.05"],
    ["20260809", "\u221213.79%", "\u221213.65%", "\u221213.64%", "\u221213.63%", "0.16"],
    ["20260810", "\u22126.82%", "\u22126.76%", "\u22126.76%", "\u22126.73%", "0.09"],
    ["20260811", "\u221216.48%", "\u221216.38%", "\u221216.43%", "\u221216.53%", "0.16"],
    ["20260812", "\u22122.76%", "\u22122.77%", "\u22122.77%", "\u22122.78%", "0.02"],
    ["20260813", "\u221223.67%", "\u221223.60%", "\u221223.60%", "\u221223.60%", "0.07"],
  ],
  "Bias of the matched ATT under each caliper, in standard deviations of the linear predictor. The final column is the range within the draw. The standard deviation down any column is 8.5 percentage points.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "Read the table across and then down. Across a row, moving the caliper by a factor of ten changes the estimate by an average of 0.09 percentage points and never by more than 0.16. Down a column, moving to a different draw of the same data-generating process changes it by a standard deviation of 8.5 points, and across the six draws the estimate ranges from \u22122.8 to \u221223.7 per cent."],

["p", "The draw therefore matters about ninety times more than the caliper. That ratio is the most useful single number in this chapter, and it has a direct implication for how time is spent: an analyst who reruns a matching procedure at three calipers and reports the one that looked best has made a selection from a set of estimates that differ by a tenth of a point, while ignoring a sampling distribution twenty points wide."],

["p", "The finding is not that the caliper does nothing. A caliper of 0.02 leaves sixteen treated persons unmatched against three at 0.2, so it does change the matched sample, and in a dataset with worse overlap it would change it much more. The finding is that in this dataset, where Chapter 4 established that overlap is good under the logistic score, the caliper operates on a part of the sample too small to move the estimate. Readers whose overlap diagnostics look like the boosted score of Chapter 4 should expect the caliper to matter more, and should check rather than assume."],

["box", "Trap: tuning inside the noise", [
  "The general form of this trap is worth recognising because it recurs. An analytic choice is varied, the estimate moves a little, the analyst concludes the choice matters and spends time on it. The missing step is comparing the movement against the variability of the estimate itself, which almost always requires either a bootstrap or, as here, repeated draws.",
  "The test is cheap. Before tuning any parameter, resample or re-draw and measure how much the estimate moves for reasons that have nothing to do with the parameter. If the parameter's effect is smaller than that, the tuning is not analysis; it is noise mining, and reporting the best of several such estimates is a specification search whether or not it was intended as one.",
]],

["h2", "5.6  The distance does matter"],

["p", "Having established that the most-discussed parameter is inert, we turn to the one that is usually chosen by default. Matching on the Mahalanobis distance across four covariates, within a propensity caliper of 0.1 standard deviations, halves the absolute bias of the estimate: 5.8 per cent against 12.4 for matching on the propensity score alone."],

["p", "Because the comparison is between two procedures applied to the same draw, it can be made as a paired difference, which removes the draw-to-draw variation that dominated Section 5.5. Table 5.4 reports it that way, and reports twelve draws rather than six. Six were not enough: on the first six the mean reduction was 7.60 percentage points with a standard deviation of 10.13, so the improvement was smaller than its own spread and could not be distinguished from nothing. Doubling the draws settled it, and the episode is worth recording because it is the chapter's own thesis applied to the chapter."],

["tab", "5.4", "Mahalanobis against propensity score matching, paired within draw, twelve draws.",
  [1500, 1800, 2000, 1800, 1326],
  ["Draw", "Mahalanobis", "Propensity score", "Reduction", "Better"],
  [
    ["20260808", "+3.66%", "\u221223.16%", "+19.50", "Mahalanobis"],
    ["20260809", "\u22126.06%", "\u221213.64%", "+7.58", "Mahalanobis"],
    ["20260810", "+4.10%", "\u22126.76%", "+2.65", "Mahalanobis"],
    ["20260811", "+2.46%", "\u221216.43%", "+13.97", "Mahalanobis"],
    ["20260812", "+12.25%", "\u22122.77%", "\u22129.48", "Propensity score"],
    ["20260813", "\u221212.21%", "\u221223.60%", "+11.39", "Mahalanobis"],
    ["20260814", "\u22129.97%", "\u221214.19%", "+4.23", "Mahalanobis"],
    ["20260815", "\u22121.33%", "\u22125.87%", "+4.54", "Mahalanobis"],
    ["20260816", "+5.60%", "\u22128.26%", "+2.66", "Mahalanobis"],
    ["20260817", "+2.48%", "\u22126.11%", "+3.63", "Mahalanobis"],
    ["20260818", "\u22124.34%", "\u221211.27%", "+6.92", "Mahalanobis"],
    ["20260819", "\u22124.82%", "\u221216.77%", "+11.95", "Mahalanobis"],
  ],
  "Twelve draws rather than the six used elsewhere in this chapter, for the reason given in the text. Both are one-to-one greedy matching without replacement inside a 0.1 standard deviation propensity caliper, differing only in what distance is minimised. Reduction is the fall in absolute bias. Mean +6.63 percentage points, standard deviation 7.27, standard error 2.10, better in eleven draws of twelve.",
  ["l", "r", "r", "r", "l"]
],

["p", "Mahalanobis matching reduces the absolute bias in eleven draws of twelve, by an average of 6.63 percentage points against a standard error of 2.10. That is a real difference rather than noise, and it is the only procedural choice in this chapter of which that can be said. It is also a good deal smaller than the six-draw figure first suggested, and materially smaller than the draw-to-draw variation it sits inside."],

["p", "The mechanism is not mysterious. A propensity score is a one-dimensional summary of eighteen covariates, and two persons can share a score while differing substantially on the covariates that make it up: a younger person with high earnings and a short payment history can have the same fitted probability as an older person with low earnings and a long one. Matching on the score treats those two as interchangeable. Matching on the Mahalanobis distance over prior earnings, payment duration, age and education does not, because it requires them to resemble each other on those four quantities directly."],

["p", "This is worth setting against what Chapter 3 said about the balancing property. The score is a balancing score in the sense that, conditional on it, the covariate distributions are equal in expectation across conditions. That is a statement about averages over the whole matched sample, and it is satisfied here, as Section 5.15 demonstrates. It is not a statement that any individual pair is well matched, and the ATT is sensitive to the quality of individual pairs in a way that the average balance does not capture."],

["p", "Two cautions before this becomes a general recommendation. The first is that the Mahalanobis matching here used four covariates, chosen in this chapter as those carrying most of the confounding, and that was not the best choice available. Over the same twelve draws, Mahalanobis distance over all eighteen covariates reduced the mean absolute bias further, from 5.8 to 3.7 per cent, and did better in nine draws of twelve, by an average of 2.07 percentage points against a standard error of 0.84. The four covariates carry much of the confounding but not all of it, and inside a propensity caliper the other fourteen still help. Which covariates enter the distance is therefore a real decision, and unlike the caliper it moves the estimate. The second is that this is one dataset, and a result that holds in twelve draws of one data-generating process is not a general law. Exercise 5.5 asks readers to reproduce it on the second dataset."],

["h2", "5.7  What ratio matching buys"],

["p", "If the caliper is not where precision comes from, the ratio is. Matching each treated person to more than one control uses more of the available control group, and in PLIDA-SIM the control group is large enough to afford it."],

["tab", "5.5", "Precision under one-to-one, one-to-two and one-to-three matching.",
  [1900, 1500, 1500, 1500, 1500, 1426],
  ["Variant", "Bias", "sd of bias", "Std. error", "Pairs", "Unmatched"],
  [
    ["NN 1:1, caliper 0.1", "\u221214.4%", "8.5", "444", "4,818", "5"],
    ["NN 1:2, caliper 0.1", "\u221213.2%", "6.5", "313", "9,596", "16"],
    ["NN 1:3, caliper 0.1", "\u221213.4%", "5.1", "260", "14,123", "63"],
  ],
  "Means across six draws. The bias is unchanged within noise; the draw-to-draw standard deviation falls by 40 per cent and the naive standard error by 41 per cent.",
  ["l", "r", "r", "r", "r", "r"]
],

["p", "Moving from one control to three leaves the bias where it was, within noise, and reduces the draw-to-draw standard deviation from 8.5 to 5.1 percentage points. That is a real gain and it is larger than anything the caliper offers, which makes the relative attention the two receive in applied work difficult to defend."],

["p", "The cost is visible in the final column. A one-to-three match leaves 63 treated persons unmatched against 5 at one-to-one, because filling three slots inside the caliper is harder than filling one. Sixty-three of 4,823 is small, and Section 5.11 considers what to do when it is not."],

["frag", [
  "for ratio in (1, 2, 3):",
  "    treated, control = match(ps, D, caliper=0.1, ratio=ratio)",
  "    est = (y[treated] - y[control]).mean()      # Chapter 9 does this properly",
  "    print(f\"1:{ratio}  pairs {len(treated):6,}  estimate {est:8,.0f}\"",
  "          f\"  unmatched {n_treated - len(set(treated)):3d}\")",
], "Fragment 5.4  Ratio matching, and what it costs in unmatched treated. Full script: ch05/05_02_match_variants.py"],

["h2", "5.8  Optimal matching against greedy"],

["p", "Greedy matching is order-dependent: whoever is matched first gets the closest control, and whoever is matched last takes what remains. Optimal matching removes the dependence by solving for the set of pairs that minimises the total distance across the whole assignment, which is a standard problem with a standard solution and is available in several packages."],

["p", "The comparison has to be made on identical inputs to mean anything, so Table 5.6 gives both procedures the same 2,500 treated persons, the same 7,500 controls and the same caliper, and differs only in how the pairs are chosen."],

["tab", "5.6", "Optimal against greedy matching, on identical inputs.",
  [1500, 1700, 1700, 1700, 1326],
  ["Draw", "Optimal", "Greedy", "Difference", "Total distance"],
  [
    ["20260808", "\u22123.19%", "\u22127.24%", "+4.05", "\u221226%"],
    ["20260809", "\u22128.07%", "\u22129.80%", "+1.73", "\u221224%"],
    ["20260810", "\u221221.08%", "\u221222.05%", "+0.97", "\u221244%"],
    ["20260811", "\u221220.29%", "\u221220.84%", "+0.55", "\u221228%"],
    ["20260812", "\u22125.35%", "\u22126.36%", "+1.00", "\u221245%"],
    ["20260813", "\u221232.01%", "\u221232.56%", "+0.54", "\u221217%"],
  ],
  "Both procedures form the same number of pairs, 2,462 on average, from the same pool at a 0.1 caliper. Difference is the reduction in absolute bias. Total distance is the change optimal matching achieves in the quantity it minimises, which is the whole of what it promises.",
  ["l", "r", "r", "r", "r"]
],

["p", "Optimal matching does what it says. It reduces the total distance across the assignment by 31 per cent on average, and it is better than greedy on bias in six draws of six, so the improvement is real rather than noise. The improvement is 1.47 percentage points, with a standard deviation across draws of 1.33."],

["p", "Set that against the range down the first column, which runs from \u22123.2 to \u221232.0 per cent. Optimal matching delivers a large and guaranteed improvement in the quantity it optimises and a small one in the quantity anybody cares about, and this is the third time in this chapter that a decision has behaved that way. It is nonetheless the easiest of these choices to recommend, because it costs nothing beyond a different function call, removes an arbitrary dependence on sort order, and never did worse in any draw."],

["p", "The practical caveat is computational. The assignment problem scales badly, and on the full 4,867 treated persons against 37,708 controls it is slow enough to be inconvenient; the comparison above is capped at 2,500 by 7,500 for that reason. Where the full problem is too large, most packages offer a blocked version that solves the assignment within strata, which recovers most of the benefit."],

["h2", "5.9  Matching without a propensity score"],

["p", "The propensity score is not the only way to define similarity, and it is worth knowing how an alternative performs, partly because readers will be asked about it and partly because the comparison is informative about what the score contributes."],

["p", "Coarsened exact matching bins each covariate into a small number of categories, forms strata from the combinations, and compares treated with controls inside each stratum, discarding strata that contain only one condition. It has the attraction of requiring no model at all, so nothing can be misspecified, and the disadvantage that the number of strata grows multiplicatively and most of them end up empty."],

["p", "This chapter does not report a coarsened exact matching estimate, because the method's performance depends heavily on how the coarsening is chosen, and a single choice would say more about that choice than about the method. Its cost can nonetheless be stated without running it. Coarsening discards the variation within each bin: two persons in the same earnings band can differ substantially in what they earned, and the stratum treats them as equivalent. With several covariates the bins must be broad for the strata to remain populated, and the broader they are, the more of that variation is lost."],

["p", "The general point is that the propensity score earns its place by being continuous. Its weakness, which Section 5.6 exposed, is that it compresses eighteen covariates into one number; its strength is that it does so without discarding the resolution within each of them. Mahalanobis matching within a propensity caliper, the least biased procedure in Table 5.2, combines the two: it keeps the resolution on the covariates that matter and uses the score only to exclude implausible pairs."],

["h2", "5.10  Control reuse, and the standard error that is not"],

["p", "Matching with replacement allows a control to be selected more than once, and in these data it is selected up to four times at a 0.1 caliper. Of the 4,864 pairs formed on the primary dataset, 4,290 distinct controls appear, and 3,803 of them appear exactly once."],

["p", "The reuse is modest here because the control group is large relative to the treated group and overlap is good. In settings with fewer suitable controls the concentration is much greater, and it is worth knowing which situation one is in, because the consequence falls on the standard error rather than on the estimate."],

["p", "The consequence is that the pairs are not independent observations. A control appearing in four pairs contributes its single outcome to four differences, so those four differences share a source of variation, and a standard error computed as though all pairs were independent leaves that shared variation out. The matched sample of 4,864 pairs carries less information than 4,864 independent pairs would, although with reuse as modest as it is here the difference is small."],

["p", "This chapter does not correct for that, and the standard errors in Table 5.2 are the naive ones. Chapter 9 compares them with a variance estimator that accounts for the reuse and finds that, in these data, the reuse adds only a few per cent to the standard error, and that other features of how the sample was built matter more. What this chapter contributes is the count: any analysis using matching with replacement should report the number of distinct controls alongside the number of pairs, because the gap between them is what Chapter 9 has to work with."],

["frag", [
  "reuse = pd.Series(matched_controls).value_counts()",
  "",
  "print(f\"pairs formed           {len(matched_controls):,}\")",
  "print(f\"distinct controls      {reuse.size:,}\")",
  "print(f\"used exactly once      {(reuse == 1).sum():,}\")",
  "print(f\"most-used control      {reuse.max()} times\")",
], "Fragment 5.5  Reuse, which Chapter 9 needs and the naive standard error ignores. Full script: ch05/05_04_reuse_and_balance.py"],

["h2", "5.11  The unmatched treated, and the estimand"],

["p", "Every caliper leaves some treated persons unmatched, and those persons leave the analysis. This is the fifth appearance in this book of a technical step that changes the population the estimate describes, after the inner join of Section 2.5, complete-case analysis in Section 2.7, attrition in Section 2.8, and trimming in Chapter 4."],

["p", "It is also, in these data, much the smallest of the five, and saying so is more useful than treating every instance as equally alarming. Averaged across the six draws, a 0.1 caliper leaves about five of the 4,823 treated persons unmatched, and the true ATT among those matched is $6,443 against $6,446 among all eligible treated persons, both averaged over the six draws: a shift of 0.05 per cent. At the tightest caliper the shift is 0.15 per cent, and under one-to-three matching, which leaves 63 unmatched, it is 0.8 per cent."],

["p", "The reason the shift is small is the reason Chapter 4 found little to trim: overlap under the logistic score is good, so the treated persons who fail to match are few and are not very different from those who succeed. A reader whose overlap looks like the boosted score of Chapter 4 will find this quantity much larger, and the check costs one line."],

["frag", [
  "unmatched = set(treated_ids) - set(matched_treated_ids)",
  "",
  "print(f\"unmatched treated      {len(unmatched):,} of {len(treated_ids):,}\")",
  "print(f\"true ATT, all treated  {tau[D == 1].mean():,.0f}\")",
  "print(f\"true ATT, matched only {tau[matched_treated].mean():,.0f}\")",
], "Fragment 5.6  The estimand check, which costs one line and is almost never run. Full script: ch05/05_04_reuse_and_balance.py"],

["p", "The general rule is the one Chapter 4 arrived at and this chapter repeats with a smaller number attached: report how many treated persons the procedure discarded, and describe them if there are enough to describe. Where the count is five, a sentence suffices. Where it runs into the hundreds, the description matters as much as the estimate."],

["h2", "5.12  Regression adjustment on the matched sample"],

["p", "A standard recommendation, on meeting a matched sample that is imperfectly balanced, is to regress the outcome on the covariates within the matched sample and take the coefficient on the treatment indicator. The reasoning is that matching removes most of the covariate imbalance and regression mops up what remains, so the two together should do better than either alone. A related procedure, sometimes called bias-corrected matching, adjusts each pair by the difference its covariates imply under an outcome model fitted on the controls."],

["p", "Both are sound recommendations in general and both are easy to apply here, so we tested them. Table 5.7 reports what they did."],

["tab", "5.7", "Regression adjustment and bias correction on the matched samples.",
  [2700, 1600, 1900, 1900, 1226],
  ["Matched sample", "Plain difference", "Bias-corrected", "Regression-adjusted", "Improved in"],
  [
    ["Propensity score nearest neighbour", "\u221214.4%", "\u221215.8%", "\u221215.4%", "2 of 6 draws"],
    ["Mahalanobis within a caliper", "+0.7%", "\u22124.6%", "\u22124.0%", "3 of 6 draws"],
  ],
  "Means across six draws. Bias correction adjusts each pair by the predicted outcome difference its covariates imply under a model fitted on the controls; regression adjustment fits the outcome on the covariates and a treatment indicator within the matched sample. Neither improved on the plain difference in these data.",
  ["l", "r", "r", "r", "l"]
],

["p", "Neither procedure helped. On the propensity score matched sample the plain difference is out by 14.4 per cent and both adjustments are out by slightly more, improving in two draws of six. On the Mahalanobis matched sample, which was nearly unbiased to begin with, both adjustments made it worse by about five points."],

["p", "The explanation is worth following because it is not a criticism of the technique. Regression adjustment removes residual imbalance that a linear model of the covariates can describe. The residual bias in the propensity score matched sample is not of that kind: the pairs are balanced on the mean of every covariate, as Section 5.15 shows, so there is very little linear imbalance left for a linear adjustment to remove. What remains is a mismatch within pairs that offsets on average, and an outcome model fitted on those same covariates cannot see it either, because it is working with the same information that failed to prevent it."],

["p", "The practical conclusion is narrow and worth stating precisely. Regression adjustment on a matched sample is cheap, is usually harmless, and should be reported when it is used; it is not a repair for a matched sample whose pairs are individually poor, and treating it as one is a way of feeling that a problem has been addressed when it has not. Chapter 6's doubly robust estimator combines the two models differently, which is the constructive version of the same idea. In these data it improves on regression adjustment of the propensity score matched sample, but not on weighting alone or on Mahalanobis matching, and Chapter 6 reports the comparison."],

["h2", "5.13  What the matched sample is for"],

["p", "It is worth closing the construction part of this chapter by being explicit about what the matched dataset is, because the rest of the book treats it as an input and the framing affects how the later chapters are read."],

["p", "The most useful description is that matching is nonparametric preprocessing. The matched sample is not an estimate and it is not an analysis; it is a dataset in which the treated and control groups resemble each other more closely than they did, prepared so that whatever analysis follows depends less on modelling assumptions than it would have. On that view the question of which matching procedure is best has no answer on its own, and the right question is which matched dataset makes the subsequent analysis most credible."],

["p", "Three things follow, and each names a later chapter. The matched sample has to be checked for balance before it is used, which is Chapter 8 and which Section 5.15 shows is harder than it appears. Its standard error has to account for how it was built, which is Chapter 9, and for which Section 5.10 records the reuse this chapter's choices produce. And the estimate computed on it can be combined with an outcome model, which is Chapter 6, and which Section 5.12 shows is not the simple repair it is often taken for."],

["p", "This also explains why the outcome plays no part in the construction. If matching is preprocessing, then it is part of the design, and a design chosen with the outcome in view is not a design. Every number in Sections 5.4 to 5.13 that involves the outcome is there to score a construction against a truth that no real project has, and none of it was used to choose among the constructions; the recommendation of Section 5.16.3 rests on balance, overlap and variability, all of which a real project can compute."],

["h2", "5.14  When matching is harder than this"],

["p", "PLIDA-SIM is a comfortable dataset for matching: the control group is roughly eight times the treated group, overlap under the logistic score is good, and every variant in Table 5.2 found a match for all but a handful of treated persons. Many real datasets are not comfortable, and the chapter would be misleading if it ended without saying what changes."],

["p", "Three symptoms indicate a harder problem, and they usually appear together. A substantial share of treated persons fails to match at a conventional caliper; the matched sample is much smaller than the treated group; and the estimate moves noticeably when the caliper is varied, which in these data it does not. The last of the three is the useful diagnostic, because it turns the negative result of Section 5.5 into a test: if the caliper does move the estimate, overlap is poor, and the earlier chapters rather than this one are where the problem lies."],

["p", "The responses available are ordered by how much they concede. Matching with replacement is the mildest, since it allows scarce good controls to serve several treated persons, at the cost of the variance problem of Section 5.10. Reducing the ratio to one-to-one recovers matches that a one-to-three rule could not fill. Widening the caliper accepts worse pairs in exchange for retaining treated persons, and is defensible provided the resulting balance is checked rather than assumed. Abandoning matching for weighting, which Chapter 6 develops, keeps every person and handles the scarcity through the weights instead."],

["p", "What none of these does is manufacture comparable controls where none exist. Where a substantial share of the treated has no counterpart, the honest conclusion is the one Chapter 4 reached about common support: the data can answer the question for part of the treated population and not for the rest, and the report should say which part."],

["h2", "5.15  Two matched samples that pass every test"],

["p", "The propensity score matched sample is out by 14.4 per cent and the Mahalanobis matched sample by 0.7 per cent. Table 5.8 reports the standardised mean differences on the eight most important covariates for both, before and after matching, which is the diagnostic Chapter 8 develops and the one a reader would use to decide whether either matched sample is usable."],

["tab", "5.8", "Balance before and after matching, and the bias each sample produces.",
  [2300, 1700, 1900, 2126],
  ["Covariate", "Before matching", "Propensity score", "Mahalanobis"],
  [
    ["log earnings 2016", "\u22120.341", "+0.009", "\u22120.002"],
    ["fortnights on payment", "+0.394", "\u22120.001", "+0.001"],
    ["long-term recipient", "+0.358", "+0.002", "\u22120.016"],
    ["age", "\u22120.155", "\u22120.017", "+0.000"],
    ["highest education", "\u22120.230", "\u22120.001", "+0.004"],
    ["remoteness", "+0.348", "\u22120.004", "+0.037"],
    ["SEIFA decile", "\u22120.276", "\u22120.002", "+0.032"],
    ["mental health item", "+0.167", "+0.001", "+0.028"],
    ["Mean absolute difference", "0.284", "0.005", "0.015"],
    ["Largest absolute difference", "0.394", "0.017", "0.037"],
    ["Covariates above 0.1", "8 of 8", "0 of 8", "0 of 8"],
    ["Bias of the resulting ATT", "\u2014", "\u221214.4%", "+0.7%"],
  ],
  "Primary dataset for the balance columns, seed 20260808; bias is the six-draw mean from Table 5.2. Both matched samples satisfy every conventional balance criterion.",
  ["l", "r", "r", "r"]
],

["p", "Both samples pass. Every covariate is under 0.1, the conventional threshold; the mean absolute difference is 0.005 and 0.015 against 0.284 before matching; by any diagnostic in ordinary use both matched datasets are well balanced and ready to analyse. One of them then produces an estimate fifteen points further from the truth than the other."],

["p", "This is the most uncomfortable result in the book so far, and it is not an artefact. Balance on the mean of each covariate, considered one at a time, is a necessary condition for the comparison to be valid and it is not a sufficient one. The propensity score matched pairs are, on average, equivalent; individually, many of them pair persons who differ in ways that offset across the sample and do not offset within the outcome. Averages can balance while the pairs underneath them do not."],

["p", "The practical response is not to distrust balance diagnostics, which remain the right first check and would have caught a genuinely unbalanced sample. It is to recognise what they certify and what they do not. Chapter 8 examines the diagnostics that go beyond the mean (i.e., variance ratios, interactions, higher moments and distributional comparisons), shows that these two samples pass all of them as well, and describes a secondary check that can tell the two apart."],

["fig", "5.2", "Balance before and after matching. Standardised mean differences on the eight covariates of Table 5.8, before matching and after each of the two procedures, with the conventional 0.1 threshold marked. Both matched samples fall well inside the threshold on every covariate, and the two estimates they produce differ by fifteen percentage points. Produced by Script 5.4.",
  "figure_5_2_balance.tif"],

["box", "In the DataLab: matched samples and the disclosure rules", [
  "A matched dataset is a subset of persons selected by a rule, and output checkers treat it more carefully than a full-sample analysis for that reason. The number of pairs is usually releasable; the number of distinct controls under matching with replacement sometimes is not, because together with the pair count it bounds how concentrated the reuse was.",
  "Matching with replacement raises a second question. Where a single control appears many times, statistics computed on the matched sample are influenced disproportionately by one person, and a checker may refuse an output on those grounds even when the cell counts look adequate. Reporting the maximum reuse in advance, and keeping it low by widening the caliper or the ratio rather than tightening them, avoids the argument.",
]],

["h2", "5.16  Is this matched dataset ready?"],
["h3", "5.16.1  What to record about a matched sample"],

["p", "Seven things should be recorded about any matched dataset before it is carried into Chapter 8. They are not diagnostics; they are the description of what was constructed, without which no diagnostic can be interpreted."],

["list", [
  "The distance measure, and where it is Mahalanobis, which covariates entered it and why those.",
  "The caliper, in the units it was specified in, and whether it was chosen before or after seeing any estimate.",
  "Whether controls were matched with or without replacement, and if with, the number of distinct controls alongside the number of pairs.",
  "The ratio of controls to treated persons, and whether it was fixed or variable.",
  "The order in which pairs were formed, since greedy matching is order-dependent and the order is a choice.",
  "The number of treated persons left unmatched, and how they differ from those matched where the number is large enough to describe.",
  "The estimand: whether the reported effect is for all treated persons or only for those who matched, and by how much the two differ.",
]],
["h3", "5.16.2  What this chapter cost"],

["p", "The accounting here is unusual, because the largest number in it belongs to a decision most analysts do not know they are making. Across nine variants the distance measure reduces the absolute bias by 6.6 percentage points, the ratio moves the estimate by 1.2, replacement by 0.5, and the caliper by 0.09. The draw moves it by 8.5."],

["p", "Ranked by how much attention each receives in applied work, that ordering is close to reversed. The caliper is the parameter most often reported, tuned and defended, and it is the one that does least. The distance measure is usually a default that goes unmentioned in the methods section, and it does most. The variability of the estimate across samples is larger than every choice except the distance, and it is the quantity least often reported at all, which is the argument Chapter 9 picks up."],

["p", "Set against the rest of the book the ordering is consistent. Chapter 2's worst preparation failure cost 55 percentage points, Chapter 3's worst estimation failure 33, Chapter 4's worst defensible trimming choice 14, and this chapter's largest defensible difference 15. The decisions made early remain the expensive ones, and the decisions made late are mostly repairs."],
["h3", "5.16.3  Recommendations"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, we would match one-to-three without replacement inside a 0.1 standard deviation propensity caliper, using the Mahalanobis distance over the four covariates carrying most of the confounding. Chapter 9 measures that combination as a whole over 200 draws (Section 9.7): the second and third controls reduce the draw-to-draw standard deviation from 5.4 to 4.1 points and cost about two points of bias (−3.3 against −1.3 per cent), so that its root mean squared error is slightly the smaller of the two. It is therefore a trade of bias for precision, and one-to-one matching is the better choice where bias matters more. Either gives a matched sample of distinct persons that needs no correction for reuse."],

["p", "The caliper in that recommendation is doing almost nothing, and we include it because it costs nothing and because a dataset with worse overlap would need it. The recommendation most worth carrying to other data is the negative one: do not spend time tuning the caliper, and do spend it on what the distance is measured over."],
["h3", "5.16.4  Scripts for this chapter"],

["tab", "5.9", "Scripts for Chapter 5. All available from the companion website.",
  [1100, 3400, 3200, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["5.1", "ch05/05_01_match_basics.py", "Table 5.1; a first matched sample", "20 s"],
    ["5.2", "ch05/05_02_match_variants.py", "The nine matched datasets", "40 s"],
    ["5.3", "ch05/05_03_compare_variants.py", "Tables 5.2 to 5.7; Figure 5.1; the checks of Sections 5.4 and 5.6", "9 min"],
    ["5.4", "ch05/05_04_reuse_and_balance.py", "Table 5.8; Figure 5.2", "30 s"],
  ],
  "Script 5.3 generates its own draws, because the central comparison of this chapter is between variation across variants and variation across samples, and it ignores --datadir for that reason.",
  ["l", "l", "l", "r"]
],
["h3", "5.16.5  Further reading"],

["p", "The matching literature is the largest in this field and the most practical parts of it are the software documentation. Leite (2017, chapter 5) works through the variants in R with the same emphasis on reporting what was constructed. On Mahalanobis matching within a propensity caliper, Rosenbaum and Rubin's original recommendation, made two years after they introduced the propensity score, is worth reading in the original rather than in summary, because the conditions attached to it are usually dropped in retelling."],

["p", "On the question this chapter raises in Section 5.15, readers should go directly to Basu, Polsky and Manning, whose argument is that balance on means is a weak certificate and who demonstrate it in a health expenditure setting. Chapter 8 develops the response. For matching with replacement and the variance consequences of reuse, Holmes (2014) is the clearest short treatment and leads directly into Chapter 9."],
["h3", "5.16.6  Exercises"],

["p", "The exercises use PLIDA-SIM B, the second dataset described in Section 2.9.6."],

["list", [
  "Construct the nine matched datasets of Table 5.2 on PLIDA-SIM B and report the bias of each. Does the ordering of the variants hold in the second dataset?",
  "Reproduce Table 5.3 on PLIDA-SIM B and compute the ratio of the between-draw standard deviation to the within-draw caliper spread. Is it of the same order as the ninety reported here?",
  "Match with replacement at a caliper of 0.02 rather than 0.1 and report the maximum reuse and the number of distinct controls. Explain why tightening the caliper increases the reuse.",
  "Replace greedy matching in descending propensity order with greedy matching in ascending order, and then in random order. Report the spread across the three, and compare it with the caliper spread of Section 5.5.",
  "Reproduce the Mahalanobis comparison of Table 5.4 on PLIDA-SIM B, then repeat it using all eighteen covariates in the distance rather than four. Report both, and say which of the two comparisons is the more informative.",
  "Take the matched dataset your answer to Exercise 5.1 recommends and write the seven-item description that Section 5.16.1 requires, as it would appear in a methods section.",
]],
["h3", "5.16.7  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Why is matching described here as part of the design of a study rather than part of its analysis, and what practical discipline follows from that description?",
  "The caliper changes the estimate by 0.09 percentage points and the draw changes it by 8.5. What does an analyst who tunes the caliper and reports the best result actually produce?",
  "Two persons can share a propensity score and differ substantially on the covariates that produced it. Explain how that is possible, and why it matters more for matching than for weighting.",
  "Matching one-to-three reduces the draw-to-draw standard deviation from 8.5 to 5.1 points and leaves the bias unchanged. Why does the bias not also improve?",
  "A control used in four pairs contributes one outcome to four differences. Explain why the resulting standard error is too small, and say which chapter fixes it.",
  "Both matched samples in Table 5.8 have every standardised difference below 0.1, and their estimates differ by fifteen percentage points. What does balance on means certify, and what does it not?",
  "Of the five decisions in Table 5.1, which would you expect to matter most in a dataset where only a few hundred controls resemble the treated, and why might the answer differ from the one this chapter reports?",
]],

];
