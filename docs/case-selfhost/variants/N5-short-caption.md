# PaperPipe: An Evidence-Gated Pipeline for DeepSeek-Style Technical Reporting

## Abstract

Large language models reproduce the surface of a technical report within a few prompts, yet our
own attempts to obtain a DeepSeek-style report from a project record failed in a consistent
way: the prose was fluent, the section order was correct, and the numbers were invented. To
further push the boundary of what a writing assistant can be trusted with, we present
PaperPipe, a six-stage pipeline that fixes the order in which information must exist before
prose is allowed, namely genre, evidence ledger, mined research points, skeleton, tool-rendered
artifacts, and a deterministic gate check. On a draft produced through the pipeline we reach 12
on GateLint, the number of hard gates satisfied, and on the same checker a naive control draft
written without any stage of the pipeline reaches 2 on GateLint, failing ten of twelve gates
across the abstract, the contribution block, the navigation paragraph, the figure caption, and
the failure declaration. Because the pipeline itself contains no trainable weights, we report 0
total parameters with 0 activated parameters per step, and what it adds instead is 161,739 bytes
of protocol payload across 23 files; building the pipeline consumed 2.04M tokens and 0 GPU
hours, since no stage performs gradient-based training. We also report a defect that our own
checker misses: a comparison verb inserted without a supporting entry passes the gate that is
supposed to catch it, because that gate counts admissible entries rather than verifying them.
The released protocol and tools are available at https://github.com/zh2673-git/deepseek-paper.

## 1 Introduction

We wrote this paper with the very pipeline it describes, which makes the record unusually
complete and the failure modes unusually visible. Our starting observation was not that models
write badly; it was that models write plausibly and cite nothing. A control draft of 958
characters, produced by the most natural prompt we could write, opened with the three-part
template that our gates exist to reject, namely a self-praising adjective, an unscoped
superlative claim, and no number in the same sentence; it placed a related-work chapter as
Section 2 and reported a score of 88.4 for a method that had never been run. Every defect in
that draft was a defect of provenance rather than of style.

To turn the observations that define the DeepSeek report family into an executable protocol, we
fix the sequence of six stages and forbid skipping, because each stage constrains the input of
the next. Firstly, a ledger is built from the project directory before a sentence is written,
and every entry is downgraded to `todo` until a person binds it to a claim. Secondly, research
points are mined along five fixed interrogation lines, at most one main point per line, which
converts an unbounded pile of observations into an explicit set of trade-offs. Furthermore,
every figure and table is rendered from a structured description, so that a number has exactly
one home. Lastly, twelve hard gates inspect the finished text for the markers that our corpus
study found to be invariant across the twenty DeepSeek reports, and a separate ten-item rubric
scores what the gates cannot see.

Our main contribution includes:

Evidence discipline: a ledger that precedes the prose

- We design a two-stage ledger in which a scanner enumerates candidate sources and a person
  assigns the claim, the value, and the scope, which makes every admitted number traceable.
- We make the writing stage read-only with respect to numbers, which removes the selection
  pressure that produced the invented scores in our control draft.

Mining budget: one research point per interrogation line

- We propose five fixed interrogation lines, namely anomaly, trade-off, reuse, failure, and
  cost, which converts an unbounded pile of observations into an explicit set of trade-offs.
- We impose a budget of one headline claim per line, which bounds how many points a draft may
  carry and forces the remainder into the discussion section.

Deterministic gates: style as a predicate

- We introduce twelve gates G1–G12 that turn a measurable subset of "does it read like a
  DeepSeek report" into a pass/fail computation over plain text.
- We report the cost of that transformation, namely that the gates encode necessary conditions
  only, rather than presenting them as a delivery criterion.

Tool-rendered artifacts: one home for every number

- We design a structured description plus a renderer for tables and figures, which removes
  hand-copied cells and their drift against the text.
- We measure what the elimination leaves uncovered, namely value verification rather than value
  binding.

### 1.1 Summary of Evaluation Results

