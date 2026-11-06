# verdikta-rubric-preflight

An offline checker for draft [Verdikta](https://bounties.verdikta.org) bounty rubrics. It flags the rubric patterns that, in the public bounty data, lead to split AI juries and missed thresholds. Each warning cites the data it rests on.

It comes with three rubric templates for the bounty types that fail most often.

## Quick start

Requires Python 3.8+ and the standard library only. It makes no network calls.

```
python3 rubric_preflight.py templates/template_publish_and_prove.json
python3 rubric_preflight.py my_draft.json --threshold 90
python3 rubric_preflight.py my_draft.json --json      # machine-readable output
```

The input is the `rubric-1` JSON used in Verdikta evaluation packages (`title`, `description`, `criteria[]` with `weight` and `must`). You can add an optional `threshold` and a `juryNotes` field. The exit code is `1` if any HIGH finding is raised, so the checker can gate a publishing script.

If you have reviewed a finding and decided to accept the risk, pass `--accept RULE` (repeatable), or list it in the rubric as `"preflightAccept": ["task_type_never_passed"]`. The finding is still printed, marked `ACCEPTED`, but it no longer fails the exit code.

## What it checks

| Rule | Level | Based on |
|---|---|---|
| `threshold_above_ceiling` | HIGH (90+) / MEDIUM | Pass rate by task type and threshold band. Overall, 58% of submissions pass at 85–89 and 15% at 90+. |
| `task_type_never_passed` | HIGH | Open-problem math: 0 of 12 submissions passed. |
| `split_jury_math` | HIGH | With 2 equally weighted jurors, one failed gate caps the score near 50. |
| `unverifiable_gate` | HIGH | Gates like "live", "published" or "genuine venue": 52 of 109 juror gate failures, and the other juror disagreed 56% of the time. |
| `too_many_gates` | MEDIUM | Split rate among rejections: 15% with 1 gate, 28–53% with 2 or more. |
| `url_only_evidence` | HIGH | Jurors' fetches to X, Reddit, Quora, LinkedIn and Facebook return `url_not_allowed`. |
| `relative_timestamp` | HIGH / MEDIUM | Platforms that show only "Just now" (e.g. #379: 57%, failed on the record gate alone). |
| `missing_jury_context` | MEDIUM | Post-cutoff sources called "fabricated" (#151, #387), and venues the jury cannot open. |
| `weights_sum` | HIGH | Scored weights must sum to 1.0. |

## Data and versioning

The empirical table in `rubric_preflight.py` (`EMPIRICAL`) is generated from public Verdikta data: `/api/jobs/<id>` for bounties 1–391, plus the justifications and rubrics on IPFS, pulled on 2026-11-06. It is recalibrated at each data refresh. Each refresh will be a tagged release, with what changed noted below.

| Version | Data | Notes |
|---|---|---|
| v1.0 | Bounties 1–391 (2026-11-06) | Initial release |
| v1.0.1 | same | `missing_jury_context` now recognises any populated jury-notes field (`juryNotes`, `jury_notes`, `juryContext`, `notes`…); new `--accept` / `preflightAccept` for reviewed risks |

## Dataset

The data behind the checker is in [`data/v1.0/`](data/v1.0/): bounties, submissions and per-juror failures as CSV, with the exclusions documented. Please cite the version you use.

## Templates

See [`templates/README.md`](templates/README.md). There are three templates: publish-and-prove, sourced research table, and open-problem math. Each has a threshold, the rationale for where its gates go, and jury notes. All three pass the checker with no HIGH findings.

## Limitations

- Task type is assigned by keyword rules on the title and description, so it is approximate.
- The thresholds and rates are correlations from one platform's history, not guarantees.

## License

MIT. Author: David Rodriguez ([@drdz23](https://github.com/drdz23)).
