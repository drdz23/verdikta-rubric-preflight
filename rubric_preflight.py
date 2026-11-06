#!/usr/bin/env python3
"""
rubric_preflight.py - flag risky patterns in a draft Verdikta rubric before you publish it.

Standard library only. Makes no network calls.

Usage:
    python3 rubric_preflight.py draft_rubric.json [--threshold 85] [--jurors 2] [--json]

Input: a Verdikta rubric JSON (the "rubric-1" format used in evaluation packages):
    {
      "title": "...",
      "description": "...",
      "threshold": 85,                # optional, can be given with --threshold instead
      "criteria": [
        {"id": "g1_published", "description": "...", "weight": 0,   "must": true},
        {"id": "accuracy",     "description": "...", "weight": 0.4, "must": false}
      ],
      "juryNotes": "..."              # optional free text with background for the jury
    }

Every rule below comes from a pattern measured in the public Verdikta bounty data
(bounties #1-391; see the report). Each warning names the evidence it is based on.

Exit code: 0 = no HIGH findings, 1 = at least one HIGH finding, 2 = bad input.
"""
import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# Empirical data (filled from the dataset; see report section 2).
# For each task type: the per-submission pass rate observed at each threshold band,
# and the highest threshold band where the observed pass rate stayed >= 50%.
# ---------------------------------------------------------------------------
EMPIRICAL = {
    "social_post": {
        "n": 125,
        "pass_by_band": {
            "<75": None,
            "75-84": 0.6,
            "85-89": 0.73,
            "90+": 0.14
        },
        "n_by_band": {
            "<75": 0,
            "75-84": 5,
            "85-89": 33,
            "90+": 87
        },
        "safe_ceiling": 89
    },
    "writing": {
        "n": 129,
        "pass_by_band": {
            "<75": 0.71,
            "75-84": 0.59,
            "85-89": 0.44,
            "90+": 0.15
        },
        "n_by_band": {
            "<75": 7,
            "75-84": 32,
            "85-89": 57,
            "90+": 33
        },
        "safe_ceiling": 84
    },
    "trivia_qa": {
        "n": 4,
        "pass_by_band": {
            "<75": None,
            "75-84": None,
            "85-89": None,
            "90+": None
        },
        "n_by_band": {
            "<75": 2,
            "75-84": 1,
            "85-89": 1,
            "90+": 0
        },
        "safe_ceiling": None
    },
    "b4b": {
        "n": 19,
        "pass_by_band": {
            "<75": None,
            "75-84": 0.64,
            "85-89": None,
            "90+": None
        },
        "n_by_band": {
            "<75": 0,
            "75-84": 14,
            "85-89": 3,
            "90+": 2
        },
        "safe_ceiling": 84
    },
    "other": {
        "n": 22,
        "pass_by_band": {
            "<75": None,
            "75-84": 0.27,
            "85-89": 0.63,
            "90+": None
        },
        "n_by_band": {
            "<75": 3,
            "75-84": 11,
            "85-89": 8,
            "90+": 0
        },
        "safe_ceiling": 89
    },
    "math_open_problem": {
        "n": 12,
        "pass_by_band": {
            "<75": None,
            "75-84": None,
            "85-89": None,
            "90+": 0
        },
        "n_by_band": {
            "<75": 0,
            "75-84": 0,
            "85-89": 0,
            "90+": 12
        },
        "safe_ceiling": None
    },
    "research_verify": {
        "n": 73,
        "pass_by_band": {
            "<75": None,
            "75-84": 0.32,
            "85-89": 0.56,
            "90+": 0.5
        },
        "n_by_band": {
            "<75": 2,
            "75-84": 47,
            "85-89": 18,
            "90+": 6
        },
        "safe_ceiling": 89
    },
    "textbook_math_logic": {
        "n": 20,
        "pass_by_band": {
            "<75": None,
            "75-84": 0.85,
            "85-89": 1,
            "90+": None
        },
        "n_by_band": {
            "<75": 0,
            "75-84": 13,
            "85-89": 5,
            "90+": 2
        },
        "safe_ceiling": 84
    },
    "code": {
        "n": 18,
        "pass_by_band": {
            "<75": None,
            "75-84": 0.71,
            "85-89": 0.75,
            "90+": None
        },
        "n_by_band": {
            "<75": 2,
            "75-84": 7,
            "85-89": 8,
            "90+": 1
        },
        "safe_ceiling": 89
    },
    "_all": {
        "n": 422,
        "pass_by_band": {
            "<75": 0.75,
            "75-84": 0.51,
            "85-89": 0.58,
            "90+": 0.15
        },
        "n_by_band": {
            "<75": 16,
            "75-84": 130,
            "85-89": 133,
            "90+": 143
        },
        "safe_ceiling": 89,
        "odds_per_10": 0.37
    }
}