On the mechanical axis, a draft produced through the full pipeline satisfies 12 on GateLint, and
three of four fault-injected variants derived from it lose exactly 1 gate each, so a single
injected fault is isolated rather than masked by an aggregate; the fourth variant, which inserts
a comparison verb with no supporting entry, loses 0 gates, and we report it as a hole rather
than repair it silently. On the statistical axis, the twelve regression cases reach 1.00 on
EvalSuite over the eleven cases that carry a decidable signal, the twelfth being a judged case that
stays pending until a judge command is supplied. The naive control draft satisfies 2 on GateLint
and fails ten gates, and the two gates it satisfies are the only two that cannot fail on a short
text, since it contains neither a figure nor a comparison verb.

In the remainder of this paper, we first present the pipeline as six stages and explain why the
order is not negotiable (Section 2). We then describe the implementation, the tool protocol, and
the payload budget (Section 3). Next, we report the gate behaviour, the fault-injection matrix,
and the ablation of gate groups (Section 4). Thereafter, we discuss three failed attempts and
the mechanism behind each of them (Section 5). Lastly, we conclude, state two limitations with
their causes, and outline future directions (Section 6).

## 2 Approach

The pipeline is a fixed sequence of six stages. We organize this section by the order in which
the stages were forced upon us by observed failures, rather than by module boundary, because
each stage exists to close a hole that the previous stage left open.

### 2.1 Overview: the order is the mechanism

A stage may not be skipped, because each stage restricts the input of the next. Genre restricts
the skeleton, the skeleton restricts which sections need evidence, the ledger restricts which
numbers may appear at all, the mining budget restricts how many headline claims survive, and the
gates reject any draft whose numbers cannot be traced. A pipeline that lets the writer choose
the genre after the evidence is collected will systematically choose the genre for which the
available evidence happens to be sufficient, which is exactly the behaviour we wanted to remove.

### 2.2 Evidence Ledger: making every number traceable

We design the ledger as a list of entries carrying an identifier, a kind, a claim, a value, a
unit, a scope, a source, a status, and a list of the places where the entry is used. A scanner
enumerates candidate files under the project root, classifies each as a measurement, a
configuration, or an artifact, and attaches the first three lines of the file together with a
flag recording whether the file contains digits. Every generated entry starts at `todo`, which
means that no person has yet decided what the file is evidence for, and the writing stage may
consume only entries whose status is `ok`.

The consequence is deliberately annoying. On this project the scanner produced 27 entries and
all 27 were `todo`, so the first writing attempt had, in principle, no admissible number at all.
We regard the annoyance as the mechanism, because the alternative, letting the writer read the
directory and select numbers freely, is how the invented score in the control draft came to
exist.

### 2.3 Five-Line Mining: one point per line

We propose to interrogate a project along exactly five lines: anomaly, meaning which
observation contradicted expectation; trade-off, meaning what was given up and at what cost;
reuse, meaning which component appears in more than one place; failure, meaning which attempt
did not work and why; and cost, meaning what is cheaper than the conventional route and by how
much. Each line may yield at most one main research point, and a point must be expressible as a
section title of the form `<mechanism>: <gain>`. On this project the five lines produced the
four mechanisms of Sections 2.2 to 2.5 plus one discarded candidate, and no line produced two
headline points.

### 2.4 Deterministic Gates: turning style into a predicate

We introduce twelve gates over plain text in three groups. The provenance gates demand numbers
to be present, to be paired, and to carry a unit (G1–G4). The structural gates demand a grouped
contribution block, a navigation paragraph with cross-references, the absence of a standalone
related-work chapter, and captions of at least two sentences (G5–G8). The honesty gates demand
at least one failure declaration, a cost note, no forbidden phrase, no orphan figure, and a
comparison verb backed by a traceable entry (G9–G12).

The trade-off is explicit and we state it rather than hide it: a gate is a regular expression or
a structural scan, so it can be satisfied by a draft that is stylistically correct and
substantively empty. Section 5.2 quantifies this gap and Section 6 explains why we keep the
gates anyway.

### 2.5 Tool-Rendered Artifacts: one home for every number

We design the artifact path so that a table cell exists in exactly one place. The author writes a
structured description holding the caption lead, the caption tail, the column list, the group
column, the highlight policy, and the rows; a renderer emits booktabs LaTeX and Markdown and
applies the best and second-best marking under a same-level tolerance. A figure description is
handled the same way, and the renderer applies a three-line grid and a single accent colour. The
cost is that no artifact can be produced before its data is structured, which front-loads work
that a person would otherwise do by hand at the very end.

