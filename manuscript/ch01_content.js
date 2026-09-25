// Chapter 1 content. Prose and exhibits; build_chapter.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "1  Overview of Propensity Score Analysis in Observational Studies"],

["h2", "1.1  Purpose and scope of this chapter"],

["p", "This book is about estimating the effect of a programme from data that were not collected to evaluate it. Most evaluations of employment, health and education programmes in Australia are of this kind: the programme has already run, participation was decided by caseworkers, clinicians or the participants themselves rather than by a random draw, and the evidence available is a set of administrative records linked after the event. Propensity score analysis is one of the principal methods for such data, and the chapters that follow take a single analysis through every stage, from the construction of the analysis file to the policy recommendation, using a simulated dataset in which the true effect of the programme is known."],

["p", "This chapter sets out what the later chapters assume. It explains why a comparison of participants with non-participants can be not merely inaccurate but of the wrong sign; defines the quantities that an analysis tries to estimate and the conditions under which it can succeed; introduces the propensity score and the four ways in which it is used; describes the simulated dataset and the conventions by which every result in the book is scored against the truth; and gives a map of the book, with the decision each chapter settles. It closes with practical notes on the scripts that accompany the book and on the secure environment in which analyses of the real data are carried out."],

["p", "By the end of the chapter, readers should be able to define the ATE and the ATT in terms of potential outcomes; to state the three assumptions on which a propensity score analysis rests and to say which of them the data can check; to explain what the propensity score is and why it is useful; and to find, for any stage of an analysis, the chapter that deals with it. Readers familiar with the potential outcomes framework may wish to read Sections 1.5 to 1.7 closely and the rest quickly, since the conventions set out there are used without further explanation from Chapter 2 onward."],

["h2", "1.2  Selection bias, potential outcomes and estimands"],

["h3", "1.2.1  A comparison with the wrong sign"],

["p", "The example that runs through the book is the Employment Pathways Programme, a fictional programme of job-search assistance and training for people receiving income support, which Chapter 2 describes in detail. Participants commenced the programme in 2017, and the outcome is their earnings in 2019. In the eligible population of the primary dataset, 4,867 of 42,575 persons took part, or 11.4 per cent. If we compare the mean 2019 earnings of those who took part with the mean for those who did not, the participants earned $2,910 less. The programme in fact raised the earnings of those who took part by $6,408 on average."],

["p", "The comparison is wrong because the two groups differed before the programme began, and in ways that bear on later earnings. Caseworkers referred people who were struggling to find work: people with long spells on income support, low or falling earnings, less education and poorer health. Those people would have earned less in 2019 than the non-participants whether or not they took part, and the shortfall that their circumstances would have produced is large enough to mask a substantial gain from the programme. This is selection bias, which occurs when the participants in one condition differ systematically in their pre-existing characteristics from those in another, and it is the central problem that propensity score methods exist to address. Programmes that target disadvantage generate it as a matter of course, because the targeting is the selection."],

["h3", "1.2.2  Potential outcomes"],

["p", "The framework in which the problem is usually stated is that of potential outcomes, associated with Rubin and set out formally by Holland. Each person i has two potential outcomes: Y_i(1), the earnings the person would have had in 2019 after taking part, and Y_i(0), the earnings the person would have had without taking part. The effect of the programme for that person is the difference, τ_i = Y_i(1) − Y_i(0). We observe only one of the two outcomes for any person, namely Y_i(1) for those who took part (D_i = 1) and Y_i(0) for those who did not (D_i = 0); the other is counterfactual. Estimating a treatment effect is therefore a problem of missing data, in which half of every person's outcomes are missing by construction, and the question is under what conditions the observed outcomes of one group can stand in for the missing outcomes of the other."],

["p", "The naive comparison answers that question by assuming that the non-participants' earnings are what the participants would have earned without the programme. The difference in means can be written as the effect on the participants plus a bias term, which is the difference between the participants' and non-participants' untreated earnings. In the example the bias term is about −$9,300, and it outweighs an effect of +$6,408. Every method in this book is, in one way or another, a device for making that bias term small."],

