# Rubric templates for the three highest-failure bounty types

Each template has a matching JSON file (`template_*.json` in this folder) in the `rubric-1` format, and each one passes `rubric_preflight.py` with no HIGH findings. The thresholds come from the empirical table in the report (section 2): the highest threshold band where the observed pass rate for that task type stayed at 50% or more.

The design rule behind all three: **gates only for disqualifiers the jury can judge from the attached files; everything else weighted.** In the data, a single juror failing a gate is the most common way a strong submission is rejected (report, section 3).

---

## 1. Publish-and-prove (social posts, public answers, forum replies)

**Why it fails today.** Social posts pass 31% of the time (n=125): 73% at thresholds of 85–89, but 14% at 90+ (n=87). The typical rejected submission is good on content but fails a gate on evidence the jury cannot check. Examples: an exact publication time that the platform does not display (#379: 57%, with both Claude jurors at 90.5 and 85.65), a URL the jurors cannot open (#354, LinkedIn), or a handle mismatch spotted by one juror only (#241).

| Item | Choice | Rationale |
|---|---|---|
| Threshold | **85** | Stays below the 90 cliff: social posts pass 73% at 85–89 against 14% at 90+. |
| Gate 1 | On-task and safe | A genuine disqualifier, judged from the pasted text. |
| Gate 2 | Record present: (a)-(e) not *absent* | Gates presence, not verifiability. Explicitly accepts a relative time with a best UTC reading (as #385 did), and says "do not fail because you cannot open the URL". |
| Weighted | substance 0.40, fit to venue 0.25, evidence quality 0.20, disclosure and craft 0.15 | Evidence problems lower the score instead of zeroing a juror. |
| Jury note | Web access may be off, so judge from the files; relative times are expected | Removes the two most common false vetoes. |

## 2. Research table / fact-check

**Why it fails today.** Jurors treat post-training-cutoff sources as invented. For example, the "forward-dated" and "fabricated citation" language in #151 and #387, where a real 2026 *Journal of Graph Theory* paper was called fictitious. Rows without a dated, quoted source are also punished unevenly between jurors.

| Item | Choice | Rationale |
|---|---|---|
| Threshold | **85** | Below 90, the threshold is not what sinks research tasks (32% pass at 75–84, 56% at 85–89); gates and "fabrication" judgments are. 85 keeps headroom for per-row deductions. |
| Gate 1 | No fabrication, defined as contradiction rather than unfamiliarity | Keeps the anti-fabrication gate, but stops "I don't recognise this paper" from counting as a failure. |
| Weighted | coverage 0.30, support 0.35, recency and relevance 0.20, clarity 0.15 | "Every row must have a source" becomes a per-row deduction, not a veto. |
| Evidence rule | Verbatim quote of 40 words or fewer per row; screenshots for sources after Jan 2025 | Gives the jury something to check without web access. |
| Jury note | Treat attached quotes and screenshots as authoritative; recent dates are expected | Directly addresses the cutoff failure mode. |

## 3. Open-problem mathematics

**Why it fails today.** 0 of 12 open-problem submissions have passed, all at thresholds of 90+. Two separate mechanisms are visible in the justifications:

- **(a)** the bounty's own statement of the state of the art is stale. #387 says R(5,5) ≤ 48 when ≤ 46 has been published, so a juror cannot tell "new" from "known".
- **(b)** one juror applies an "extraordinary claim, no peer review" prior that no self-contained proof can satisfy. In #151, gpt-5.6-sol scored the proof at 95.5 while claude-sonnet-5 scored it at about 15 with zero post-2008 dependencies.

| Item | Choice | Rationale |
|---|---|---|
| Threshold | **80**, or 90 with a 3-model jury | At 95 with two equal jurors, one skeptical juror caps the score near 50 whatever the proof's quality. |
| Gate 1 | Claims a strictly better bound than the stated state of the art | Novelty measured against the description, which the creator keeps current. |
| Weighted | correctness 0.50 ("check the steps; don't lower the score because the claim is surprising or unreviewed"), rigor 0.30, clarity 0.20 | Moves the peer-review prior out of the score explicitly. |
| Jury note | The stated state of the art is current and may postdate your training; a correct proof of an open problem is unpublished by nature | Addresses both mechanisms. |