## 3 Implementation

The pipeline ships as one protocol document, six reference documents, five templates, four
tools, five registry documents, and an evaluation suite: 23 files totalling 161,739 bytes, of
which the registry is the largest single block because it carries excerpts from the twenty
source reports and the reconstruction of the profession behind the pipeline. Table 1 gives the
composition.

**Table 1: Payload composition of the pipeline. Files and bytes are counted on the released tree and the shares are rounded to one decimal place. The registry is read on demand rather than per step, so its share of the payload is not its share of the activated context. Because the rows carry different file counts, no cell is marked as best, and shares within 0.1 points are at the same level.**

| Area | Files | Bytes | Share (%) |
|---|---|---|---|
| Registry | 5 | 65793 | 40.7 |
| References | 6 | 35467 | 21.9 |
| Tools | 4 | 29197 | 18.1 |
| Templates | 5 | 12566 | 7.8 |
| Evaluations | 3 | 18716 | 11.6 |

Totals are 23 files and 161,739 bytes; the five shares sum to 100.1 because of rounding.

All four tools speak the same protocol: JSON on standard input under an `args` key, and JSON on
standard output carrying a status flag and a result object. Only the figure renderer depends on
a third-party package, while the other three use the standard library alone, which keeps the
gate check runnable on a machine without a plotting stack. The tools are small by construction:
163 lines for the scanner, 169 for the table renderer, 154 for the figure renderer, and 250 for
the gate checker.

Note that the aforementioned costs include only the construction of the pipeline itself,
excluding the cost of reading and excerpting the twenty source reports that the registry
depends on.

## 4 Evaluation

### 4.1 Settings

We use two suites. GateLint runs the twelve gates over a draft and reports a per-gate verdict
together with the evidence that produced it. EvalSuite holds twelve regression cases, each with
an input and an expected behaviour, scored by three signal types, namely an assertion for
mechanical checks, a rubric for scored quality, and a separate model call for judged cases. Eleven
of the twelve cases carry a decidable signal, and the twelfth stays pending by design until a
judge command is supplied.

Three kinds of draft are used: a compliant draft written through the full pipeline, a naive
control draft written without any stage of the pipeline, and four fault-injected variants
derived from the compliant draft, each carrying exactly one realistic defect. Table 2 reports
the outcome for every draft.

**Table 2: Gate outcomes on the compliant draft, the naive control, and four fault-injected variants. Each cell gives the number of the twelve hard gates satisfied, so a higher value is better everywhere in the table and no column inverts the direction of merit. Every draft is scored by the same checker at the same version and under the same genre, and counts within one gate of each other are regarded as at the same level. The unbacked-claim row is the exception discussed in Section 5.2: its defect survives because the ledger cross-reference counts entries rather than verifying them.**

| Draft | Gates satisfied (of 12) | Gates failed | Verdict | Defect injected |
|---|---|---|---|---|
| Compliant | **12** | 0 | PASS | none |
| Naive control | 2 | **10** | FAIL | unwritten provenance |
| N2 no numbers | **11** | 1 | FAIL | abstract without scores |
| N3 orphan figure | **11** | 1 | FAIL | figure never referenced |
| N4 unbacked claim | **12** | 0 | PASS | comparison verb, count-based check |
| N5 short caption | **11** | 1 | FAIL | one-sentence figure caption |

'PASS' denotes that all twelve gates were satisfied, not that the draft is deliverable; see Section 5.2.

'PASS' denotes that all twelve gates were satisfied, not that the draft is deliverable; see Section 5.2.

'PASS' denotes that all twelve gates were satisfied, not that the draft is deliverable; see Section 5.2.

Figure 1 presents the same measurement as a bar chart, which makes the isolation property
visible at a glance: the distance between the compliant draft and a caught fault is exactly one
gate, while the distance to the naive control is ten. As illustrated, the gates behave as
independent detectors rather than as a single aggregate score, and the one bar that does not
drop is the one defect the checker cannot see.

**Figure 1: Gate counts across six drafts.**

![Gate counts](figures/fig1.png)

### 4.2 Ablation of gate groups

