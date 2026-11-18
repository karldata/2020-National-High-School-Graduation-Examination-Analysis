#!/usr/bin/env python3
"""Aggregate-only extended diagnostics for the NHSGE prepared CSV."""
import argparse
from collections import Counter
import csv
from datetime import date
import json
import math
from pathlib import Path
import statistics

DOB = ("Dob_dd","Dob_mm","Dob_yyyy")
GROUPS = {"Natural Sciences": ("Physics","Chemistry","Biology"),
          "Social Sciences": ("History","Geography","Civic Education")}
SUBJECTS = ("Maths","Literature","English","Physics","Chemistry","Biology",
            "History","Geography","Civic Education")
MISSING = {"","na","n/a","null","none","nan"}

def number(value):
    raw = str(value if value is not None else "").strip()
    if raw.lower() in MISSING:
        return None
    try:
        result = float(raw)
        return result if math.isfinite(result) else None
    except ValueError:
        return None

def valid_score(value):
    val = number(value)
    return val is not None and 0 <= val <= 10

def describe(values):
    if not values:
        return {"count":0}
    sorted_values = sorted(values)
    def pct(q):
        index = (len(sorted_values) - 1) * q
        low = int(index)
        high = min(low + 1, len(sorted_values)-1)
        return round(sorted_values[low] + (index-low)*(sorted_values[high]-sorted_values[low]),3)
    counts = Counter("10" if x == 10 else str(int(x)) for x in sorted_values)
    return {"count":len(values),"min":sorted_values[0],"max":sorted_values[-1],
            "mean":round(statistics.fmean(values),3),"median":pct(.5),
            "p10":pct(.1),"p90":pct(.9),"zero":counts.get("0",0),
            "perfect_10":counts.get("10",0),
            "histogram_0_to_9_plus_10":{str(i):counts.get(str(i),0) for i in range(11)}}

def audit(csv_path, manifest):
    dates = Counter()
    participation = {group: Counter() for group in GROUPS}
    aggregate_field_types = {group: Counter() for group in GROUPS}
    combinations = Counter()
    scores = {subject: [] for subject in SUBJECTS}
    rows = 0
    with csv_path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        needed=set(DOB)|set(SUBJECTS)|set(GROUPS)
        absent=sorted(needed-set(reader.fieldnames or []))
        if absent:
            raise ValueError("Missing expected CSV headers: "+", ".join(absent))
        for row in reader:
            rows += 1
            values=[number(row.get(key)) for key in DOB]
            if any(v is None for v in values):
                dates["missing_or_non_numeric"]+=1
            elif any(not v.is_integer() for v in values):
                dates["non_integer_date_component"]+=1
            else:
                try:
                    birth=date(*[int(values[i]) for i in (2,1,0)])
                except ValueError:
                    dates["invalid_calendar_date"]+=1
                else:
                    dates["valid_calendar_date"]+=1
                    if birth > date(2020,12,31):
                        dates["birth_after_exam_year"]+=1
                    else:
                        age=2020-birth.year-((12,31)<(birth.month,birth.day))
                        if age < 10: dates["age_under_10_review"]+=1
                        if age > 100: dates["age_over_100_review"]+=1
            for subject in SUBJECTS:
                if valid_score(row.get(subject)):
                    scores[subject].append(number(row[subject]))
            n_by_group={}
            for group, subjects in GROUPS.items():
                n=sum(valid_score(row.get(subject)) for subject in subjects)
                n_by_group[group]=n
                participation[group][str(n)+"_scores"]+=1
                raw=str(row.get(group) or "").strip()
                if raw.lower() in MISSING: kind="blank"
                elif number(raw)==-1: kind="minus_one"
                elif number(raw) is not None: kind="numeric_other"
                else: kind="text"
                aggregate_field_types[group][kind]+=1
            combinations[str(n_by_group["Natural Sciences"])+" natural / "+
                         str(n_by_group["Social Sciences"])+" social"]+=1
    coverage={"manifest_supplied":False,"confirmed":False,
              "attempted":None,"succeeded":None,"failed":None,"excluded":None,
              "reconciliation":"Not verifiable without source collection logs"}
    if manifest:
        m=json.loads(manifest.read_text(encoding="utf-8"))
        coverage["manifest_supplied"]=True
        for key in ("attempted","succeeded","failed","excluded"):
            v=m.get(key)
            if type(v) is int and v >= 0: coverage[key]=v
        a,s,f,e=(coverage[k] for k in ("attempted","succeeded","failed","excluded"))
        if all(x is not None for x in (a,s,f,e)):
            coverage["arithmetic_checks"]={"attempted_eq_succeeded_plus_failed":a==s+f,
                                          "succeeded_minus_excluded_eq_csv":s-e==rows}
            coverage["reconciliation"]=("Arithmetic agrees" if all(coverage["arithmetic_checks"].values())
                                        else "Arithmetic does not reconcile")
    return {"records":rows,"age_reference":"2020-12-31",
            "date_of_birth_checks":dict(dates),
            "subject_group_participation":{k:dict(v) for k,v in participation.items()},
            "subject_group_field_types":{k:dict(v) for k,v in aggregate_field_types.items()},
            "participation_matrix":dict(combinations),
            "score_distributions":{k:describe(v) for k,v in scores.items()},
            "source_completeness":coverage}