["h3", "1.2.3  The ATE and the ATT"],

["p", "Because the individual effects τ_i vary from person to person, an analysis must say which average of them it is estimating. The average treatment effect (ATE) is the mean of τ_i over the whole population, participants and non-participants alike, and it answers the question of what the programme would do if everyone in the population took part. The average treatment effect on the treated (ATT) is the mean of τ_i over those who actually took part, and it answers the question of what the programme did for its participants. The two differ whenever the effect varies with characteristics that also affect participation. In PLIDA-SIM, as in many targeted programmes, those who take part are those whom the programme helps most, a pattern usually described as selection on gains, so that the ATT ($6,408) exceeds the ATE ($5,412)."],

["p", "Neither estimand is the correct one in general. An evaluation of whether a programme justified its cost for the people it served calls for the ATT, and a decision about extending it to others calls for the ATE, or for an effect on the population to which it would be extended. Different propensity score methods estimate different estimands by default: matching and odds weighting estimate the ATT, inverse probability weighting estimates the ATE, and stratification can be weighted towards either. Much of the confusion in applied work arises from reporting one while describing the other, and Chapters 5 to 7 return to the choice repeatedly. A third quantity, the effect of being referred rather than of taking part (the intention-to-treat effect), is distinguished from both in Section 2.2.1; this book estimates the effect of taking part."],

["h2", "1.3  The assumptions"],

["p", "A propensity score analysis identifies a causal effect, meaning that the effect could be recovered exactly from a sufficiently large sample, only under three assumptions. The first two are specific to observational studies; the third applies to randomised trials as well. It is worth stating them before the methods are introduced, because each chapter can be read as an attempt to satisfy one of them, to check it, or to measure what happens when it fails."],

["p", "The first is unconfoundedness, also called ignorability, conditional independence or selection on observables. It requires that, among persons with the same values of the observed covariates X, taking part is unrelated to the potential outcomes: that is, that the covariates include every variable that affects both participation and earnings. If it holds, participants and non-participants with the same covariates are comparable, and the non-participants' earnings can stand in for the participants' missing untreated earnings. It cannot be tested from the data, because the potential outcomes it concerns are never observed together. The case for it rests on knowledge of how participation was decided, which is why Chapter 2 selects covariates from the programme's operating logic rather than from the data, and the case against it is examined by the sensitivity analysis of Chapter 10."],

["p", "The second is overlap, also called positivity or common support. It requires that every person has a probability of taking part strictly between zero and one given the covariates, so that for every kind of participant there are comparable non-participants, and conversely for the ATE. Unlike unconfoundedness, overlap can be examined directly, and Chapter 4 does so. Where it fails, an analysis must either extrapolate from a model into a region where no comparison is possible or narrow the population to one in which comparison is possible, which changes the estimand."],

["p", "The third is the stable unit treatment value assumption (SUTVA). It requires that each person's potential outcomes depend only on that person's own participation, not on who else took part, and that there is only one version of the programme. An employment programme can violate the first part: if participants take jobs that non-participants would otherwise have filled, the programme's effect on participants overstates its effect on employment, and no comparison of participants with non-participants can detect the displacement. Section 10.4.1 returns to this point. The assumption is usually defended by argument about the scale of the programme relative to its labour market rather than tested."],

["h2", "1.4  The propensity score"],

["p", "The propensity score is the probability of taking part given the observed covariates, e(X) = Pr(D = 1 | X). Rosenbaum and Rubin showed that it is a balancing score: among persons with the same propensity score, the distribution of the covariates is the same for participants and non-participants, and if unconfoundedness holds given X it also holds given e(X) alone. The practical consequence is a reduction of dimension. An analysis that must compare persons who are alike on eighteen covariates at once can instead compare persons who are alike on one number, and the problem of finding comparable non-participants becomes tractable even when the covariates are many and some are continuous."],

