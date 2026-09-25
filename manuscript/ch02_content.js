// Chapter 2 content. Prose and exhibits; build_ch02.js does formatting.
// Register per Book_language_and_style_guide.md.

module.exports = [

["h1", "2  Preparing Observational Data"],

["h2", "2.1  Purpose and scope of this chapter"],

["p", "A propensity score analysis of observational data has a conspicuous component and a consequential one, and they are not the same. The conspicuous component is the modelling: estimating the score, matching or weighting on it, and producing an estimate of the treatment effect. This is the part of the procedure that the method is named after, and it is the part that most of the methodological literature discusses. The consequential component is everything that precedes the fitting of the propensity model, including the definition of the treatment condition, the choice of a reference date, the linking of administrative modules that were never designed to be linked, the interpretation of absent records, and the units in which the outcome is measured."],

["p", "This chapter is concerned with the second component. Propensity score methods exist to reduce selection bias in observational studies, which occurs when the participants in one condition differ systematically in their pre-existing characteristics from those in another; the argument of this chapter is that in linked administrative data, the construction of the analysis file frequently determines more of the final answer than the choice of propensity score method does. That claim is testable here, because PLIDA-SIM records the true treatment effect for every person in the file. In the sections that follow we make a series of data preparation decisions, each of which a competent analyst might reasonably make differently. One of them moves the estimated effect between fifteen and sixty times further than the entire choice between matching and weighting moves it in Chapters 5 to 9. Several of the others barely move the estimate at all but change what it is an estimate of, which is arguably the more serious failure, because nothing in the output indicates that it has occurred."],

["p", "None of the failures we document in this chapter is exotic. They are the ordinary ones: an inner join that silently discards a third of the sample, a merge that duplicates participants because one module is recorded at a finer grain than another, and a variable that appears to be a useful covariate (e.g., referral type) but is in fact a perfect predictor of treatment because it is recorded only for participants. These failures are common in part because the software does not warn against them. A join that loses fifteen thousand persons returns a smaller data frame and no error message."],

["p", "By the end of this chapter, readers should be able to construct an analysis file from the nine PLIDA-SIM modules, to justify each construction decision made in doing so, and to state what a reader of the resulting report would need to know to judge whether the file was suitable for causal inference. We will also arrive at a quantitative answer to the question of how far these preparation choices moved the estimate, since we will have scored several of them against the known treatment effect."],

["p", "The workflow that follows is written against PLIDA-SIM, but its structure is that of the real PLIDA Modular Product: discrete modules held at different grains, linked through a person spine, and requested and approved individually. Researchers who go on to work in the ABS DataLab should find the shape familiar, and the boxes headed “In the DataLab” identify the points at which the real environment imposes constraints that the synthetic one cannot reproduce."],

["h2", "2.2  Defining the treatment and the outcome"],

["p", "Before we extract any data, two definitions must be fixed: what constitutes the treatment condition, and what constitutes the outcome. Both are more contestable than they initially appear, and both determine what question the analysis will ultimately answer."],
["h3", "2.2.1  Defining the treatment condition"],

["p", "The Employment Pathways Programme, the fictional intervention evaluated throughout this book, is an intensive employment service mediated by caseworkers, and participants commence at some point during 2017. That single sentence conceals at least four candidate definitions of the treatment condition: (a) referral to the programme, (b) commencement, (c) completion of a minimum period, and (d) completion of the full programme."],

["p", "These four definitions are not interchangeable, and the choice among them determines what question the analysis answers. Defining treatment as completion means conditioning on an event that occurs after treatment begins (i.e., a post-treatment variable) and is plainly affected by it: participants who find work early may leave the programme without completing it, and those who find the programme unhelpful may withdraw. A comparison of completers with non-participants therefore confounds the effect of the programme with the characteristics that predict finishing it. This is among the most common serious errors in programme evaluation, and it cannot be repaired by propensity score adjustment, because a propensity model can only balance covariates that were determined before treatment."],

["p", "Referral presents the opposite problem. It is genuinely pre-treatment, but many referred persons never commence, so the comparison is diluted: it estimates the effect of being offered the programme rather than the effect of receiving it. This is a legitimate estimand, and in many policy settings it may be the more useful one, since ministers can control who is referred but not who attends. It is usually termed the intention-to-treat effect, and it should be selected deliberately rather than by default."],

["p", "We define treatment as commencement during 2017. Commencement is recorded in the programme module, it precedes the outcome, and it corresponds to the operational decision that a programme manager makes. The definition is stored in the analysis file as a single binary variable and is never revisited, which is a rule worth adopting generally: a treatment definition that shifts between sections of a report is one that no reader can audit."],
["h3", "2.2.2  Defining and timing the outcome"],

["p", "The outcome is annual salary and wages in calendar 2019, two years after commencement. Three aspects of that definition carry weight, and we consider each in turn."],

["p", "The first is the choice of 2019 rather than 2017 or 2018. Employment programmes typically depress earnings during participation, since time spent in a programme is time not spent working; this is known in the evaluation literature as the lock-in effect. Earnings then rise afterwards, if the programme is effective at all. Measuring the outcome in the treatment year would therefore capture the lock-in and miss the benefit, whereas measuring it too late risks both the decay of the effect and the accumulation of attrition. A two-year follow-up is a common compromise, and it should be defended as a compromise rather than presented as self-evident."],

["p", "The second is that the outcome is a continuous earnings measure rather than a binary employment indicator. Both are reported in this book, but the continuous measure is the primary one, because a programme may move a participant from unemployment into low-paid part-time work without substantially changing a binary outcome, or may raise the earnings of participants who would have worked in any case. The two measures answer different questions, and a report that presents only one of them invites readers to assume that it also gave the other."],

["p", "The third is units. The outcome is measured in constant 2019 dollars rather than in the nominal dollars recorded in the tax module. Section 2.6.5 sets out what deflation requires and what it costs to omit."],

["box", "In the DataLab: dates that are not visible", [
  "PLIDA-SIM records a commencement date for every participant. Real programme administrative data linked into PLIDA often does not, or records it at a coarser grain such as quarter or financial year. Where the treatment date is coarse relative to the outcome window, the boundary between pre-treatment and post-treatment covariates becomes fuzzy, and the safe course is to draw covariates from a period that is unambiguously before any possible commencement date.",
  "This is one reason the baseline in this book is 2016 rather than 2017, even though 2017 covariates would be closer to treatment and therefore more predictive.",
]],
["h3", "2.2.3  Selecting a reference date"],

["p", "A covariate is admissible in a propensity score model if it was determined before treatment; conditioning on anything determined afterwards may introduce bias rather than remove it. This appears to be a simple test, but it is not, because administrative data typically records the date on which a fact was captured (e.g., the lodgement date of a tax return) rather than the date on which it became true."],

["p", "The Census of Population and Housing was conducted in August 2016, and programme commencements run from January 2017. The Census module is therefore admissible, in that everything it records was true before any participant commenced. The 2017 personal income tax record is not admissible, even though it describes a year that overlaps the pre-treatment period for a person who commenced in December, because for most participants it substantially post-dates commencement and reflects the lock-in effect described above. Including it would amount to conditioning on a consequence of treatment."],

["p", "The 2016 tax record is admissible for everyone, as is the 2016 income support record. Location is recorded annually, and the 2016 value is admissible. Health service use in 2016 is likewise admissible. This is why we set the baseline year at 2016, and why every covariate constructed in this chapter is dated 2016 or earlier."],

["p", "That rule carries a real cost, which should be stated rather than passed over. The 2017 covariates would predict the 2019 outcome better than the 2016 covariates do, and a propensity model that used them would appear more impressive on any goodness-of-fit measure. It would also be wrong. Predictive performance is not the objective of a propensity score model, and Chapter 3 returns to this point at length."],
["h3", "2.2.4  Defining the eligible population"],

["p", "The third definition, and the one most often left implicit, is who is in the study at all. A propensity score analysis compares treated with untreated persons (i.e., the treatment and control conditions), and the untreated persons must be plausible counterfactuals rather than merely available. Fifty thousand records exist in PLIDA-SIM, but not all of them describe someone who could have been referred to the programme."],

["p", "We apply three criteria in defining eligibility. A person must be (a) aged 22 to 59 at the end of 2016, because the programme targets working-age adults outside the youth stream; (b) in receipt of at least one fortnight of working-age income support in 2015 or 2016, because referral runs through the income support system; and (c) in scope in 2016, meaning resident, alive, and interacting with at least one administrative system, because a person who was not in the population cannot have been referred."],

["p", "Applied to PLIDA-SIM, we find the second criterion to be the binding one: 42,575 persons, or 85.2 per cent of the file, satisfy all three. The remaining 7,425 were never candidates for the programme, and including them as controls would improve the apparent precision of the estimate while making the comparison less credible. They are not similar to participants, and no amount of propensity score adjustment will make them so; they merely widen the region in which the model must extrapolate. Chapter 4 returns to this question when it considers trimming on the propensity score."],

["p", "There is an awkward corollary. Of those who commenced the programme, 502 fall outside this eligibility definition, mostly persons whose income support spell falls just outside the 2015 to 2016 window. Whichever way this is resolved, something is lost: excluding them narrows the estimand to a population that omits real participants, whereas including them means that the eligibility rule does not in fact describe who was eligible."],

["p", "We exclude them and report that we have done so, on the grounds that a rule which cannot be stated cleanly cannot be replicated. The choice is arguable and the number is small. What is not arguable is where the decision belongs, which is in a footnote of the report rather than in nobody’s notes. Exercise 2.1 asks readers to quantify the difference."],

["p", "One further rule is worth stating. The eligibility criterion should be applied once, recorded as a flag on the analysis file, and never reapplied downstream. Filtering at the point of analysis, separately in each script, is how two tables in the same report come to be based on different samples."],

["h2", "2.3  The PLIDA-SIM data"],

["p", "Every worked example in this book uses PLIDA-SIM, a synthetic dataset of fifty thousand persons observed over six years. It is not PLIDA data. No PLIDA record contributed to it and none could, since access to the real asset is confined to approved projects inside the ABS DataLab and nothing leaves that environment. PLIDA-SIM imitates the structure of the PLIDA Modular Product so that the workflow transfers, and every value in it was generated from equations that are distributed with the book."],

["p", "Readers who are learning a method from synthetic data are owed an account of what was put into it, for two reasons. The first is that a dataset built to demonstrate a technique may be built, deliberately or otherwise, so that the technique appears to work. The second is that knowing the data-generating process is what makes the exercises scoreable: the file truth_parameters.csv contains both potential outcomes for every person (i.e., what each person did earn and what the same person would have earned under the other condition), so any estimate produced in this book can be compared with the correct answer."],
["h3", "2.3.1  Two properties relevant to later chapters"],

["p", "The full generator is documented on the companion website and its equations are reproduced in Appendix A. Two of its features shape everything that follows and should be stated here."],

["p", "The first is that a single latent earnings capacity, constructed from observable characteristics (e.g., education, age, location and family circumstances), drives pre-programme earnings, income support history and later earnings alike. That shared dependence is what makes the confounding substantive rather than decorative, in that the same underlying quantity determines both who is selected into the programme and what they would have earned in its absence. Confounding that is added to a dataset after the fact can usually be adjusted away by almost any method; confounding that runs through a common cause cannot."],

["p", "The second feature is the earnings shock. Approximately one third of the sample loses between one quarter and three quarters of its income in 2016, and that shock does three things simultaneously: it moves people onto income support, it makes them candidates for referral, and it independently depresses their 2019 earnings. This is the pre-programme dip that has been familiar in the evaluation literature since Ashenfelter, and it is the archetypal confounder (i.e., a variable related both to selection and to the outcome). Because it is stored in the truth file rather than in the analysis file, Chapter 10 can ask what happens when such a variable is not observed, and finds that its observed trace, the fall in earnings between 2015 and 2016, does most of the work."],

["p", "Two quantities anchor everything that follows, and we will keep both in view throughout. The average treatment effect on the treated (ATT), which is the mean effect among those who commenced the programme, is $6,192 a year. The average treatment effect (ATE), which averages over all 50,000 persons in the file whether they participated or not, is $5,157. The two differ because the programme was taken up disproportionately by the people it helps most, a pattern usually described as selection on gains; Chapters 5 to 7 return to the choice between these two estimands repeatedly, since different propensity score methods estimate different ones. Comparing the raw means of participants and non-participants, by contrast, yields −$3,994, which is not merely too small but of the wrong sign. A researcher who stopped at that comparison would conclude that the programme cost participants approximately $4,000 a year, when it in fact raised their earnings by approximately $6,200. These three figures describe all 50,000 persons in the file; restricted to the 42,575 eligible persons of Section 2.2.4, who are the population analysed from Chapter 3 onward, the ATT is $6,408, the ATE $5,412 and the raw difference −$2,910, and Section 1.5 sets out which of these values each chapter uses. Chapter 1 discusses why selection bias of this severity arises; the present chapter is concerned with the preparation decisions that lie between those two numbers."],

["p", "One practical consequence should be noted. The generator is seeded, and reseeding it produces an independent draw from the same data-generating process. Several results in this book are therefore reported as an average across five or six draws rather than as a single number. This turns out to matter more than any modelling choice made in this chapter, for reasons that Section 2.7.4 makes concrete."],
["h3", "2.3.2  Limitations of the simulation"],

["p", "Two departures from realism should be stated plainly."],

["p", "The programme effect in PLIDA-SIM is larger than published evaluations of real employment programmes typically report, at approximately fifteen per cent of the control group mean (for the treated, against the untreated mean). This is deliberate on our part. An effect of realistic magnitude would be obscured by sampling variability in several of the exercises, and readers would be unable to distinguish a method that worked from one that did not. It is a teaching parameter rather than an estimate, and no number in this book should be cited as evidence about what employment programmes achieve."],

["p", "The linkage is also perfect. Every person in PLIDA-SIM has a single identifier that joins cleanly across all nine modules. Real probabilistic linkage produces both false matches and missed matches, and the rates typically differ systematically across population groups, which introduces a form of measurement error that this dataset does not reproduce. Researchers working with the real asset should treat the linkage quality documentation as part of their data preparation rather than as a technical annexe."],

["h2", "2.4  Selecting covariates"],

["p", "Having established which variables are admissible, the next question is which of the admissible ones to use. The instinct of many analysts, particularly those arriving from predictive modelling, is to include everything available and to allow the model to sort it out. In this setting that instinct is mistaken, and the reason is worth setting out carefully."],
["h3", "2.4.1  Three types of covariate"],

["p", "Leite (2017) and Bai and Clark (2019) both organise covariate selection around a three-way distinction among the variables available to the researcher, and both caution that the three types behave differently when they are entered into a propensity score model."],

["p", "A true confounder is related both to treatment assignment and to the outcome; if such a covariate is omitted, the estimated treatment effect will be biased. A pure predictor of the outcome is related to the outcome (in this case, later earnings) but not to selection into the programme, so including it removes no selection bias, because none arose from that source. Leite recommends including these covariates nonetheless, to improve precision; however, as Section 2.4.2 demonstrates, the precision benefit depends on where in the analysis the covariate is used. A pure predictor of treatment, sometimes called an instrument or a near-instrument, is related to selection but has no direct effect on the outcome. These covariates are the most problematic of the three, in that they push the estimated propensity scores towards 0 and 1, which inflates the variance of every weighting estimator and reduces the pool of comparable control cases, without removing any bias."],

["p", "PLIDA-SIM contains one covariate of each type, so that the distinction can be demonstrated empirically rather than asserted. Table 2.1 reports the evidence: for each candidate covariate, how well it discriminates between the treatment and control conditions, and how much of the variance in the untreated outcome it explains."],

["tab", "2.1", "The covariate taxonomy in PLIDA-SIM. Discrimination is the area under the ROC curve for a model of treatment using that variable alone; outcome share is the proportion of variance in untreated 2019 earnings it explains on its own.",
  [2900, 2100, 1600, 2426],
  ["Variable", "Expected kind", "Discrimination", "Outcome share"],
  [
    ["Earnings in 2016", "True confounder", "0.610", "0.446"],
    ["Highest education", "True confounder", "0.574", "0.139"],
    ["Fortnights on payment, 2016", "True confounder", "0.617", "0.071"],
    ["occupation_group", "Pure outcome predictor", "0.511", "0.084"],
    ["mutual_obligation_status", "Near-instrument", "0.628", "0.036"],
    ["Remoteness", "?", "0.579", "0.018"],
    ["Mental health item flag", "?", "0.527", "0.004"],
    ["referral_type", "Post-treatment", "1.000", "—"],
  ],
  "Each statistic is marginal: the variable on its own, ignoring the others. The final row is not a covariate at all; see Section 2.4.4.",
  ["l", "l", "r", "r"]
],

["p", "The fourth and fifth rows may usefully be read against each other. The covariate occupation_group discriminates between conditions at 0.511, which is only marginally better than chance, and explains 8 per cent of the variance in untreated earnings; this is the signature of a pure outcome predictor, and such a covariate belongs in the model. The covariate mutual_obligation_status shows the opposite pattern, discriminating at 0.628 while explaining under 4 per cent of the outcome, which is the signature of a near-instrument. Chapter 3 quantifies what including it costs; in summary, it multiplies the largest stabilised weight about fivefold, widens the standard error of the weighted estimate by nearly thirty per cent, and reduces the effective control sample from roughly 24,000 to roughly 3,500, with no reliable reduction in bias."],

["p", "The two rows marked with a question mark should be considered next, because they are the reason that this table cannot be used as a decision rule. On these statistics, remoteness is indistinguishable from the near-instrument, at 0.579 on treatment and 2 per cent of the outcome, and mental health contact is weak on both measures. Neither profile matches the textbook description of a confounder, and an analyst applying the taxonomy mechanically would exclude both covariates."],

["p", "That would be a mistake, and the reason exposes the limits of the exercise. These statistics are marginal, in that each covariate is considered alone, whereas a covariate’s role as a confounder is conditional. Remoteness affects earnings largely through the local labour market and through education and occupation, so once those covariates are in the model its own marginal association with the outcome is small; it nonetheless remains the channel through which a substantial part of the confounding runs. Removing it from the propensity model moves the matched estimate by an average of seven percentage points across five independent draws, although the spread of that change is wide enough that no single draw would establish it, a point to which Chapter 9 returns."],

["p", "No statistic computable from these data settles the classification, because the classification is a claim about causal structure and the data are consistent with several such structures. This is precisely why Bai and Clark place theory first and statistics second, and why the next section begins from how the programme operates rather than from a correlation matrix."],
["h3", "2.4.2  Where a pure outcome predictor improves precision"],

["p", "The recommendation to include pure predictors of the outcome is standard, and it is sound. It is also routinely misapplied, in a way that this dataset makes visible."],

["p", "A propensity score analysis contains two models rather than one, and the distinction between them is easily lost. There is the treatment model, which produces the score, and there is whatever produces the estimate afterwards, which may be a matched difference, a weighted mean, or an outcome regression. A pure outcome predictor belongs in the second of these. Including it in the first accomplishes nothing useful, because the first model is attempting to predict treatment and the covariate by construction does not predict treatment."],

["p", "The point is testable in these data, and we test it directly. Consider occupation_group, which discriminates on treatment at 0.511 and explains 8 per cent of untreated earnings, and add it in each location in turn, across six independent draws."],

["tab", "2.2", "What a pure outcome predictor buys, by where it is used. Standard error ratio is the estimate’s standard error with the variable divided by the standard error without it, so below one is an improvement.",
  [3400, 1900, 1500, 2226],
  ["Where it is added", "Standard error ratio", "Draws improved", "Effect on bias"],
  [
    ["Propensity model, then matched", "1.020", "1 of 6", "None reliable"],
    ["Outcome model, doubly robust", "0.988", "6 of 6", "None reliable"],
  ],
  "Six draws of 50,000 persons. Neither placement moves the bias detectably; only one improves precision. Occupation is carried forward from the most recent pre-period year in which it is observed, per Section 2.6.3.",
  ["l", "r", "r", "l"]
],

["p", "In the propensity model, the covariate does not improve precision; it slightly reduces it, with a standard error ratio of 1.020 and a worse result in five of the six draws. This is what theory would predict. Adding a covariate that does not predict treatment introduces noise into the fitted score, the matches become marginally worse, and the comparison becomes marginally less precise."],

["p", "In the outcome model, the covariate does what the literature promises, although modestly: a ratio of 0.988, better in all six draws, which is a gain of somewhat over one per cent. The improvement is small, it is obtained at no cost, and it is consistent across draws."],

["p", "The guidance therefore survives, with its address corrected. Pure predictors of the outcome should be included in the model of the outcome. For a plain matched difference, which has no outcome model, there is nowhere useful to put them, and the doubly robust estimator in Chapter 6 is the first point in this book at which occupation_group yields any benefit."],

["p", "This distinction is worth labouring, because the mistake is difficult to detect. A propensity model with an additional covariate in it appears more thorough, converges without complaint, and produces a score that correlates at approximately 0.99 with the score that should have been fitted. Nothing in the output indicates that the addition was of no value."],
["h3", "2.4.3  Selecting covariates in practice"],

["p", "The taxonomy is a way of thinking rather than an algorithm. In practice, nothing indicates which category a covariate falls into before it is examined, and examining the outcome to decide which covariates to include is itself a form of data-dredging (e.g., fitting several specifications and retaining the one that gives the largest effect). Bai and Clark's recommendation, which this book follows, is that covariate selection should be driven first by subject-matter theory about how participants came to be treated, and only second by the observed statistical relationships."],

["p", "For the Employment Pathways Programme, that theory is straightforward. Caseworkers refer people who are struggling to find work, and struggling to find work appears in the data in several forms (e.g., time on income support, a recent fall in earnings, low educational attainment, poor local labour market conditions, and health problems that impede employment). Each of these is both a plausible driver of referral and a plausible driver of later earnings. They are the confounders, and they were identified from the programme’s operating logic before any model was estimated."],

["frag", [
  "CONFOUNDERS = [           # theory first: what drives referral AND earnings",
  "    \"fortnights_on_payment_2016\", \"log_earnings_2016\", \"log_earnings_2015\",",
  "    \"highest_edu\", \"remoteness_area\", \"seifa_irsd_decile\",",
  "    \"mh_item_flag\", \"gp_attendances\", \"age\", \"dependent_children\",",
  "]",
  "OUTCOME_ONLY = [\"occupation_group\"]      # improves precision, costs nothing",
  "TREATMENT_ONLY = [\"mutual_obligation_status\"]   # include with your eyes open",
], "Fragment 2.1  Covariate sets declared explicitly, before modelling. Full script: ch02/02_04_covariate_sets.py"],

["p", "Declaring the covariate sets as named lists before any model is fitted is a small discipline with a substantial payoff. It makes the selection auditable, it obliges the analyst to assign each covariate to a category and to defend that assignment, and it means that the sensitivity analysis in Chapter 10 can be run by substituting one list rather than by rewriting the model."],
["h3", "2.4.4  Variables that must be excluded"],

["p", "The programme extract, epp_program.csv, contains a field named referral_type that records whether a participant’s referral was voluntary or mandatory. It appears to be exactly the sort of variable that a propensity model should use. It is not."],

["p", "The file contains one row per participant. Non-participants have no row and therefore no referral type, so the variable predicts treatment perfectly, as the last row of Table 2.1 shows. Any propensity model that includes it will separate: the fitted probabilities collapse to 0 and 1, the standard errors become large or the optimiser fails to converge, and no matching is possible because no treated case has a comparable control."],

["p", "The general rule is that any variable drawn from a file that exists only for the treated is post-treatment by construction, whatever it appears to measure. The test is not whether the underlying fact preceded treatment, since a participant’s referral type was determined before commencement. The test is whether the variable is observed for both conditions."],

["p", "The legitimate pre-treatment version of the same construct is mutual_obligation_status, which sits in the income support module and is recorded for everyone regardless of participation. It captures the same activity-requirement intensity that drives mandatory referral, and it is the variable used throughout this book. Exercise 2.4 asks readers to fit the model both ways and to observe the failure directly."],

["h2", "2.5  Linking the modules"],

["p", "PLIDA-SIM is distributed as nine files. None of them is an analysis file, and constructing one is the first substantial exercise we undertake. In a real project, this stage regularly consumes more time than every subsequent stage combined, and it is where most silent errors are introduced."],
["h3", "2.5.1  The person spine and the grain of each module"],

["p", "The modules link through a person spine, which is a single identifier that appears in every file. Beyond that, they have little in common: they are recorded at four different grains (i.e., four different definitions of what one row represents), they cover different subsets of the population, and they use different conventions for what an absent record means."],

["tab", "2.3", "The nine PLIDA-SIM modules: grain, coverage, and what it means when a row is not there.",
  [2300, 1900, 1300, 3526],
  ["Module", "Grain", "Rows", "An absent row means"],
  [
    ["spine_scoping", "person", "50,000", "— (complete)"],
    ["core_demographics", "person", "50,000", "— (complete)"],
    ["core_locations", "person × year", "300,000", "— (complete)"],
    ["census16_person", "person", "46,420", "Census non-response"],
    ["pit_income", "person × year", "262,071", "Did not lodge a return"],
    ["domino_payments", "person × year × payment", "136,866", "No payment of that type"],
    ["mbs_pbs_health", "person × year", "243,281", "No service contact"],
    ["epp_program", "participant", "5,492", "Did not participate"],
    ["reference_indices", "year", "6", "— (complete)"],
  ],
  "Four grains and four different meanings for a missing row. The distinctions in the final column are the substance of this chapter.",
  ["l", "l", "r", "l"]
],

["p", "Figure 2.1(a) plots coverage over time, showing the share of the fifty thousand persons who have a record in each module in each year. Three features of the data are visible immediately. The locations module covers everyone throughout, because it is derived rather than observed. The tax and health modules cover between eighty and ninety per cent, declining after 2017; that decline is attrition, which Section 2.8 takes up. The income support module rises to seventy-nine per cent in 2016 and then falls to forty-three per cent by 2019, which is not attrition but rather the programme working, in that participants leave income support."],

["fig", "2.1", "The raw data. (a) The share of the 50,000 persons with a record in each module, by reference year. (b) Mean salary and wages by year, as recorded in nominal dollars and after deflation to constant 2019 dollars. Produced by Script 2.2.",
  "figure_2_1_the_raw_data.tif"],

["p", "That last observation deserves emphasis. The steep fall in income support coverage after 2017 is partly a consequence of treatment, so any covariate constructed from post-2017 payment records is contaminated, exactly as described in Section 2.2.3. The same file supplies admissible covariates for 2016 and inadmissible ones for 2018, and nothing within the file distinguishes between them."],
["h3", "2.5.2  Three ways in which a join can fail"],

["p", "Each of the three failures described below produces no error message, which is what makes them dangerous in practice."],

["p", "The first is duplication through grain mismatch. The income support module is recorded at person by year by payment type, so a person receiving two payment types in the same year has two rows. Merging it onto the person-level demographics without aggregating first will silently multiply those persons."],

["frag", [
  "# wrong: 51,174 rows out of 50,000 people",
  "bad = demographics.merge(payments_2016, on=\"person_id\", how=\"left\")",
  "",
  "# right: collapse to the grain you are merging onto, first",
  "totals = (payments_2016.groupby(\"person_id\", as_index=False)",
  "                       .agg(fortnights=(\"fortnights_on_payment\", \"sum\")))",
  "good = demographics.merge(totals, on=\"person_id\", how=\"left\")",
], "Fragment 2.2  Aggregate to one row per person before merging. Full script: ch02/02_05_link_modules.py"],

["p", "The naive merge returns 53,033 rows for 50,000 persons. The 3,033 duplicated persons then appear twice in every subsequent calculation, including the propensity model and the estimated treatment effect. An inflation of six per cent is small enough to escape a cursory glance at the row count and large enough to matter, and it is not random: persons receiving multiple payment types are systematically more disadvantaged than those receiving one."],

["p", "The second failure is loss through inner joins. Chaining inner merges across the demographics, tax, Census and health modules for 2016 returns 34,900 persons, or just under seventy per cent of the sample. Thirty per cent of the data disappears without comment, because the software has done exactly what was asked of it."],

["p", "The loss is not random either. The treated share falls from 10.74 per cent to 9.99 per cent, because participants are more likely than non-participants to be absent from the tax module."],

["p", "What does that cost? We may run the matching procedure from Chapter 5 on the inner-joined file and score it against the known truth. The answer is instructive. The inner-joined build is close to unbiased for the population that it retains; against the full eligible population it is out by approximately five per cent, which is roughly four and a half percentage points worse than the correct build, and the spread across draws is wide enough that this difference cannot be distinguished from zero."],

["p", "Chaining inner joins therefore does not reliably produce the wrong number. It reliably produces a number about the wrong people. Thirty per cent of the sample is removed, with a consistency across draws — 69.8 per cent retained, with a standard deviation of a tenth of a percentage point — that ought to be more troubling than a large bias would be. A large bias announces itself as soon as anyone checks; a silently narrowed population does not."],

["p", "That distinction is worth establishing here, because the chapter returns to it three more times. A preparation decision may cause harm in either of two ways. It may move the estimate away from the truth, which is bias, and which a simulation or a sensitivity check can detect. Alternatively, it may leave the estimate where it is and move the truth, by changing which population the estimand (i.e., the quantity the analysis is attempting to estimate) describes; no internal check will reveal this, because the estimate is correct for the sample in hand. Statistical training generally prepares researchers for the first of these. The second is more common, and it is the principal subject of this chapter."],

["p", "We take the view that a left join from a person-level spine, retaining nulls to be handled deliberately, is almost always the correct construction, and Section 2.7 addresses how those nulls should then be handled."],

["p", "The third failure is treating a structural zero (i.e., a true zero recorded as an absent row) as an unknown value. A person with no health module row in 2016 did not fail to report their health service use; they had none. The correct fill is therefore zero. Treating the absence as missing and dropping the affected cases raises mean GP attendances from 3.10 to 3.67, a spurious increase of eighteen per cent, and removes 7,753 persons who differ systematically from those retained. The same mistake has a categorical form, which is easier to miss. Activity-requirement status is recorded per payment, so a person with no 2016 payment row has no status; folding those 10,719 persons into the “Exempt” level treats “not on payment” as though it were “on payment with no requirement”. The two groups commence the programme at 6.7 and 9.3 per cent respectively, so the fold is not harmless, and the scripts for this chapter give the absent group a level of its own."],

["frag", [
  "analysis = spine[[\"person_id\"]].copy()                # start from everyone",
  "for module in (demographics, census, locations_2016, income_2016):",
  "    analysis = analysis.merge(module, on=\"person_id\", how=\"left\")",
  "",
  "# structural zeros: absence is information, and the information is 'none'",
  "for col in (\"gp_attendances\", \"mh_item_flag\", \"pbs_scripts\", \"fortnights\"):",
  "    analysis[col] = analysis[col].fillna(0)",
], "Fragment 2.3  Left joins from the spine, then fill the structural zeros only. Full script: ch02/02_05_link_modules.py"],

["p", "The distinction between these three cases cannot be inferred from the data. It comes from the data dictionary, and the only reliable defence is to record, for every module, what an absent row means, before any merge is written. Table 2.3 is that document for PLIDA-SIM."],
["h3", "2.5.3  Constructing the linked file"],

["p", "The construction we adopt avoids all three failures and has a single shape: begin from the spine, which contains every person exactly once, and left-join everything onto it. Nothing is ever joined onto anything other than the spine, and every module is reduced to one row per person before it is joined."],

["tab", "2.4", "Building the 2016 analysis file. The row count and the person count are identical at every step, and that is the point.",
  [3400, 1500, 1500, 2626],
  ["Step", "Rows", "Persons", "Note"],
  [
    ["Start from spine_scoping", "50,000", "50,000", "One row per person, by construction"],
    ["+ core_demographics", "50,000", "50,000", "Person grain, complete"],
    ["+ census16_person", "50,000", "50,000", "7.2% arrive as nulls"],
    ["+ core_locations, 2016 only", "50,000", "50,000", "Filter the year before joining"],
    ["+ pit_income, 2016 only", "50,000", "50,000", "10.9% arrive as nulls"],
    ["+ domino_payments, aggregated", "50,000", "50,000", "Collapsed to person grain first"],
    ["+ mbs_pbs_health, 2016 only", "50,000", "50,000", "Absences filled with zero"],
    ["+ treatment flag", "50,000", "50,000", "Membership test, not a join"],
  ],
  "Twenty-five columns for 50,000 persons, of whom 5,369 are flagged as participants (10.74 per cent) and 42,575 as eligible (85.2 per cent).",
  ["l", "r", "r", "l"]
],

["p", "Two details in Table 2.4 repay attention. The first is that the year filter is applied before the join rather than after it. Joining the full 300,000-row locations module and then filtering to 2016 produces the same answer more slowly, and it leaves a window during which the frame is at the wrong grain; this is typically when someone adds a further merge and the duplication begins."],

["p", "The second is that the treatment flag is constructed as a membership test rather than as a join. Joining the programme extract would bring its other columns with it, and those columns are the post-treatment trap described in Section 2.4.4. Testing membership imports exactly one bit of information, which is precisely what is required."],

["frag", [
  "# membership, not merge: brings in the flag and nothing else",
  "analysis[\"treated\"] = analysis[\"person_id\"].isin(programme[\"person_id\"]).astype(int)",
  "",
  "# if you need commencement date too, take it explicitly and knowingly",
  "# analysis = analysis.merge(programme[[\"person_id\", \"commencement_date\"]], ...)",
], "Fragment 2.4  Constructing the treatment indicator. Full script: ch02/02_05_link_modules.py"],
["h3", "2.5.4  Documenting and verifying the build"],

["p", "The failures described in Section 2.5.2 are silent, so the defence against them must be active. Three assertions placed after every join will catch all of them, and they cost little to write."],

["frag", [
  "def safe_merge(left, right, on=\"person_id\"):",
  "    n_before = len(left)",
  "    assert right[on].is_unique, f\"right side is not one row per {on}\"",
  "    out = left.merge(right, on=on, how=\"left\", validate=\"one_to_one\")",
  "    assert len(out) == n_before, f\"row count changed: {n_before} -> {len(out)}\"",
  "    return out",
], "Fragment 2.5  A merge that refuses to duplicate. Full script: ch02/02_05_link_modules.py"],

["p", "The validate argument to the pandas merge function does most of this work and is underused. Passing one_to_one raises an exception if either side has duplicate keys, which converts the duplication failure from a silent one into an immediate one. The explicit uniqueness assertion before the merge is redundant with it, but it produces a clearer error message by naming the offending frame."],

["p", "The row-count assertion catches the residual cases, including the one in which a left join has been changed to an inner join during editing. The two assertions together are difficult to break by accident. Where the analysis frame is legitimately finer than one row per person, an assertion on the person count should be added as well."],

["p", "None of this is sophisticated, and that is the point. The errors described in this section are not conceptually difficult; they are difficult to notice. A build that asserts its own invariants converts a class of undetectable errors into a class of immediate failures."],

["box", "In the DataLab: the data cannot be inspected", [
  "The debugging habits that make merge errors survivable outside the DataLab, such as printing a few rows or inspecting a suspicious record, are not available in the DataLab, where output is cleared before release and individual records are never visible.",
  "The practical consequence is that assertions replace inspection. Every merge in a DataLab project should be followed by a check that the row count is the expected one and that the person count has not changed, written as an assertion that fails loudly rather than as a print statement that nobody reads.",
]],

["h2", "2.6  Reshaping the panel into a cross-section"],

["p", "The linked data are longitudinal, comprising 300,000 person-years across six waves. A propensity score analysis of a single treatment at a single point in time requires one row per person, so collapsing the panel is necessary. Doing so involves two decisions that are usually made by default and should instead be made deliberately."],
["h3", "2.6.1  Selecting a reference year"],

["p", "Time-varying covariates must be summarised as of some date, and we have to choose which. The obvious choice is the year immediately preceding treatment, 2016, on the grounds that it carries the most recent admissible information. The obvious choice is not automatically the correct one."],

["tab", "2.5", "The same covariate, three reference years. Coverage, mean value, and the standardised difference between participants and non-participants.",
  [2200, 2000, 2100, 2726],
  ["Reference year", "Income observed", "Mean earnings", "Standardised difference"],
  [
    ["2014 (t−3)", "93.2%", "$43,783", "−0.230"],
    ["2015 (t−2)", "94.0%", "$43,246", "−0.264"],
    ["2016 (t−1)", "89.1%", "$39,075", "−0.363"],
  ],
  "Earnings are in constant 2019 dollars. The 2016 figures reflect the pre-programme earnings shock experienced by about a third of the sample.",
  ["l", "r", "r", "r"]
],

["p", "Table 2.5 sets out the trade-off. The 2016 measure is the most strongly associated with treatment, which is what is wanted from a confounder, with a standardised difference of −0.36 against −0.23 three years earlier. It is also, however, the least completely observed, at 89.1 per cent against 93.2 per cent, because persons whose earnings collapsed are more likely to have stopped lodging returns. It is furthermore the year contaminated by the earnings shock, which means that it captures a transitory dip as well as the persistent earnings capacity beneath it."],

["p", "The resolution, in this case, is not to choose between them at all. The level and the trajectory each carry information that the other does not, and both are admissible. The analysis file used in this book retains earnings for 2014, 2015 and 2016 separately, and Chapter 3 allows the propensity model to use all three. Collapsing a panel does not require discarding the panel; it requires deciding what summary of it to carry forward."],

["frag", [
  "wide = (income.pivot_table(index=\"person_id\", columns=\"ref_year\",",
  "                           values=\"salary_wages_real\")",
  "              .add_prefix(\"earnings_\"))",
  "",
  "# keep the trajectory, not just the level",
  "wide[\"earnings_drop_2016\"] = 1 - wide[\"earnings_2016\"] / wide[\"earnings_2015\"]",
], "Fragment 2.6  Reshaping to one row per person, retaining the pre-period path. Full script: ch02/02_06_reshape_panel.py"],
["h3", "2.6.2  Summarising a covariate trajectory"],

["p", "Three years of earnings may be summarised in more than one way, and the summaries are not interchangeable. The level indicates how much a person was earning (e.g., $30,000 in 2016); the change indicates the direction in which they were moving; and the volatility indicates how stable their attachment to work had been. All three are pre-treatment, all three are constructible, and they capture different things about the same person."],

["p", "In these data the change carries more information about selection than the level does. The proportional fall in earnings between 2015 and 2016 is observable for 84.5 per cent of the sample, and participants experienced a mean fall of 18.8 per cent against 9.9 per cent for non-participants, which is a standardised difference of 0.28. Earnings volatility across the three pre-treatment years, measured as a coefficient of variation, gives a standardised difference of 0.18. Neither is as strong as the level, at 0.36, but neither is redundant with it: a person earning $30,000 who has earned $30,000 for three years is in a different position from one who was earning $60,000 two years earlier, and only the trajectory variables distinguish between them."],

["frag", [
  "wide[\"earnings_volatility\"] = (wide[[\"earnings_2014\", \"earnings_2015\",",
  "                                       \"earnings_2016\"]].std(axis=1)",
  "                                / wide[[\"earnings_2014\", \"earnings_2015\",",
  "                                        \"earnings_2016\"]].mean(axis=1))",
], "Fragment 2.7  Trajectory summaries alongside the levels. Full script: ch02/02_06_reshape_panel.py"],

["p", "A caution about derived ratios is in order. Both of the variables above are undefined when the denominator is zero or missing, and in these data the denominator is missing for the 6 per cent who did not lodge a return in 2015 and is close to zero for persons with low earnings. The drop variable is therefore observable for 84.5 per cent of persons rather than for the 89 per cent who have a 2016 record, and its own missingness is informative in the manner that Section 2.7 describes. Constructing a ratio from two partially observed variables compounds their missingness, and the compounding is easy to overlook because the result appears as a single clean column."],

["p", "The practical rule is to construct the derived variable and then to check immediately how many rows it is defined on, and whether that subset differs systematically from the whole. If it does, the variable requires a missingness indicator of its own."],
["h3", "2.6.3  Time-varying covariates other than income"],

["p", "Earnings dominate this discussion because they are continuous and because the outcome is measured in the same units, but the same choices arise for every annual covariate."],

["p", "Income support receipt is the clearest case. Fortnights on payment in 2016 is a level; total fortnights across 2014 to 2016 is a cumulative history; and whether the person was on payment in all three years is a persistence indicator. The three are correlated but they are not interchangeable, and the persistence indicator in particular captures something that the annual level does not, namely the difference between a short spell and an entrenched one, which is precisely the distinction on which caseworkers act."],

["p", "Location is less prominent but has the same structure (i.e., the same choice between a single year and a summary of several): the 2016 value and the modal pre-period value are both defensible, the 2019 value is post-treatment, and a careless join of the full locations module makes the third easy to reach by accident."],

["p", "Health service use raises the structural-zero question again, in temporal form. A person with no health module row in 2015 but with rows in 2014 and 2016 had no service contact in 2015. Summing attendances across the three years handles this correctly; averaging the observed years does not, because it treats the zero year as unobserved and thereby inflates the mean for precisely those persons with intermittent contact."],

["p", "Occupation is the case in which the choice of year is not merely a modelling preference but a question of correctness, and it is worth setting out in full, because the trap is easy to fall into and difficult to detect afterwards. Occupation is recorded in the personal income tax module, so it exists only for years in which the person lodged a return. If it is read from 2016 alone, it is null for every 2016 non-lodger and for nobody else. The “None” category is then an exact copy of the missingness indicator discussed in Section 2.7, and it inherits that indicator’s association with treatment: 15.8 per cent of persons with no 2016 return commenced the programme, against 10.1 per cent of those who lodged."],

["p", "That is sufficient to invalidate the variable. Section 2.4 offers occupation as the clean example of a pure outcome predictor, which is to say a covariate that predicts earnings but not participation. Taken from 2016, it is nothing of the kind. A researcher who creates dummy variables from it and enters them into the propensity model will have imported the non-lodgement mechanism without modifying it, without any error being raised, and without any diagnostic indicating that a problem exists."],

["p", "The repair is the ordinary practice with administrative data and costs a single line of code: take the value from the most recent pre-period year in which it is observed. Occupation in 2014 is not a worse measurement than occupation in 2016; it is an older one, and for a covariate that changes slowly the trade is a favourable one."],

["frag", [
  "def occupation_carried_forward(pit, years=(2014, 2015, 2016)):",
  "    occ = None",
  "    for y in years:                       # oldest first, newest wins",
  "        s = (pit.query(\"ref_year == @y\").set_index(\"person_id\")",
  "             [\"occupation_group\"].dropna())",
  "        occ = s if occ is None else s.combine_first(occ)",
  "    return occ",
], "Fragment 2.8  Carrying a categorical covariate forward. Full script: ch02/02_05_link_modules.py"],

["p", "The effect is substantial. Reading from 2016 alone leaves 10.9 per cent of the file with no occupation, whereas carrying the value forward across three years leaves 0.34 per cent, or 172 persons out of 50,000, who lodged no return in any of the three years. Occupation’s discrimination on treatment falls from 0.534 to 0.511, which is the figure reported in Table 2.1, and the covariate becomes the clean case that this chapter claims it to be."],

["p", "What remains is a substantive category rather than an artefact. Those 172 persons have no recorded employment across the whole pre-treatment period, and their participation rate is 17.4 per cent. They should be retained as an explicit “None” level rather than dropped or assigned an occupation they did not have; the group is small enough that it will not by itself determine a match, and it is informative enough that it should not be concealed. This is the general rule for carried-forward categorical covariates: after the carry-forward, establish what the residual missing group represents, and name it."],
["h3", "2.6.4  Distinguishing pre-treatment change from outcomes"],

["p", "The derived variable earnings_drop_2016 in Fragment 2.6 measures the proportional fall in earnings between 2015 and 2016. It is a legitimate covariate, in that both years precede treatment, so nothing about it is contaminated. It is also, in these data, among the most useful covariates available, because it is the observable trace of the earnings shock that drives both selection and the outcome."],

["p", "The distinction to retain is that a pre-treatment change is a covariate whereas a post-treatment change is an outcome. The difference between 2015 and 2016 earnings describes the person as they were when the caseworker met them. The difference between 2016 and 2018 earnings is partly the quantity that the analysis is attempting to measure. Constructing the second and entering it into a propensity model is a well-documented way to estimate an effect of approximately zero and to conclude, incorrectly, that the programme does not work."],
["h3", "2.6.5  Deflating to constant dollars"],

["p", "One transformation belongs in the reshape and is easily omitted. Every monetary variable in PLIDA-SIM is recorded in the nominal dollars of its reference year, as it is in the real asset. Comparing 2016 earnings with 2019 earnings without adjustment therefore compares different currencies that happen to share a name."],

["p", "Figure 2.1(b) showed the magnitude of the problem: mean earnings in 2014 were $39,461 as recorded and $43,783 in constant 2019 dollars, a gap of ten per cent, narrowing to six per cent by 2016. Neither figure is large enough to be obvious in a table, and both are large enough to matter for an effect estimated at approximately fifteen per cent of the control group mean. A pre-post comparison that mixes the two will understate the earlier year and therefore overstate any apparent growth."],

["p", "The module reference_indices.csv supplies two series, and the choice between them is a substantive rather than a technical decision. The consumer price index answers the question of what a dollar could purchase, whereas the wage price index answers the question of how earnings compared with prevailing wages. For an employment programme evaluated on earnings, the second is often the better match to the policy question, since a participant whose real earnings held steady while wages rose has not in fact done well; the first, however, is more conventional and is easier for a non-specialist reader to interpret. We use the consumer price index and say so."],

["frag", [
  "income = income.merge(indices[[\"ref_year\", \"cpi_index\"]], on=\"ref_year\")",
  "income[\"salary_wages_real\"] = (income[\"salary_wages_nominal\"]",
  "                                / (income[\"cpi_index\"] / 100))",
], "Fragment 2.9  Deflation to constant 2019 dollars. Full script: ch02/02_06_reshape_panel.py"],

["p", "One convention repays adopting wholesale. In PLIDA-SIM every nominal column carries the suffix _nominal and every deflated column carries the suffix _real, so an analyst who writes salary_wages receives an error rather than a silently incorrect answer. A naming convention that makes an ambiguous operation impossible is cheaper than any amount of documentation, and it is probably the single change most likely to prevent a units error in a project involving more than one analyst."],
["h3", "2.6.6  The completed analysis file"],

["p", "The completed analysis file has 50,000 rows and 32 columns, and it is the input to every subsequent chapter. Script 2.6 rebuilds it from the raw modules in approximately twenty seconds, which is worth knowing: a build that takes twenty seconds will be rerun whenever something changes, whereas a build that takes an hour will be patched instead."],

["p", "The columns fall into six groups: the person identifier; the treatment and eligibility flags; the confounders, dated 2016 or earlier; the pure outcome predictor; the near-instrument; and the outcomes, dated 2019, which must not be examined until Chapter 9."],

["p", "That last point deserves elaboration. The outcome is present in the file because it has to be stored somewhere, but every operation between this point and Chapter 9 — estimating the propensity score, trimming, matching, weighting, and assessing covariate balance — should be conducted without reference to it. This is the chief practical virtue of propensity score methods, noted by Rubin and repeated by most subsequent authors: the design can be constructed and evaluated before anyone knows what answer it will produce. A researcher who inspects the treatment effect after each modelling decision has forfeited that protection and is engaged in something closer to specification search."],

["p", "A practical way to enforce this separation is to keep the outcome in a separate file and to join it only in the final script. The arrangement may feel bureaucratic, but it removes the temptation entirely."],

["h2", "2.7  Missing data"],

["p", "Three of the nine PLIDA-SIM modules have rows missing, and in each case the absence means something different. A person with no personal income tax record for a year did not lodge a return; a person with no health module row in that year saw no doctor; and a person whose records cease in 2018 has left the population. These are not three instances of a single problem. They are three problems that happen to present identically in a data frame, as a null value, and an analyst who treats them alike will obtain three different kinds of incorrect answer."],

["p", "We are concerned here with the first of the three. Attrition is the subject of Section 2.8, and the structural zeros in the health module were dealt with when the modules were linked in Section 2.5. What remains is non-response, meaning values that exist in the world but are not present in the data."],
["h3", "2.7.1  Identifying what is missing, and why"],

["p", "Five covariates in the analysis file carry missing values (e.g., salary and wages, and the three Census items), at rates between 6 and 11 per cent, as set out in Table 2.6. Considered one at a time, these rates are unremarkable. Considered together, they remove more than a fifth of the sample from any analysis that requires a complete record."],

["tab", "2.6", "Missing values in the Chapter 2 analysis file, by covariate and source.",
  [2600, 1500, 1400, 3526],
  ["Covariate", "Source", "Missing", "Why"],
  [
    ["Salary and wages, 2016", "PIT", "10.9%", "Did not lodge a return"],
    ["Highest education", "Census", "7.2%", "Census non-response"],
    ["Dependent children", "Census", "7.2%", "Census non-response"],
    ["English proficiency", "Census", "7.2%", "Census non-response"],
    ["Salary and wages, 2015", "PIT", "6.0%", "Did not lodge a return"],
    ["Any of the above", "—", "21.5%", "—"],
  ],
  "The three Census items are missing together, because the module is missing at the person level rather than the field level. This matters: the Census non-response is one mechanism, not three.",
  ["l", "l", "r", "l"]
],

["p", "The conventional next step is to classify each mechanism as missing completely at random, missing at random, or missing not at random, and to select a method accordingly. That taxonomy is standard and is set out in every treatment of the subject. On real linked administrative data, however, it is close to unusable, because the classification depends on the very values that cannot be observed. What follows is the diagnostic that can in fact be run."],
["h3", "2.7.2  Profiling the cases with missing values"],

["p", "The income variable is missing for those who did not lodge a tax return. Whether this matters depends entirely on whether non-lodgers differ from lodgers in ways related to the treatment or to the outcome. Their incomes cannot be examined, by definition; everything else about them can be, however, including their payment history, their health service use, their age, where they live, and, most importantly, whether they subsequently commenced the programme."],

["p", "Script 2.7 constructs an indicator for the absence of a 2016 tax record and computes standardised differences between the two groups on covariates that are complete for everyone. This is the same standardised mean difference that Chapter 8 uses to assess covariate balance after matching, applied here to a different question."],

["frag", [
  "absent = analysis[\"inc_2016\"].isna()",
  "",
  "for name, v in complete_covariates.items():",
  "    a, b = v[absent], v[~absent]",
  "    pooled = np.sqrt((a.var() + b.var()) / 2)",
  "    smd[name] = (a.mean() - b.mean()) / pooled",
], "Fragment 2.10  Profiling the missing, using only what is observed for everyone. Full script: ch02/02_07_missingness_experiment.py"],

["fig", "2.2", "Missing data. (a) Standardised differences between persons with and without a 2016 personal income tax record; bars beyond the dashed lines exceed the conventional 0.1 threshold. (b) Bias in the estimated ATT by handling strategy, across five independent draws; open circles are individual draws, filled diamonds the mean. Produced by Script 2.7.",
  "figure_2_2_missing_data.tif"],

["p", "The result in Figure 2.2(a) settles the question. Persons without a 2016 tax record spent an average of 14.4 fortnights on income support in that year, against 9.5 for those with one, which is a standardised difference of 0.48. Long-term receipt separates the two groups more sharply still, at 0.39. Those without a record are more likely to live in outer regional or remote areas (12.6 against 8.7 per cent), more likely to have a mental health item recorded (13.5 against 9.4 per cent), and a little over two years younger. Most consequentially, 15.8 per cent of them subsequently commenced the programme, against 10.1 per cent of those who lodged."],

["p", "Non-lodgement is therefore not incidental to this analysis. It is concentrated among persons with weak recent attachment to the labour market, and those are precisely the persons whom the programme selects. Any handling of this variable that treats the absence as uninformative discards one of the strongest signals in the file."],

["p", "This diagnostic also delivers the unwelcome news. The probability of non-lodgement depends on income itself, since persons earning nothing are those with nothing to declare, which makes the mechanism missing not at random. No imputation method recovers the truth under those conditions, because the information required to do so is exactly the information that is absent. The realistic objective is therefore not to solve the problem, but to select the handling that does least damage and to say so in the report."],
["h3", "2.7.3  Six strategies for handling missing data"],

["p", "We consider six approaches, each of them defensible and each with published advocates. Every one is carried through an identical downstream pipeline, using the same covariates, the same logistic propensity model, and the same 1:1 nearest-neighbour match at a caliper of 0.1 standard deviations, so that the only quantity varying is the treatment of missingness."],

["frag", [
  "incomplete = [c for c in X.columns if X[c].isna().any()]",
  "flags = X[incomplete].isna().astype(int).add_suffix(\"_missing\")",
  "",
  "median    = SimpleImputer(strategy=\"median\").fit_transform(X)",
  "iterative = IterativeImputer(max_iter=10, random_state=0).fit_transform(X)",
  "",
  "# the fourth and sixth strategies keep the flags alongside the imputed values",
  "strategies[\"median + indicators\"] = pd.concat([median, flags], axis=1)",
], "Fragment 2.11  Constructing the six covariate sets. Full script: ch02/02_07_missingness_experiment.py"],

["p", "Because PLIDA-SIM records both potential outcomes for every person, each result can be scored against the truth rather than merely compared with the others. Because the generator can be reseeded, the whole experiment can also be repeated on independent draws from the same data-generating process, which turns out to matter more than the choice of method does. Panel (b) of Figure 2.2 reports the result, and panel (a), the diagnosis, is placed beside it because the two together constitute one argument."],

["tab", "2.7", "Bias by strategy: mean across five draws, and the paired within-draw difference against median imputation with indicators.",
  [3300, 1300, 1000, 1600, 1826],
  ["Strategy", "Mean bias", "SD", "Paired diff.", "SD of diff."],
  [
    ["Drop every column with any missing", "–58.7%", "6.9", "–55.0", "6.8"],
    ["Iterative imputation", "–7.6%", "5.0", "–3.9", "5.3"],
    ["Median imputation + indicators", "–3.7%", "3.9", "—", "—"],
    ["Median imputation", "–2.3%", "7.1", "+1.4", "8.6"],
    ["Iterative imputation + indicators", "–2.1%", "4.2", "+1.6", "5.3"],
    ["Complete case (listwise deletion)", "–1.4%", "14.9", "+2.3", "14.9"],
  ],
  "Bias is relative to the true effect for the sample each strategy actually analyses. Pairing removes variation common to a draw, which is why the paired differences are more informative than the means.",
  ["l", "r", "r", "r", "r"]
],
["h3", "2.7.4  Comparing the six strategies"],

["p", "Table 2.7 reports two quantities for each strategy: the mean bias across the five draws, and the paired within-draw difference against median imputation with indicators. The paired differences are the more informative of the two, because they remove the variation that is common to all strategies within a given draw and thereby isolate the contribution of the strategy itself."],

["p", "One result was consistent across all five draws. Dropping every covariate that contained a missing value produced a bias of 55.0 percentage points, with a standard deviation across draws of 6.8; this is approximately one eighth of the treatment effect being estimated, and it was the only strategy whose bias had the same sign in every draw. The reason is that the discarded covariates included prior income, which is the strongest confounder in these data. When researchers remove covariates to avoid the inconvenience of missing values, the rule is applied without regard to the confounding role of the covariate that is removed; consequently, the covariate on which the analysis depends may be discarded along with the others. Although the practice is often defended on grounds of caution, it may substantially increase, rather than reduce, selection bias in the estimated treatment effect."],

["p", "The remaining five strategies performed similarly to one another. Their mean biases ranged from −1.4 to −7.6 per cent, a range of approximately six percentage points, while the draw-to-draw standard deviation within each strategy ranged from 3.9 to 14.9. Every paired difference reported in Table 2.7 was smaller than its own standard deviation; therefore, the apparent ordering among these five strategies should not be interpreted as evidence that any one of them is preferable. Iterative imputation, which is the most computationally sophisticated of the options considered, produced a slightly larger bias than median imputation, but this difference cannot be distinguished from sampling variability."],

["p", "This comparison illustrates a point that recurs throughout the remaining chapters: the variability of an estimator across samples frequently exceeds the differences among defensible analytic choices. Researchers who devote considerable effort to selecting an imputation method, and who then report a point estimate without an accompanying interval, have attended to the smaller source of uncertainty while neglecting the larger one."],

["p", "Two qualifications are necessary, so that these results are not read as a justification for arbitrary choices. First, the five strategies performed similarly only because the sixth was avoided; the results are comparable across the defensible options, not across all available options. Second, the two strategies that retained missingness indicators were not merely comparable to the others but were also more stable. Median imputation with indicators had the smallest standard deviation of any strategy examined, at 3.9, compared with 7.1 for median imputation alone and 14.9 for complete-case analysis. Retaining the fact of missingness as a covariate did not reliably change the estimate, but it did appear to stabilise it. Given that the mechanism in these data is missing not at random, and that the missingness indicator is the only observable component of that mechanism, this is the result that theory would predict."],
["h3", "2.7.5  Complete-case analysis"],

["p", "Complete-case analysis deserves separate treatment from us here, because its entry in Table 2.7 is misleading in a way that matters for policy work. Its mean bias across draws, at −1.4 per cent, is the smallest in the table, and on that evidence it appears to be the best available choice."],

["p", "It is not, and the reason is not visible in the table. Listwise deletion removed 10,736 persons, or 21.5 per cent of the sample, and Figure 2.2(a) has already established that they are not a random 21.5 per cent. The estimate that survives is close to unbiased for the population that remains, but that population is not the one about which the policy question was asked. The survivors are older (40.8 years against 39.1), more attached to the labour market (9.4 fortnights on payment against 12.5), and less likely to have participated (9.8 against 14.0 per cent). Deletion has therefore selected against precisely those persons whom the programme reaches."],

["p", "The consequence is measurable. The true ATT among the survivors is $5,932, against $6,237 for all treated persons in the file, averaged over the five draws; an estimate that is unbiased for the survivors is therefore already 4.9 per cent low for the population about which the question was asked, and that gap is systematic, appearing in all five draws. Complete-case analysis obtains its apparent accuracy by changing the estimand. Its standard deviation across draws, at 14.9 against 3.9 for the steadiest imputation strategy, indicates that the remainder of the apparent accuracy was attributable to chance rather than to method. The analysis is arithmetically correct and answers a question that nobody asked. This is the same failure that Chapter 4 encounters when trimming on the propensity score, and to which Chapter 10 returns when discussing reporting: a defensible technical step silently redefines the population, and nothing in the output indicates that it has done so."],
["h3", "2.7.6  Recommendations and reporting"],

["p", "For PLIDA-SIM, and for linked administrative data resembling it, our recommendation is to impute rather than to delete, to retain a missingness indicator for every variable imputed, and not to agonise over the choice of imputation method. Median imputation with indicators and iterative imputation with indicators are equivalent for these data; the second is marginally preferable on stability grounds and costs nothing but runtime."],

["p", "Four things should be reported: (a) the rate of missingness for every covariate entering the propensity model; (b) the profile of the cases with missing values, in the form of Figure 2.2(a) or the table underlying it, since a reader cannot otherwise judge whether the mechanism is ignorable; (c) the method used, together with that indicators were retained; and (d) the number of persons, if any, excluded from the analysis, and how they differ from those retained. The fourth is the item most often omitted and the one that a careful reviewer will request first."],

["p", "What we cannot report is that the problem has been solved. Under a missing-not-at-random mechanism it has not been, and the honest closing sentence of a missing data section is a statement of what remains unresolved and of how much it could matter. Chapter 10 develops sensitivity analysis for a confounder that was not measured, and the same reasoning, which asks how different the missing values would have to be for the conclusion to change, is the way to place a magnitude on that residual doubt."],

["h2", "2.8  Attrition"],

["p", "Section 2.7 dealt with persons who are present in the data but missing a value. This section deals with persons who leave the observable population altogether. The two are often discussed together, but in observational studies they are not the same problem: an imputation strategy cannot assist with a person who has no 2019 outcome to impute towards, and the damage that attrition does is to the population the estimate describes rather than to the estimate itself."],
["h3", "2.8.1  Three routes out of the sample"],

["p", "Between commencement in 2017 and the outcome year of 2019, 12.5 per cent of the sample leaves the observable population by one of three routes (i.e., death, emigration, or ceasing to appear)."],

["tab", "2.8", "Attrition between treatment and outcome, by route.",
  [2400, 1300, 1300, 4026],
  ["Route", "Rate", "Labelled?", "How it is identified"],
  [
    ["Death", "1.7%", "Yes", "deceased_year is populated"],
    ["Emigration", "2.0%", "Yes", "emigrated_year is populated"],
    ["Left the in-scope population", "8.8%", "No", "last_active_year is before 2019"],
    ["Any of the three", "12.5%", "—", "—"],
  ],
  "The largest route is the unlabelled one. An analyst who filters on the two explicit fields has addressed 3.7 percentage points of a 12.5 point problem.",
  ["l", "r", "l", "l"]
],

["p", "The asymmetry evident in Table 2.8 is the practical lesson. Death and emigration are recorded because administrative systems have a reason to record them. Simply ceasing to interact with the tax, payment and health systems is not an event that anything records, so it must be inferred from the absence of subsequent records, which is the purpose of last_active_year in the scoping module. Real PLIDA has the same property, and the Core Scoping module exists precisely because defining who is in the population in a given year is not straightforward."],
["h3", "2.8.2  Assessing whether attrition is random"],

["p", "Attrition runs at 17.2 per cent among participants and 12.0 per cent among non-participants. It is concentrated among persons who experienced the pre-programme earnings shock, who constitute 66 per cent of those who leave against 29 per cent of those who remain, and those are precisely the persons with the largest treatment effects in these data."],

["p", "The consequence is a shift in what can be estimated. The true ATT is $6,192 across all 50,000 persons and $5,895 among those still observable in 2019, a difference of 4.8 per cent. That difference is not bias. It is a different quantity, and it exists before any estimator has been applied."],
["h3", "2.8.3  The effect of attrition on the estimand"],

["p", "Running the matching procedure from Chapter 5 on survivors only, which is the only thing that can be done, recovers the effect for survivors to within 6.7 per cent; this is respectable, and well inside the sampling variability documented in Chapter 9. Scoring the same estimate against the effect for the full eligible population, however, gives an error of 10.9 per cent."],

["p", "Nothing in the output distinguishes these two readings, since the estimate is the same number in both cases. What differs is the population that it describes, and the analyst is the only person in a position to know which population the policy question concerned. This is the third route into the same failure: the inner join in Section 2.5 reached it, complete-case analysis in Section 2.7 reached it, and attrition arrives at it from a direction that the analyst does not control at all. It will occur twice more, when Chapter 4 trims on the propensity score and when Chapter 5 discards unmatched participants. Five routes lead to one destination, which is an estimate that is correct about a population nobody asked about."],
["h3", "2.8.4  Available responses to attrition"],

["p", "Three responses are available to us, in ascending order of ambition and descending order of reliability."],

["p", "The first is disclosure, which is not optional. Researchers should report the attrition rate, report it separately by treatment condition, characterise how those who leave differ from those who remain using covariates observed for both (e.g., age, prior earnings and payment history), and state which population the estimate describes. These four items cost a paragraph and they allow a reader to judge the result; a reader given only a point estimate cannot do so."],

["p", "The second is inverse probability of attrition weighting, in which the probability of remaining observable is modelled as a function of baseline covariates, and the survivors are weighted by the inverse of that probability so that they stand in for those who left. This is the same machinery that Chapter 6 applies to a different selection problem, and it rests on the same assumption, namely that attrition is ignorable given the observed covariates. In these data that assumption is false, because attrition is driven partly by the earnings shock, which the observed fall in 2016 earnings captures only in part. The weighting therefore recovers some of the shift but not all of it, which is the usual situation in practice."],

["p", "The third is bounds. Rather than assuming anything about those who left, the researcher may ask how extreme their outcomes would have to be to overturn the conclusion. If the estimate survives the assumption that every treated leaver would have earned nothing and every control leaver would have earned the maximum, then it is robust to attrition whatever the mechanism. Worst-case bounds of this kind are usually too wide to be informative at an attrition rate of 13 per cent, but they are inexpensive to compute and they occasionally settle an argument. Chapter 10 develops the analogous sensitivity analysis for unobserved confounding."],

["p", "What none of the three responses does is recover the missing outcomes. Attrition removes information, and no method restores it. The only question is whether the remaining information supports the claim being made, and that is a question for the analyst to answer explicitly rather than for the software to answer silently."],

["h2", "2.9  Is this dataset ready to analyse?"],

["p", "We have now built the analysis file. Whether it is fit for causal inference is a separate question, and the honest answer for PLIDA-SIM, as for most linked administrative data, is that it is fit for a carefully qualified analysis and not for an unqualified one."],
["h3", "2.9.1  Verifying the constructed file"],

["p", "A file that built without error is not the same as a file that is correct. We recommend four checks, which take a few minutes and catch most of what survives the assertions described in Section 2.5.4."],

["p", "The first is to check the marginal distributions against something external. Every constructed variable has an expected distribution, and the expectation comes from outside the data: the sex ratio should be close to even, the age range should match the eligibility rule, and the education distribution should resemble the Census. Discrepancies usually indicate a mapping error, such as a category recoded to the wrong level or an ordinal scale reversed. Errors of this kind are invisible in aggregate statistics but obvious in a frequency table."],

["p", "The second is to check the joins by counting. For each module, how many persons acquired a value, and does that number match the coverage reported in Table 2.3? A join that silently matched nothing produces a column of nulls, which is indistinguishable from a high rate of non-response."],

["p", "The third is to check the derived variables on cases that can be verified by hand. Take five persons, compute the earnings drop with a calculator, and compare the results. This may feel beneath a professional analyst, but it detects sign errors, off-by-one year offsets, and denominators that should have been numerators. In a DataLab project, where individual records cannot be viewed, the equivalent is to construct the variable in two different ways and to assert that the two agree."],

["p", "The fourth is to compare the treatment and control conditions on the raw covariates, before any modelling. If the two groups appear identical on everything, the treatment flag is probably wrong. If they differ on something that should be unrelated to selection, then either the theory set out in Section 2.4.3 is incomplete or the variable is contaminated. The standardised differences in these data run from 0.25 to 0.42 on the confounders and reach 0.65 on the near-instrument, with twelve covariates exceeding the conventional threshold of 0.1. These differences are large, as they should be, since the whole premise of the analysis is that assignment was not random."],

["frag", [
  "assert analysis[\"person_id\"].is_unique",
  "assert analysis[\"treated\"].isin([0, 1]).all()",
  "assert analysis.loc[analysis.eligible == 1, \"age_2016\"].between(22, 59).all()",
  "assert analysis[\"earnings_2016\"].min() >= 0",
  "assert analysis.filter(like=\"_nominal\").empty, \"nominal columns must not reach the analysis file\"",
], "Fragment 2.12  Invariants worth asserting on the finished file. Full script: ch02/02_06_reshape_panel.py"],

["p", "The last assertion in Fragment 2.12 is the units guard from Section 2.6.5, enforced structurally: if a nominal column has reached the analysis file, then something upstream has omitted the deflation step."],
["h3", "2.9.2  What to record about an analysis file"],

["p", "Before we enter a constructed file into a propensity model, seven things should be true and documented. Each corresponds to a decision made somewhere in this chapter."],

["list", [
  "The treatment is a single binary variable with a stated definition and a stated date, and nothing downstream redefines it.",
  "Every covariate is dated before the earliest possible treatment date, and no covariate is drawn from a file that exists only for the treated.",
  "Covariates are assigned to declared sets — confounders, outcome predictors, treatment predictors — with the assignment defensible from the programme's operating logic rather than from the outcome data.",
  "For every module, what an absent row means is written down, and structural zeros are distinguished from unknown values.",
  "Missingness rates are reported for every covariate entering the model, and the people who are missing have been profiled against those who are not.",
  "Attrition is quantified overall and by treatment arm, and the population the estimate will describe is stated explicitly.",
  "All monetary quantities are in constant dollars of a stated base year, with the index series named.",
]],

["p", "None of these is a statistical test, and none of them can be automated. They are the items that a careful reviewer will ask for, and assembling them after the analysis is complete is considerably harder than recording them as the work proceeds."],
["h3", "2.9.3  What this chapter cost"],

["p", "We can now total the decisions made in this chapter against the effect being estimated. The true ATT across all 50,000 persons is $6,192, and Table 2.9 prices each failure against the true ATT of the population that each analysis retains."],

["tab", "2.9", "What each preparation failure costs. Bias figures are means across five independent draws, each scored against the true ATT of the population the analysis retains.",
  [3100, 1900, 1500, 2526],
  ["Failure", "Damage to the estimate", "Damage to the estimand", "Detectable internally?"],
  [
    ["Drop columns containing any missing", "–59%", "None", "Yes, if scored against truth"],
    ["Treat structural zeros as unknown", "Not measured", "7,753 people removed", "No"],
    ["Chain inner joins", "–4.6pp, within noise", "30.1% of the sample", "No"],
    ["Complete-case analysis", "–1.3pp, within noise", "21.6% of the sample", "No"],
    ["Ignore attrition", "–9.0pp", "12.5%, differential by arm", "No"],
  ],
  "Damage to the estimate is bias against the population the analysis retains. Damage to the estimand is the change in which population that is. The final column asks whether an analyst working only from their own output could discover the problem.",
  ["l", "r", "r", "l"]
],

["p", "Reading Table 2.9 by its last three columns makes the argument of the chapter visible at once. Exactly one failure, the first, produces a large, reliable and detectable bias; it is also the only one that most analysts would immediately recognise as a mistake. The other four leave the estimate substantially where it was and quietly change the population that it describes, and not one of them can be detected by inspecting one's own results."],

["p", "That asymmetry is the reason this chapter is the longest in the book, and it is the reason that treatments of observational data which begin at the propensity model begin too late. The failure mode for which statistical training prepares researchers, namely a biased estimate, is the rarer of the two. The more common one is an estimate that is correct but is about the wrong people, and the only defence against it is knowing what was done to the file and recording it."],

["p", "For comparison, the difference between nearest-neighbour matching and inverse probability weighting, which is the choice that occupies Chapters 5 and 6 and much of the methodological literature, is approximately one percentage point of bias across the 200 draws of Chapter 9, and a few points in the trimmed comparisons of Chapter 7, which is small against the spread of either estimate from one draw to the next. That comparison is the argument of this chapter and, in a sense, of this book. It is not that the estimators do not matter; it is that they are being asked to carry weight that the data preparation has already placed elsewhere."],
["h3", "2.9.4  Scripts for this chapter"],

["tab", "2.10", "Scripts for Chapter 2. All available from the companion website.",
  [1100, 3400, 3200, 1326],
  ["Script", "File", "Produces", "Runtime"],
  [
    ["2.1", "ch02/02_01_load_modules.py", "The nine modules profiled; Table 2.3", "5 s"],
    ["2.2", "ch02/02_02_coverage_and_units.py", "Figure 2.1", "10 s"],
    ["2.3", "ch02/02_03_plida_sim_properties.py", "The generator summary in 2.3", "5 s"],
    ["2.4", "ch02/02_04_covariate_sets.py", "Tables 2.1 and 2.2", "40 s (4 min with --placement)"],
    ["2.5", "ch02/02_05_link_modules.py", "The linked file; Table 2.4", "20 s"],
    ["2.6", "ch02/02_06_reshape_panel.py", "The analysis file; Table 2.5", "20 s"],
    ["2.7", "ch02/02_07_missingness_experiment.py", "Tables 2.6 and 2.7; Figure 2.2", "3 min"],
    ["2.8", "ch02/02_08_attrition.py", "Table 2.8", "15 s"],
    ["2.9", "ch02/02_09_score_against_truth.py", "Table 2.9; the scoring used throughout", "10 s"],
  ],
  "Script 2.4 produces Table 2.2 only when run with --placement, because that table needs six independent draws. Script 2.7 generates its own draws for the same reason and ignores --datadir.",
  ["l", "l", "l", "r"]
],
["h3", "2.9.5  Further reading"],

["p", "Leite (2017, chapter 2) offers the most practical treatment of covariate selection and missing data in a propensity score context, and its framing of the three covariate types is the one adopted here. Holmes (2014) is the best short treatment of variance estimation with matched, and therefore correlated, samples. Bai and Clark (2019, chapter 2) covers the same ground with more attention to the theoretical justification for covariate selection, and their Chapter 1 is the clearest short statement of the assumptions under which propensity score methods are appropriate at all. For missing data specifically, the distinction between mechanisms originates with Rubin (1976), and any modern treatment of multiple imputation will be more thorough than this chapter needs to be. On the consequences of conditioning on post-treatment variables, Rosenbaum (1984) remains the clearest short statement."],

["p", "For the Australian data environment, the ABS documentation on the Person Linkage Spine and the PLIDA Modular Product is essential reading before any DataLab project, and the linkage quality reports for each module deserve more attention than they commonly receive."],
["h3", "2.9.6  Exercises"],

["p", "Every script named in this chapter is listed in Table 2.10 and is available from the companion website. The exercises use PLIDA-SIM B, a second dataset with the same structure and different realised values, so that answers cannot be carried over from the worked examples. It is generated by passing --variant B to the data generator."],

["list", [
  "Build the analysis file for PLIDA-SIM B following Sections 2.5 and 2.6. Report the row count after each merge and confirm that the person count never changes.",
  "Compute the coverage table behind Figure 2.1(a) for the variant. Does the income support module show the same post-treatment fall? Explain what would have to be true of the programme for it not to.",
  "Profile the people with no 2016 tax record, as in Section 2.7.2. Compare the standardised differences with those reported for the primary dataset and account for any that differ in sign.",
  "Fit a propensity model including referral_type. Report what happens and explain it. Then fit the same model with mutual_obligation_status in its place and compare the distribution of fitted scores.",
  "Estimate the attrition rate by treatment arm. Using only covariates observed for everyone, write the two-sentence description of how leavers differ from stayers that you would include in a report.",
]],
["h3", "2.9.7  Study questions"],

["p", "The exercises above require the data and a Python environment. The questions below do not, and they are intended to check that the reasoning of the chapter has carried, rather than the mechanics."],

["list", [
  "Why is a variable that is recorded only for participants inadmissible as a covariate, even when the fact it records was determined before treatment began?",
  "A colleague reports that chaining inner joins across four modules retained 70 per cent of the sample, and that the estimated treatment effect barely moved as a result. Why is this reassuring answer the wrong thing to be reassured by?",
  "Distinguish between a preparation decision that biases the estimate and one that changes the estimand. Why is the second harder to detect, and which internal checks will fail to reveal it?",
  "The six missing data strategies in Table 2.7 differ from one another by less than the variation between draws, with one exception. What is the exception, why does it behave differently, and what does that imply about how much effort a researcher should devote to selecting among the remaining five?",
  "Complete-case analysis produced the smallest mean bias in Table 2.7. Give two reasons why it is nonetheless not the recommended choice.",
  "Occupation is offered in Section 2.4 as a pure outcome predictor. Explain how reading it from the treatment year alone would make that description false, and what the carry-forward procedure in Section 2.6.3 repairs.",
  "Attrition in these data is higher among participants than among non-participants. Does this bias the estimated ATT, change the population to which it refers, or both? Justify your answer.",
]],

];