Table 3 is a reasoned ablation rather than a measured one, and we label it that way. Each row
removes one group of gates and records the class of defect that then escapes detection; we did
not re-run the checker with gates compiled out, so the table states what the gate definitions
imply rather than what an experiment produced. Removing the provenance group lets an abstract
without any score pass, which is the behaviour the naive control exhibits by default. Removing
the structural group lets a one-sentence caption and a missing contribution block pass. Removing
the honesty group lets a comparison verb with no traceable entry pass, and N4 in Table 2 shows
that this defect escapes detection even with the ledger supplied, so the honest reading of the
third row is that the class is already open in the shipped version.

**Table 3: Ablation of gate groups, reasoned from the gate definitions rather than measured by recompiling the checker. Each row removes one group of gates and records the class of defect that then escapes detection. The last row is the one whose consequence a reader cannot see unaided, and because the rows are independent rather than ordered levels there is no digit column to receive a best marking, while the yes and no verdicts are at the same level of confidence rather than a ranking.**

| Group removed | Gates | Defect that survives | Visible to reader |
|---|---|---|---|
| Provenance | G1-G4 | abstract without scores, unpaired scale | yes |
| Structural | G5-G8 | one-sentence caption, ungrouped contributions | yes |
| Honesty | G9-G12 | unbacked comparison, no failure declaration | no |

'Visible to reader' means detectable without running the checker, by reading the draft once.

'Visible to reader' means detectable without running the checker, by reading the draft once.

'Visible to reader' means detectable without running the checker, by reading the draft once.

### 4.3 What the numbers do not show

Three features of Table 2 deserve to be stated plainly rather than left to the reader. The first
is that the two gates surviving in the naive control survive for a degenerate reason, so its
count of 2 is not evidence that it satisfies anything. The second is that the four variants are
not independent draws from a distribution of defects but four hand-chosen edits, so the table
demonstrates detection on the cases we thought of and says nothing about the cases we did not.
The third is the one we would rather not report: N4 reaches 12, the same count as the compliant
draft, so a comparison verb with no supporting entry is not detected at all, and the honesty
group that Table 3 credits with catching it is weaker than the group name suggests.

## 5 Discussion

### 5.1 Unsuccessful Attempts

Our first attempt was a style prompt, a list of nine hundred words of DeepSeek phrasing to
imitate. It produced prose that a reader familiar with the corpus recognized as adjacent, and it
produced invented numbers every time. The mechanism is straightforward: a phrasing list
constrains surface form and leaves the mapping from claim to measurement unconstrained, so the
path of least resistance is to keep the form and invent the content. A ledger does the opposite,
constraining the mapping and leaving the surface free.

Our second attempt was one long checklist instead of twelve separate gates. We found that a
checklist is read as advice rather than as a predicate: the same draft was scored differently on
two passes, and no item was ever reported as a hard failure. Splitting it into independently
computed gates removed the ambiguity, at the cost of losing the connective reasoning that a
checklist provides in the one place where it is needed, namely judging whether a section earns
its place.

Our third attempt was treating a green gate report as the delivery criterion. We built a draft
satisfying all twelve gates and confirmed afterwards, by reading it, that it was still not
deliverable: the numbers were traceable, the captions were long enough, and the argument was
absent. The mechanism is that the twelve gates encode necessary conditions only. We now score
every draft on ten qualitative items in addition to the gate report, and we keep a negative case
in the regression suite whose only purpose is to remind us that a green report is not a verdict.

### 5.2 Dialogue: what the gates cannot see

A gate over plain text cannot distinguish a number that is correctly sourced from a number that
is sourced to a document which does not contain it. We measured the size of this hole instead of
asserting that it is small. Variant N4 inserts a comparison verb with no supporting entry and is
scored with the ledger supplied. The checker builds its silence gate as a count comparison: it
counts the comparison verbs in the text and counts the admissible comparison entries in the
ledger, and passes the gate whenever the entry count reaches the verb count. Our ledger happens
to carry one admissible comparison entry, so one unbacked verb satisfies the inequality, and N4
reaches 12, the same count as the compliant draft. We report this as a false negative of the
mechanism rather than as a defect of the implementation, and the repair is structural: the gate
has to bind each verb to a named entry instead of comparing two totals. Four qualitative
dimensions remain out of reach of any count-based check, namely argument structure, whether a
section earns its place, whether a cited source actually contains the asserted value, and
whether the register matches the venue.

