#!/usr/bin/env python3
"""Aggregate-only audit of the prepared 2020 NHSGE CSV. Python standard library only."""
import argparse
import collections
import csv
import json
import re
from pathlib import Path

MISSING = {"", "nan", "none", "null", "na", "n/a"}
SCORE_TOKENS = ("toan", "math", "van", "literature", "ngu_van", "anh", "english",
                "ly", "physics", "hoa", "chem", "sinh", "biology", "su", "history",
                "dia", "geography", "gdcd", "civic", "foreign", "ngoai_ngu")
ID_TOKENS = ("sbd", "registration", "candidate_id", "so_bao_danh", "student_id")
DOB_TOKENS = ("birth", "ngay_sinh", "dob")
def normalized(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def audit(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        if not columns:
            raise ValueError("CSV has no header row")
        normalized_columns = {c: normalized(c) for c in columns}
        scores = [c for c in columns if any(t in normalized_columns[c] for t in SCORE_TOKENS)]
        ids = [c for c in columns if any(t in normalized_columns[c] for t in ID_TOKENS)]
        dates = [c for c in columns if any(t in normalized_columns[c] for t in DOB_TOKENS)]
        missing = collections.Counter()
        minus_one = collections.Counter()
        out_of_range = collections.Counter()
        nonnumeric = collections.Counter()
        id_counts = {c: collections.Counter() for c in ids}
        empty_rows = 0
        malformed_rows = 0
        total = 0
        for row in reader:
            total += 1
            if None in row or any(k not in row for k in columns):
                malformed_rows += 1
            if all(str(row.get(c) or "").strip().lower() in MISSING for c in columns):
                empty_rows += 1
            for col in columns:
                val = str(row.get(col) or "").strip()
                if val.lower() in MISSING:
                    missing[col] += 1
                if col in id_counts and val.lower() not in MISSING:
                    id_counts[col][val] += 1
                if col in scores and val.lower() not in MISSING:
                    try:
                        v = float(val)
                        if v == -1:
                            minus_one[col] += 1
                        elif not 0 <= v <= 10:
                            out_of_range[col] += 1
                    except ValueError:
                        nonnumeric[col] += 1
        dup = {
            col: {"distinct_nonmissing": len(counts),
                  "duplicate_identifier_values": sum(v > 1 for v in counts.values()),
                  "rows_beyond_first_for_duplicate_identifiers": sum(v - 1 for v in counts.values() if v > 1)}
            for col, counts in id_counts.items()
        }
        return {"file": path.name, "records": total, "columns": columns,
                "identifier_columns_detected": ids, "date_of_birth_columns_detected": dates,
                "score_columns_detected": scores, "entirely_empty_records": empty_rows,
                "malformed_records": malformed_rows,
                "missing_values_by_column": dict(missing),
                "score_minus_one_by_column": dict(minus_one),
                "score_outside_0_to_10_excluding_minus_one": dict(out_of_range),
                "score_non_numeric_by_column": dict(nonnumeric),
                "duplicate_identifier_summary": dup,
                "source_records_attempted": None, "source_records_failed": None,
                "source_records_excluded": None,
                "coverage_confirmed": False}

def render(a):
    lines = ["# NHSGE data-quality audit", "",
             "This report is generated from the repository's prepared CSV, not the original scraping logs.",
             "It contains aggregate statistics only; no student-level values are printed.", "",
             "## Summary", "",
             f"- CSV data records: **{a['records']:,}**",
             f"- Columns: **{len(a['columns'])}**",
             f"- Entirely empty records: **{a['entirely_empty_records']:,}**",
             f"- Malformed records: **{a['malformed_records']:,}**",
             f"- Candidate identifier columns detected: {', '.join(a['identifier_columns_detected']) or 'None (check headers manually)'}",
             f"- Score columns detected: {', '.join(a['score_columns_detected']) or 'None (check headers manually)'}", "",
             "## Column-level checks", "",
             "| Column | Missing / blank | Score -1 (not taken) | Invalid score (<0 or >10, excluding -1) | Non-numeric score |",
             "|---|---:|---:|---:|---:|"]
    for c in a["columns"]:
        safe = c.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {safe} | {a['missing_values_by_column'].get(c, 0):,} | {a['score_minus_one_by_column'].get(c, 0):,} | {a['score_outside_0_to_10_excluding_minus_one'].get(c, 0):,} | {a['score_non_numeric_by_column'].get(c, 0):,} |")
    lines += ["", "## Identifier duplication (candidate IDs only, if detected)", ""]
    if not a["duplicate_identifier_summary"]:
        lines.append("No candidate identifier column was confidently detected. **Duplicate candidate check requires manual column mapping.**")
    else:
        for c, x in a["duplicate_identifier_summary"].items():
            lines.append(f"- **{c}**: {x['distinct_nonmissing']:,} distinct nonblank IDs; {x['duplicate_identifier_values']:,} duplicated IDs; {x['rows_beyond_first_for_duplicate_identifiers']:,} rows beyond the first.")
    lines += ["", "## What this audit does NOT prove", "",
              "- It cannot determine how many source registrations were attempted, rejected, skipped, or lost in scraping.",
              "- It cannot establish national or geographic coverage, completeness against an official roster, or accuracy of source values.",
              "- It cannot determine whether repeated IDs are legitimate without checking record granularity.",
              "- Column identification uses header-name heuristics. Inspect detected column mappings before accepting checks.",
              "- Missing-score sentinel (-1) is reported separately; do not include it in mean score calculations.",
              "- A missing or non-numeric score is not automatically an error without source-specific definitions.",
              "", "## Follow-up required", "",
              "1. Confirm the candidate-ID, date-of-birth, and subject-score columns against the notebook.",
              "2. Reconcile source attempts, exceptions, skipped IDs, and final records using scraping logs.",
              "3. Compare the dataset's geographic and population scope against an authoritative source.",
              "4. Review whether student-level identifiers and birth dates should remain in the public dataset.",
              ""]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("clean_data.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/data_quality.md"))
    parser.add_argument("--json", type=Path, default=Path("reports/data_quality.json"))
    args = parser.parse_args()
    findings = audit(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(findings), encoding="utf-8")
    args.json.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Analyzed {findings['records']:,} records. Reports: {args.output}, {args.json}")

if __name__ == "__main__":
    main()