TASK_TYPE_RULES = [
    # (task type, regex over title + description), first match wins
    ("b4b", r"bounty-for-bounty|\bb4b\b|create (and fund )?(a|your|one) (first |own )?(verdikta )?bounty|recruit a first-time verdikta creator"),
    ("math_open_problem", r"perfect cuboid|ramsey number|erd(o|ő)s|lonely runner|hadwiger|chromatic number of the plane|collatz|riemann|goldbach|twin prime|\bconjecture\b"),
    ("textbook_math_logic", r"\b(prove (it|that)|theorem|formula|principle|probability|combinatorics|modular arithmetic|logic puzzle|knights and knaves|chess puzzle|cipher|derive)\b"),
    ("trivia_qa", r"\b(identify the|name the|capital of|answer (ten|\d+) .{0,30}questions|find verdikta.s official)\b"),
    ("code", r"\b(python|sql|script|pull request|merged?|github|repo(sitory|s)?|awesome list|agent-tools directory|ecosystem page)\b"),
    ("social_post", r"\b(linkedin|reddit|tweet|x thread|twitter|quora|hacker news|social post|moltbook|post (it )?(publicly|on (a|your|any|one))|publish (it )?(publicly|on))\b"),
    ("research_verify", r"\b(fact-check|verify|claims|research|sourced map|audit|comparison|compare|survey|study)\b"),
    ("writing", r"\b(blog|guide|article|story|explain(er)?|essay|case study|report|write|faq|proposal|campaign)\b"),
]

RELATIVE_TIME_PLATFORMS = ["quora", "x.com", "twitter", "linkedin", "facebook", "instagram", "tiktok", "medium", "discord", "telegram"]
UNOPENABLE_FOR_JURY = ["linkedin", "quora", "x.com", "twitter", "facebook", "instagram", "medium", "substack", "discord", "telegram", "paywall", "login"]
UNVERIFIABLE_GATE_WORDS = [
    r"\blive\b", r"\bexists?\b", r"\bpublished\b", r"\bposted\b", r"\bgenuine\b", r"\bfirst[- ]hand\b",
    r"\bindependently verif", r"\bverif(y|ied|iable)\b", r"\bnot the (creator|same person)\b", r"\bnot (been )?submitted\b",
    r"\bmerged\b", r"\bunique (person|human)\b", r"\boriginal(ity)?\b", r"\bnew result\b", r"\bnovel\b",
]
TIMESTAMP_WORDS = r"(timestamp|publication time|time (posted|published)|posted at|exact (time|date)|utc|as (the )?platform (itself )?displays)"
URL_EVIDENCE_WORDS = r"\b(url|link|permalink)\b"
PASTED_EVIDENCE_WORDS = r"(paste|verbatim|screenshot|full text|complete text|attach|quoted)"
RECENCY_WORDS = r"(arxiv|preprint|20(2[5-9]|3\d)|latest|state of the art|current (best|record|bound)|recent(ly)?|new (paper|release|version))"
JURY_NOTE_WORDS = r"(jury note|note (to|for) (the )?jur|background|context for (the )?jur|evaluable from the submitted text|treat attached|authoritative)"


def classify(title, desc=""):
    # title first (most indicative); the description is a fallback, and trivia is only detected from the title
    for part, allow_trivia in ((title.lower(), True), (desc.lower(), False)):
        for name, rx in TASK_TYPE_RULES:
            if name == "trivia_qa" and not allow_trivia:
                continue
            if re.search(rx, part):
                return name
    return "other"


def band_of(threshold):
    if threshold < 75:
        return "<75"
    if threshold < 85:
        return "75-84"
    if threshold < 90:
        return "85-89"
    return "90+"


def finding(level, rule, message, evidence):
    return {"level": level, "rule": rule, "message": message, "evidence": evidence}


NOTE_KEYS = ("juryNotes", "jury_notes", "juryNote", "jury_note", "juryContext", "jury_context", "notes", "backgroundForJury")


def jury_notes_of(rubric):
    # accept the common spellings, and strings or lists of strings
    parts = []
    for k in NOTE_KEYS:
        v = rubric.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
        elif v:
            parts.append(str(v))
    return "\n".join(parts)