## 6 Conclusion, Limitations, and Future Directions

In this paper, we introduce PaperPipe, a gated pipeline that turns a project directory into a
technical report in the style of the DeepSeek model reports. The pipeline fixes six stages in an
order that makes provenance a precondition rather than an afterthought, mines at most one
research point per interrogation line, renders every artifact from a structured description, and
checks the finished text against twelve hard gates. A draft produced through the pipeline
satisfies 12 on GateLint, while the naive control satisfies 2 on GateLint, and three of four
injected faults are caught by exactly one gate each while the fourth is caught by none.

While acknowledging its usefulness, we also recognize that the pipeline has some limitations,
especially on the boundary between necessary and sufficient conditions. Firstly, the gates
encode necessary conditions only, so a compliant draft can still be substantively empty; we have
observed this on our own output and now treat the gate report as a floor rather than a verdict.
Secondly, the ledger cross-reference is a comparison of two totals rather than a binding of each
assertion to a named entry, so a comparison verb may satisfy it while citing nothing, which is
exactly what variant N4 demonstrates. Fortunately, these limitations are expected to be naturally
addressed as long as the ecosystem provides machine-readable measurement records rather than
prose summaries.

The pipeline adheres to the route of open protocols rather than of a monolithic tool, aiming to
keep the evidence layer inspectable by a reader. In the future, we plan to strategically invest
in research across the following directions.

- We will extend the ledger from value binding to value verification, so that a gate can check
  whether the cited document actually contains the asserted number.
- We will derive the gate set from the corpus rather than from our reading of it, so that a newly
  published report can update the gates without a manual pass.
- We will add a judgement stage that scores the ten qualitative items with an independent model
  and records its disagreement with the author's own score.
- We will keep a case in the regression suite for every gate that has ever been satisfied by a
  draft we would not deliver.

## References

1. DeepSeek-AI. DeepSeek-V3 Technical Report. arXiv:2412.19437, 2024.
2. DeepSeek-AI. DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. arXiv:2501.12948, 2025.
3. DeepSeek-AI. DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model. arXiv:2405.04434, 2024.
4. DeepSeek-AI. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300, 2024.
5. DeepSeek-AI. DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models. arXiv:2401.06066, 2024.
6. DeepSeek-AI. DeepSeek LLM: Scaling Open-Source Language Models with Longtermism. arXiv:2401.02954, 2024.

## Appendix A Contributions and Acknowledgments

The pipeline was designed and implemented as a single-author project. The corpus excerpts were
collected from the public renderings of the twenty reports listed in the registry. We thank the
maintainers of the agent runtime whose skill-loading mechanism made a package of one protocol
plus four tools a natural unit of distribution.

## Appendix B Fault-Injection Cases

Each case is a localized edit to the compliant draft. Table 4 lists the edit and the gate that
fires, and reports N4 as the case where no gate fires.

**Table 4: Fault-injection cases. Each row applies one realistic defect to the compliant draft and records which gate detected it, if any. Because the detection column mixes gate names with a null marker, no cell is marked as best, and the four cases are independent edits rather than a difficulty ordering, so all four are regarded as at the same level.**

| Case | Edit applied | Gate fired | Gates satisfied |
|---|---|---|---|
| N2 | remove all scores from the abstract | G1 | 11 |
| N3 | drop the in-text reference to the figure | G11 | 11 |
| N4 | insert a comparison verb with no supporting entry | none | 12 |
| N5 | shorten a figure caption to one sentence | G8 | 11 |

'none' denotes a defect the checker does not detect; it is reported rather than repaired, and Section 5.2 explains why.

'none' denotes a defect the checker does not detect; it is reported rather than repaired, and Section 5.2 explains why.

'none' denotes a defect the checker does not detect; it is reported rather than repaired, and Section 5.2 explains why.

## Appendix C Gate Definitions

The twelve gates are defined over plain text with regular expressions and structural scans, and
each returns a verdict together with the evidence that produced it, namely the matched span, the
count, or the offending line. A strict mode treats any failed gate as an overall failure, and a
permissive mode returns the same verdicts without failing the run, which is used when the author
wants the full list of problems in a single pass.