["p", "Two features of the score deserve emphasis at the outset. The first is that it is estimated, usually by a logistic regression, and the estimated score balances the covariates only to the extent that the model is right; whether it has done so is checked after the fact, by the balance diagnostics of Chapter 8, rather than assumed. The second is that the score is valued for the balance it produces and not for its accuracy as a prediction. A model that predicts participation better is not necessarily a better propensity score, and Chapter 3 shows a case in which the better predictor produces the worse estimate. Researchers trained in prediction find this the least intuitive feature of the method."],

["p", "The score is used in four ways, each of which has a chapter. Matching (Chapter 5) pairs each participant with one or more non-participants of similar score, and estimates the ATT from the pairs. Weighting (Chapter 6) gives each person a weight derived from the score, so that the weighted groups resemble each other, and estimates the ATE or the ATT depending on the weights. Stratification, or subclassification (Chapter 7), divides the sample into strata of similar score and averages the within-stratum differences. Covariate adjustment uses the score, or the covariates themselves, in a regression model of the outcome, either alone (Chapter 7) or combined with weighting in the doubly robust estimator (Chapter 6), which is consistent if either the propensity model or the outcome model is correct. All four rely on the same three assumptions, and none of them can repair a failure of unconfoundedness."],

["p", "One principle governs how the book uses them. Every decision about the design, including the covariates, the form of the propensity model, the trimming rule, the matching or weighting scheme and the balance criteria, is made and checked without reference to the outcome. The principle, which Rubin has stated as the separation of design from analysis, is what makes an observational study resemble a randomised trial: the comparison is fixed before the result is known, so that it cannot be chosen, even unconsciously, for the result it produces. Chapter 2 sets the 2019 earnings aside for this reason, and Chapter 9 is the first chapter in which they are examined as an analyst with real data would examine them."],

["h2", "1.5  The data, and how results are scored"],

["h3", "1.5.1  PLIDA and PLIDA-SIM"],

["p", "The analyses that this book prepares researchers for are carried out on the Person Level Integrated Data Asset (PLIDA), which the Australian Bureau of Statistics maintains. PLIDA links administrative records on income tax, income support, health service use, education and the Census through a person linkage spine, and makes them available as separate modules through the PLIDA Modular Product. Access is granted to approved researchers for approved projects, and analysis takes place inside the ABS DataLab, a secure environment from which only outputs that have passed disclosure checks may be removed. The arrangements follow the Five Safes framework of safe projects, people, settings, data and outputs, and several of them shape how a propensity score analysis must be done; the boxes headed In the DataLab identify those points throughout the book."],

["p", "PLIDA-SIM is a simulated dataset built to have PLIDA's structure without containing any real person's records. It holds 50,000 simulated persons in nine modules, held at different grains, with the gaps, duplicates and inconsistencies that linked administrative data typically contain, and Chapter 2 constructs an analysis file from them as a researcher would from PLIDA. What distinguishes it from real data is that the generator records, for every person, both potential outcomes, the true propensity score and the variables that drove participation, in a separate truth file. Every estimate in the book can therefore be scored against the truth, and every recommendation rests on measured performance rather than on the assurance of the literature. No result from PLIDA-SIM is evidence about any real Australian programme."],

["p", "The truth file also contains two variables that no analysis file contains: a pre-programme earnings shock and a latent employability, of the kind a caseworker perceives and no administrative record captures. Figure 1.1(a) shows where they sit in the structure that the generator builds in. The book uses the truth file only to score results, with two deliberate exceptions, in Section 6.9 and Chapter 10, where it is used to diagnose why an estimate is biased; in each case the text says so."],

["fig", "1.1", "The book in one figure. (a) The causal structure that the generator of PLIDA-SIM builds in: participation and 2019 earnings both depend on the observed confounders; mutual obligation status affects participation but hardly earnings; occupation affects earnings only; the earnings shock and latent employability (dashed) are not in the analysis file. (b) Estimates of the effect on the primary dataset from the naive comparison and eight designs of Chapters 5 to 7, each with the true ATT for the persons it describes (vertical bars); the dotted line is the true ATT of the eligible population. Produced by Script 1.1.",
  "figure_1_1_overview.tif"],