def check(rubric, threshold=None, jurors=2, accept=()):
    out = []
    title = str(rubric.get("title", ""))
    desc = str(rubric.get("description", ""))
    notes = jury_notes_of(rubric)
    criteria = rubric.get("criteria") or []
    full = "\n".join([title, desc, notes] + [str(c.get("description", "")) for c in criteria]).lower()
    if threshold is None:
        threshold = rubric.get("threshold")
    task = classify(title, desc)

    # 0. Structural sanity
    weights = [float(c.get("weight", 0) or 0) for c in criteria if not c.get("must")]
    if criteria and abs(sum(weights) - 1.0) > 0.001:
        out.append(finding("HIGH", "weights_sum", f"Scored criteria weights sum to {sum(weights):.3f}, not 1.0.",
                           "Verdikta requires weights to sum to 1.0 (+-0.001); packages that don't are rejected or mis-scored."))
    gates = [c for c in criteria if c.get("must")]
    bare = [str(c.get("id", "?")) for c in criteria if len(str(c.get("description", "") or "").strip()) < 15]
    if bare:
        out.append(finding("HIGH", "criteria_without_description",
                           f"Criteria with no (or almost no) description: {', '.join(bare)}. The jury scores only what the description says.",
                           "Every other check here reads the descriptions, so an empty one passes silently while giving the jury no definition of pass/fail, bands or exclusions."))
    if len(desc.strip()) < 40:
        out.append(finding("MEDIUM", "task_description_missing",
                           "The rubric has no task description (or a very short one).",
                           "Jurors judge the deliverable against the description; without it, gate wording carries all the interpretation."))

    # 1. Threshold above empirical ceiling for this task type
    if threshold is None:
        out.append(finding("INFO", "threshold_missing", "No threshold given; pass --threshold to check it.", ""))
    else:
        emp = EMPIRICAL.get(task) or EMPIRICAL.get("_all")
        ceiling = emp.get("safe_ceiling")
        rate = (emp.get("pass_by_band") or {}).get(band_of(threshold))
        if ceiling is not None and threshold > ceiling:
            out.append(finding("HIGH" if threshold >= 90 else "MEDIUM", "threshold_above_ceiling",
                               f"Threshold {threshold} is above the empirical safe ceiling ({ceiling}) for task type '{task}'.",
                               f"Observed pass rate for '{task}' in band {band_of(threshold)}: "
                               f"{'n/a' if rate is None else str(round(rate*100))+'%'} (n={emp.get('n_by_band', {}).get(band_of(threshold), 0)}). "
                               f"Overall, each +10 threshold points multiplies the odds of passing by ~{EMPIRICAL['_all'].get('odds_per_10', 0.57)}."))
        known = [v for v in (emp.get("pass_by_band") or {}).values() if v is not None]
        if ceiling is None and known and max(known) == 0:
            out.append(finding("HIGH", "task_type_never_passed",
                               f"No jury-scored submission of task type '{task}' has ever passed ({emp.get('n')} submissions, all bands).",
                               "Treat this as a research bounty: lower the threshold, add a state-of-the-art jury note, and consider a 3-model jury."))
        if threshold >= 90 and jurors == 2 and gates:
            out.append(finding("HIGH", "split_jury_math",
                               "With 2 equally weighted jurors and must-pass gates, one juror failing any gate caps the score near 50, far below a 90+ threshold.",
                               "A failed gate zeroes that juror; the contract averages and rounds down. Rejected submissions cluster at 40-60 for this reason."))

    # 2. Must-pass gates on criteria the jury cannot verify
    for g in gates:
        gt = str(g.get("description", "")).lower()
        hits = [w for w in UNVERIFIABLE_GATE_WORDS if re.search(w, gt)]
        if hits and not re.search(PASTED_EVIDENCE_WORDS, gt):
            out.append(finding("HIGH", "unverifiable_gate",
                               f"Gate '{g.get('id')}' asks the jury to confirm something it usually cannot check from the submitted files ({', '.join(h.strip(chr(92)+'b') for h in hits[:3])}).",
                               "In the data, gates about publication/live evidence produced 52 of 109 juror gate failures (the largest group), and in 56% of them the other juror passed the same submission. "
                               "Make it a weighted criterion, or say exactly which pasted evidence satisfies it."))
    if len(gates) > 3:
        out.append(finding("MEDIUM", "too_many_gates", f"{len(gates)} must-pass gates. Each one is an independent chance for a single juror to zero the submission.",
                           "Split-jury rejections grow with the number of gates; keep gates for disqualifiers only (safety, wrong task, fabrication)."))

    # 3. URL-only evidence
    if re.search(URL_EVIDENCE_WORDS, full) and not re.search(PASTED_EVIDENCE_WORDS, full):
        out.append(finding("HIGH", "url_only_evidence",
                           "Evidence is requested as a URL/link with no requirement to paste the content or attach a screenshot.",
                           "Jurors only see attached files; fetches to LinkedIn, Quora, X etc. return url_not_allowed. Require the full text pasted plus a screenshot."))

    # 4. Relative timestamps
    if re.search(TIMESTAMP_WORDS, full):
        plats = [p for p in RELATIVE_TIME_PLATFORMS if p in full]
        lenient = re.search(r"(relative time|best utc|will not be held against|if (it|the platform) only shows)", full)
        if not lenient:
            out.append(finding("HIGH" if plats or "any platform" in full or "your choice" in full else "MEDIUM", "relative_timestamp",
                               "The rubric demands an exact publication time, but many platforms only display relative times ('Just now', '10m')" +
                               (f" - mentioned here: {', '.join(plats)}." if plats else "."),
                               "Case #379: both Claude jurors scored 90.5/85.65, gpt-5.6-terra failed the record gate on Quora's 'Just now' -> 57%. "
                               "Accept 'best UTC reading if the platform shows only a relative time' (as #385 did)."))

    # 5. Missing jury context notes
    needs_ctx = []
    if re.search(RECENCY_WORDS, full):
        needs_ctx.append("recent literature or results that may postdate the jurors' training data")
    if any(p in full for p in UNOPENABLE_FOR_JURY):
        needs_ctx.append("venues the jurors cannot open")
    if task == "math_open_problem":
        needs_ctx.append("open-problem claims, where jurors apply a strong 'extraordinary claim' prior")
    has_note = len(notes.strip()) >= 40 or re.search(JURY_NOTE_WORDS, full)
    if needs_ctx and not has_note:
        out.append(finding("MEDIUM", "missing_jury_context",
                           "The task depends on " + "; ".join(needs_ctx) + ", and the rubric gives the jury no background note.",
                           "In 408 public justifications, 8 rejected submissions cite sources the jury called fabricated/future-dated (#151, #387) and 17 mention a venue the jury could not open (e.g. #354 LinkedIn). "
                           "Add a jury note with the current state of the art, and tell jurors to treat attached sources as authoritative."))

    # Risks the author has reviewed and accepted: from --accept and/or rubric["preflightAccept"].
    accepted = set(accept) | set(rubric.get("preflightAccept") or [])
    for f_ in out:
        if f_["rule"] in accepted and f_["level"] != "INFO":
            f_["accepted_from"] = f_["level"]
            f_["level"] = "ACCEPTED"

    return {"task_type": task, "threshold": threshold, "gates": len(gates), "findings": out}


