# Dataset v1.0: Verdikta bounties 1–391 (pulled 2026-11-06)

Derived only from public endpoints:
- `GET https://bounties.verdikta.org/api/jobs/<id>`, for ids 1 to 391;
- each submission's `justificationCids` and each bounty's `rubricCid`, read from IPFS.

The pull returned 465 justifications and 367 rubrics. No API key or private data was used. Wallet addresses are the public on-chain hunters and creators.

| File | Rows | Content |
|---|---|---|
| `verdikta_bounties.csv` | one per bounty | taskType, threshold, prize, jury size, gates, passRate, timeToWinnerMin, wonByFirstSubmission |
| `verdikta_submissions.csv` | one per evaluated submission | score, passed, minutesFromOpen, jurorFailures, gateType, splitJury, timeToWinner, passRate |
| `verdikta_juror_failures.csv` | one per juror per rejected submission with a justification | model, failedGate, gateId, gateType, quoted reason |

## Exclusions used for all statistics

The rows stay in the files; filter on these columns to get the statistics base:

- `excludedSelfAwarded = 1`: **73 bounties** where the creator won their own bounty (early platform tests).
- `scoreRecorded = 0`: **85 submissions** approved while the platform recorded a score of 0 (old single-juror and early flows).

After these exclusions the base is 318 bounties (258 awarded) and 422 jury-scored submissions.

## Caveats

- `taskType` comes from keyword rules on title and description, so it is approximate.
- Per-juror verdicts are extracted from the aggregated justification text. A manual check of 41 verdicts found 39 correct.

## Citing

Please cite the version, e.g. "Verdikta dataset v1.0 (bounties 1–391, 2026-11-06), github.com/drdz23/verdikta-rubric-preflight". Each monthly delta adds a new `data/vX` folder; older versions are never edited.