["h3", "1.5.2  The primary dataset, the draws and the true values"],

["p", "The primary dataset is the version of PLIDA-SIM generated with seed 20260808 (dataset version v1.1.0, variant A), and every table and figure labelled as the primary dataset comes from it. Because a single dataset is a single draw from the generator, a result on it may be a matter of chance, and the book therefore repeats its comparisons on further draws, generated with the consecutive seeds that follow. The number of draws differs between chapters, because it was set by what each comparison needed and by how long the scripts take: five draws in Chapters 2 to 4, six (seeds 20260808 to 20260813) in Chapters 5 to 8, with twelve for one comparison in Chapter 5, 200 in Chapter 9, which is concerned with variability itself, and 40 in Chapter 10. A mean across draws is therefore not directly comparable between chapters that use different draws, and where an estimator appears in several chapters its bias may differ slightly for that reason alone. Exercises use a second dataset, PLIDA-SIM B, whose truth file is withheld from readers so that the answers must be worked out."],

["p", "Bias is reported as a percentage of the true effect for the persons the estimate describes, so that a bias of −10 per cent means an estimate a tenth below the truth; a difference between two biases is given in percentage points, or points. The true value depends on the population, and the book uses three sets of true values, which Table 1.1 gives. Chapter 2 works with all 50,000 persons, because it is concerned with how the analysis file is built; from Chapter 3 onward the analysis is confined to the 42,575 eligible persons of Section 2.2.4, and results are scored against the eligible values, on the primary dataset or averaged over the draws as each table states. Where a design removes persons, by trimming or by leaving participants unmatched, it is scored against the truth for the persons it retains."],

["tab", "1.1", "The three sets of true values used in the book, primary dataset, 2019 dollars.",
  [3726, 1300, 1300, 1400, 1300],
  ["Population", "Persons", "True ATT", "True ATE", "Naive difference"],
  [
    ["All persons in the file (Chapter 2)", "50,000", "$6,192", "$5,157", "−$3,994"],
    ["Eligible population (Chapters 3 to 10)", "42,575", "$6,408", "$5,412", "−$2,910"],
  ],
  "Seed 20260808. The naive difference is the mean 2019 earnings of those who took part less that of those who did not. Averaged over the six draws of Chapters 5 to 8, the eligible population's true ATT is $6,446 and its true ATE $5,417. Produced by Script 1.1.",
  ["l", "r", "r", "r", "r"]
],

["frag", [
  "tau = truth[\"tau_i\"]                       # each person's true effect",
  "att_true = tau[D == 1].mean()             # the truth for those who took part",
  "bias_pct = 100 * (estimate - att_true) / att_true",
], "Fragment 1.1  Scoring an estimate against the truth. Full script: ch01/01_01_overview.py"],

["h2", "1.6  A map of the book"],

["p", "Table 1.2 sets out the stages of a propensity score analysis in the order the book takes them, with the decision each chapter settles and the assumption it serves. The order matters. Each stage takes the output of the one before as given, and an error made early cannot be repaired later: a confounder omitted from the analysis file in Chapter 2 cannot be balanced in Chapter 8, and a population silently narrowed in Chapter 4 cannot be restored in Chapter 9."],