def markdown(a):
    lines=["# Extended data-quality diagnostics","",
           "Aggregate results only. No candidate-level data is output.",
           "Records: **{:,}**".format(a["records"]),"",
           "## Date-of-birth checks","",
           "Age reference: end of 2020. Under 10 and over 100 are review flags, not automatic errors.",""]
    for key,val in a["date_of_birth_checks"].items():
        lines.append("- {}: {:,}".format(key,val))
    lines+=["","## Subject group participation","",
            "Participation is defined as a valid subject score (0–10); -1 is excluded.",
            "Partial completion is a diagnostic only. Exam combination rules require independent validation.",""]
    for key,vals in a["subject_group_participation"].items():
        lines.append("- **{}**: {}".format(key,", ".join("{}={:,}".format(k,v) for k,v in vals.items())))
    lines+=["","The Natural Sciences / Social Sciences fields are NOT assumed to be scores or flags.",
            "Their observed data types and the 0–3 subject participation matrix are in JSON.","",
            "## Subject score distributions (excluding -1)","",
            "| Subject | Count | Mean | Median | P10 | P90 | Minimum | Maximum | Zeros | Tens |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name,d in a["score_distributions"].items():
        vals=([d.get(k,"–") for k in ("count","mean","median","p10","p90","min","max","zero","perfect_10")])
        lines.append("| {} | {} |".format(name," | ".join(map(str,vals))))
    lines+=["","The JSON file includes 0–9 score bands and a separate exact-score-10 bucket.","",
            "## Original source completeness","",
            "- Manifest supplied: {}".format(a["source_completeness"]["manifest_supplied"]),
            "- Reconciliation: {}".format(a["source_completeness"]["reconciliation"]),
            "- Geographic/national coverage cannot be proven from the prepared CSV.",
            "- Optional --manifest JSON keys: attempted, succeeded, failed, excluded.",
            "- A matching manifest only reconciles user-provided counts; it is not independent validation.","",
            "## Follow-up","",
            "- Inspect date/age flags against source records without publishing personal information.",
            "- Confirm science-group coding and allowed candidate combinations from exam rules.",
            "- Review unusual distributions by subject and denominators for subject comparisons.",
            "- Obtain original scraping attempt/error logs and authoritative coverage information.",""]
    return "\n".join(lines)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--csv",type=Path,default=Path("clean_data.csv"))
    parser.add_argument("--manifest",type=Path)
    parser.add_argument("--outdir",type=Path,default=Path("reports"))
    args=parser.parse_args()
    result=audit(args.csv,args.manifest)
    args.outdir.mkdir(parents=True,exist_ok=True)
    (args.outdir/"extended_quality.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (args.outdir/"extended_quality.md").write_text(markdown(result),encoding="utf-8")
    print("Extended audit complete: {:,} rows".format(result["records"]))

if __name__=="__main__":
    main()