def main():
    ap = argparse.ArgumentParser(description="Flag risky patterns in a draft Verdikta rubric (offline).")
    ap.add_argument("rubric", help="path to rubric JSON")
    ap.add_argument("--threshold", type=float, default=None, help="acceptance threshold (overrides rubric.threshold)")
    ap.add_argument("--jurors", type=int, default=2, help="number of equally weighted jurors (default 2)")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    ap.add_argument("--accept", action="append", default=[], metavar="RULE",
                    help="mark a reviewed risk as accepted (repeatable); it is still printed but no longer fails the exit code. "
                         "Same effect as listing it in rubric['preflightAccept'].")
    a = ap.parse_args()
    try:
        with open(a.rubric, encoding="utf-8") as f:
            rubric = json.load(f)
    except Exception as e:
        print(f"error: cannot read rubric: {e}", file=sys.stderr)
        sys.exit(2)
    res = check(rubric, a.threshold, a.jurors, a.accept)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"Task type: {res['task_type']} | threshold: {res['threshold']} | must-pass gates: {res['gates']}")
        if not res["findings"]:
            print("No risky patterns found.")
        for f_ in res["findings"]:
            lvl = f_["level"] + (f" (was {f_['accepted_from']})" if f_.get("accepted_from") else "")
            print(f"\n[{lvl}] {f_['rule']}: {f_['message']}\n    evidence: {f_['evidence']}")
    sys.exit(1 if any(f_["level"] == "HIGH" for f_ in res["findings"]) else 0)


if __name__ == "__main__":
    main()