["tab", "1.2", "The stages of a propensity score analysis, and where the book deals with each.",
  [900, 2400, 3526, 2200],
  ["Chapter", "Stage", "The decision it settles", "What it serves"],
  [
    ["2", "Preparing the data", "The treatment, outcome and population; linking; missing data and attrition", "Unconfoundedness, the estimand"],
    ["3", "Estimating the score", "The covariates, their functional form and the estimator", "Balance"],
    ["4", "Trimming", "Whether and where to restrict the sample to common support", "Overlap, the estimand"],
    ["5", "Matching", "Distance, caliper, ratio and replacement", "Balance, the ATT"],
    ["6", "Weighting", "Estimand, normalisation, trimming or capping, doubly robust", "Balance, precision"],
    ["7", "Stratification", "The number of strata and adjustment within them", "Balance"],
    ["8", "Assessing balance", "Whether the adjusted groups are comparable, and how to tell", "Checks balance"],
    ["9", "Estimation and variance", "The estimate and a standard error that reflects how it was built", "Inference"],
    ["10", "Sensitivity and interpretation", "How strong a hidden confounder would have to be; what the estimate means for policy", "Unconfoundedness, the decision"],
  ],
  "Chapter 1 sets out the assumptions; each later chapter serves one or more of them.",
  ["c", "l", "l", "l"]
],

["p", "Figure 1.1(b) previews where the journey leads on the primary dataset. The naive comparison is $2,910 below zero. The designs of Chapters 5 to 7, applied to the logistic score of Chapter 3, give estimates of the ATT from $4,921 for propensity score matching to $6,640 for Mahalanobis matching, against a truth of $6,408; odds weighting gives $5,601, 12.6 per cent low. The designs that the chapters come to recommend do better: Mahalanobis matching with three controls gives $6,193, and odds weighting on the trimmed boosted score gives $6,209, each within about four per cent of the truth for the persons it describes. The outcome regression, at $6,294, is closer still, and Section 6.9 explains why its accuracy in these data is a coincidence of two errors rather than a recommendation. Chapter 10 then explains the bias that remains in the other designs, and shows that part of it could have been found with the observed data and part of it could not."],

["p", "Two recommendations in the book may appear to conflict and are better read together. Chapter 3 recommends the logistic score, and Chapter 6 recommends odds weighting on the boosted score once the sample has been trimmed. The better score depends on how it is used: matching needs a score that places comparable persons next to one another, which the logistic score did better, while weighting on a trimmed sample gave the smaller bias with the boosted score in these data. Chapters 7 to 10 use the logistic score throughout so that their results can be compared with those of Chapters 5 and 6, and Section 10.8.2 returns to the choice. The general rule is to choose the score for the method, to report the other beside it, and to fix both choices before the outcome is examined."],

["h2", "1.7  How to use this book"],

["h3", "1.7.1  The scripts and the companion website"],

["p", "Every table, figure and number in the book is produced by a Python script, and the scripts are available from the companion website, which hosts the book's code repository. The scripts are numbered by chapter, so that Script 5.3 is the third script of Chapter 5 and lives at ch05/05_03_compare_variants.py, and each chapter closes with a table listing its scripts, what each produces and how long it takes. The book prints short code fragments where the code carries the argument, and each fragment names the script that contains it in full. Appendix B maps every exhibit to the script that produces it."],

["p", "The scripts share a small set of command-line options. The option --datadir names the folder holding the PLIDA-SIM files, so that the same script can be run on the primary dataset, on PLIDA-SIM B or on a draw of the reader's own; --quick runs a single draw where a script repeats an experiment across several; and --estimator selects the logistic or boosted score in Chapters 3 and 4. The scripts that generate their own draws say so and ignore --datadir. A few options belong to one script and are described in its chapter, such as --draws in Chapter 9 and --placement in Chapter 2."],

["p", "The package versions are pinned, because some numbers change in their later digits from one version to the next, and the repository includes an audit script that re-derives every number in the book from the scripts' output and fails if any disagrees. Readers who cannot install the packages locally can run each chapter in a hosted notebook from the link in the repository's README. The generator itself is included, so that readers can create further datasets with make_data.py and a seed of their choosing."],

["h3", "1.7.2  Boxes and conventions"],

