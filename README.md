# 2020 Vietnam National High School Graduation Examination — Exploratory Data Analysis

An exploratory data analysis (EDA) project intended to help a journalist investigate the **2020 National High School Graduation Examination (NHSGE)** in Vietnam and identify possible stories from examination results.

The goal is **descriptive exploration and communication**, not prediction or causal inference.

## Project questions

- What does the distribution of candidates' birth years look like?
- How do examination scores vary across age groups?
- Which surnames occur most often in the collected records?
- How do Mathematics and English score distributions compare?

These are starting points for journalistic investigation; a descriptive pattern alone should not be presented as an explanation or causal effect.

## Data

The project description identifies **diemthi.hcm.edu.vn** as the source of examination results. The repository includes a prepared dataset in [`clean_data.csv`](clean_data.csv).

The documented fields include examination registration number, date of birth, and subject scores. Scores are on a 0–10 scale; the project description indicates **-1** for subjects a candidate did not take or register for. Treat that value as a missing/not-taken indicator, **not** as an examination score when calculating descriptive statistics.

**Important data limitations:** The current repository does not document the exact number of attempted, successfully retrieved, excluded, and retained records, nor does it establish the complete geographic/population coverage of the extracted records. Findings should therefore be described as applying to the **collected dataset**, rather than to every Vietnamese examination candidate, until coverage is validated.

The prepared dataset may contain student-level information. Review identifiers and dates of birth for privacy and publication appropriateness before redistributing or reusing the data.

## Workflow

1. **Collect:** Retrieve examination results from the source website.
2. **Clean:** Handle invalid registration numbers, HTML-derived values, text encoding, and special cases in the source records.
3. **Prepare:** Organize candidate information and subject scores for analysis.
4. **Explore:** Use Python to summarize age and score distributions and surname frequencies.
5. **Visualize:** Produce figures that support potential news angles.

See the [Jupyter notebook](2020%20Vietnam%20National%20High%20School%20Graduation%20Examination%20Analysis.ipynb) for the analytical work and its outputs.

## Exploratory observations

The accompanying [portfolio project page](https://cuonghv.ca/NHSGE.html) describes four observations:

| Topic | Reported observation | Suggested journalistic follow-up |
| --- | --- | --- |
| Candidate ages | The oldest test-taker in the analysis was born in 1963. | Confirm record validity and explore the candidate's story with appropriate sourcing. |
| Age-group scores | Average scores were described as broadly similar for older candidates and grade-12 students. | Check group definitions, sample sizes, and score distributions before drawing a conclusion. |
| Surnames | Nguyễn appeared most frequently. | Report the frequency and clarify whether the pattern is surprising relative to a suitable benchmark. |
| Mathematics and English | Mathematics performance was described as higher than English. | Define the comparison (mean, median, score thresholds, or full distributions) and report numerical differences. |

These are **reported exploratory observations**, not independently validated results in this README. Confirm values and denominators directly from the analysis before quoting them in an article.

## Repository files

| File | Role |
| --- | --- |
| `2020 Vietnam National High School Graduation Examination Analysis.ipynb` | Jupyter notebook containing the analysis |
| `clean_data.csv` | Prepared examination dataset |
| `test.txt` | Supplementary file; its precise role should be documented after review |
| `unicode.txt` | Supplementary file; its precise role should be documented after review |

## How to explore

1. Open the notebook in **Jupyter Notebook** or **JupyterLab**.
2. Review the input-file paths and dependencies in the notebook before executing cells.
3. Use the included dataset only where the notebook expects that file; adjust local paths if needed.
4. Re-run the cleaning/analysis steps and check whether the published outputs are reproduced.

A verified dependency list, supported Python version, and end-to-end run instructions have **not yet been documented**. This README does not claim that a fresh environment can reproduce the notebook without adjustments.

## Data-quality audit

A reproducible, aggregate-only audit of the prepared CSV is provided in [`scripts/data_quality_audit.py`](scripts/data_quality_audit.py).

```bash
python scripts/data_quality_audit.py
```

This creates `reports/data_quality.md` and `reports/data_quality.json` locally with row count, missing values, automatically detected candidate-ID duplicates, and checks for score sentinel `-1`, non-numeric values, and invalid scores. **Review detected column names**, because detection is based on header patterns. No student-level data is included in the reports.

The [Data quality audit workflow](.github/workflows/data-quality-audit.yml) runs the same script on GitHub Actions; download the `data-quality-report` artifact from its workflow run to inspect verified totals. These aggregate reports are **not yet a reconciliation** to the original scraping attempts or the official candidate population; source logs and coverage documentation are still needed.

## Limitations and next steps

- Record the source coverage, collection date, and number of attempted/retrieved/removed/final observations.
- Verify duplicate registration numbers, missing score codes, and other exceptional values.
- Confirm that comparisons use comparable candidates and account for unequal group sizes.
- Add quantitative summaries for each chart and separate findings from story hypotheses.
- Document the notebook's software dependencies and the roles of the supplementary text files.
- Review student-level data for privacy and use limitations.

## Portfolio

[View the project on cuonghv.ca](https://cuonghv.ca/NHSGE.html)