["p", "Three kinds of box recur. Boxes headed In the DataLab describe the points at which the secure environment imposes constraints that PLIDA-SIM cannot reproduce, chiefly the rules on what may be released: output checkers typically require minimum cell counts, prevent the release of individual values such as a maximum weight, and treat matched or trimmed samples with particular care because they are subsets selected by a rule. Boxes headed Trap describe a mistake that is common in published work and that the software will not warn against. Boxes headed Right for the wrong reason describe a result that is correct in these data for a reason that would not transfer to other data, which is a hazard that only a dataset with a known truth can expose."],

["p", "Each chapter from Chapter 2 onward ends in the same way: a list of what to record about the stage it covers, a summary of what the chapter found or what its decisions cost, recommendations, the scripts, further reading, exercises on PLIDA-SIM B and study questions that require no data. Section 10.7 compiles the lists of what to record into a single reporting checklist. The abbreviations used throughout (e.g., ATE, ATT, SMD) are listed at the front of the book."],

["h2", "1.8  Is this chapter's groundwork in place?"],

["h3", "1.8.1  What this chapter established"],

["p", "A comparison of participants with non-participants in the Employment Pathways Programme gives an effect of −$2,910 where the true effect on participants is +$6,408, because the programme selects people whose earnings would have been low without it. The potential outcomes framework states the problem as one of missing counterfactual earnings, and the ATE and the ATT are the averages an analysis may target; they differ here because the programme selects those it helps most. A propensity score analysis recovers either only under unconfoundedness, overlap and SUTVA, of which only overlap can be examined directly. The propensity score reduces the comparison to a single dimension and is used in four ways, by matching, weighting, stratification and covariate adjustment, each the subject of a chapter. PLIDA-SIM makes every result checkable against the truth, and the book scores results in the eligible population from Chapter 3 onward, on the primary dataset or across draws."],

["h3", "1.8.2  Scripts for this chapter"],

["tab", "1.3", "Scripts for Chapter 1. All available from the companion website.",
  [1100, 3700, 2900, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["1.1", "ch01/01_01_overview.py", "Table 1.1; Figure 1.1; the figures of Sections 1.2 and 1.6", "30 s"],
  ],
  "Script 1.1 reads the analysis file that Scripts 2.5 and 2.6 build, and recomputes each estimate with the functions of the chapter that develops it.",
  ["l", "l", "l", "r"]
],

["h3", "1.8.3  Further reading"],

["p", "Rubin's 1974 paper and Holland's 1986 paper set out the potential outcomes framework in the form used here, and Imbens and Rubin give the standard book-length treatment. Rosenbaum and Rubin's 1983 paper introduced the propensity score and proved its balancing property, and remains readable. For a shorter introduction to the methods as a whole, Austin's 2011 overview and Stuart's review of matching methods are widely used, and Bai and Clark give a concise account of the assumptions and the methods in the register this book adopts. Yanovitzky, Hornik and Zanutto set out the selection problem clearly for social scientists, including the point that observational studies gain in external validity what they lose in control of assignment."],

["p", "For a clinician's view of what the methods can and cannot claim, Vikatmaa's short commentary is a useful corrective: propensity score analyses make the groups more alike, but they do not replace randomised trials. This book agrees, and its last chapter measures the distance that remains."],

["h3", "1.8.4  Study questions"],

["p", "The questions below require no data and are intended to check that the reasoning of the chapter has carried."],

["list", [
  "Why can a naive comparison of participants and non-participants have the wrong sign, and what must be true of the non-participants for it to be unbiased?",
  "Define the ATE and the ATT in terms of potential outcomes. Which would you estimate to decide whether to extend a programme to a new population, and why?",
  "Which of the three assumptions can be examined with the data, and which cannot? For the one that cannot, what kind of evidence supports it?",
  "An employment programme places its participants in jobs that non-participants would otherwise have filled. Which assumption does this violate, and in which direction would it bias an estimate of the programme's effect on employment?",
  "Why is a propensity score model that predicts participation better not necessarily a better propensity score?",
  "Why does the book make every design decision without reference to the outcome, and what would be lost if it did not?",
]],

];
