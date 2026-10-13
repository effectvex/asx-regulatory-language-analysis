# ASX regulatory-language analysis

Reproducible code and derived data for the 2015-2025 analysis of regulatory language in 1,045 annual reports from 95 companies in the retained ASX200 continuity panel.

The repository measures how frequently six regulatory-language families occur, normalized per 100,000 extracted words. It provides year, sector, and company comparisons and audits document quality.

## What is included

- `scripts/extract-regulatory-language.ps1` - PDF-to-text extraction, word counting, and six-term incidence.
- `scripts/build-company-year-data.ps1` - rebuilds the company-year incidence table from extraction shards.
- `scripts/generate-html-report.ps1` - self-contained interactive HTML report generator.
- `scripts/process-dashboard-data.ps1` - graph-ready annual, sector, and company datasets.
- `scripts/archive-removed-sections.py` - one-time preservation utility for the removed histogram, theme, and frame outputs.
- `archive/` - standalone HTML and Excel copies of those removed exploratory sections.
- `scripts/export-excel.ps1` and `scripts/add-incidence-chart.py` - spreadsheet exports.
- `scripts/quality/` - PDF integrity, identity, completeness, word-count, and Form 20-F checks.
- `data/processed/company-year-analysis.csv` - the 1,045-row company-year analytical dataset.
- `data/intermediate/` - eight reproducible extraction shards used by the report generator.
- `data/graph-data/` - graph-ready outputs used to cross-check the dashboard.
- `data/manifests/` - company-panel and sector metadata.

Annual-report PDFs are intentionally excluded. They remain subject to their publishers' rights and can be placed locally in `annual-reports/` using this structure:

```text
annual-reports/
  CBA - Commonwealth Bank/
    2015 - Annual Report.pdf
    ...
    2025 - Annual Report.pdf
```

## Six tracked term families

The primary incidence measure is the combined count of these non-overlapping families:

1. `regulation`, `regulations`, and `regulatory`
2. `compliance`, `compliances`, and `compliant`
3. `burden` and `burdens`
4. `requirement` and `requirements`
5. `regulator` and `regulators`
6. `legislation`, `legislations`, `legislative`, and `legislated`

The exact regular expressions are in `scripts/extract-regulatory-language.ps1`. In particular, `regulator` and `regulators` are excluded from the regulation family and counted only in the separate regulator family.

## Reproduce the analysis

Requirements:

- PowerShell 7 or Windows PowerShell 5.1
- [Poppler](https://poppler.freedesktop.org/) commands `pdftotext` and `pdfinfo` available on `PATH`
- Python 3.10+ for the spreadsheet utility
- Microsoft Excel on Windows only for the COM-based `export-excel.ps1`

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the complete extraction and report pipeline:

```powershell
./scripts/run-analysis.ps1
```

Or extract the eight shards individually:

```powershell
0..7 | ForEach-Object {
  ./scripts/extract-regulatory-language.ps1 -Shard $_ -Shards 8
}
```

Generate the interactive HTML report:

```powershell
./scripts/generate-html-report.ps1
```

Regenerate graph-ready datasets from the checked-in company-year table:

```powershell
./scripts/process-dashboard-data.ps1
```

The checked-in intermediate and processed data allow the aggregation logic to be inspected without redistributing the PDFs. To rebuild extraction results from source, users must obtain the annual reports separately.

## Interpretation

Incidence is calculated as:

```text
100,000 * tracked-term occurrences / extracted words
```

This measures disclosure-language frequency. It does not measure actual compliance expenditure, legal exposure, regulatory quality, or whether regulation is beneficial or burdensome. Differences can also reflect report length, reporting style, OCR quality, corporate structure, and sector-specific disclosure conventions.

See [METHODOLOGY.md](METHODOLOGY.md) for the coding framework and limitations. The exploratory histogram, theme, and frame sections are no longer part of the main report.

## Tests and continuous integration

Run the repository checks without the annual-report PDFs:

```powershell
python -m unittest discover -s tests -v
```

The tests verify the balanced-panel shape, non-overlapping lexical definitions, absence of report extracts and revenue fields, company-year incidence calculations, and corpus-weighted annual aggregation. GitHub Actions runs these checks and parses every PowerShell script on each push and pull request.

## Data provenance

The analytical panel contains 95 retained companies with complete 2015-2025 coverage, giving 1,045 company-year observations. Annual reports were obtained from company investor-relations sites and official filing sources, then subjected to structural and text-extraction checks. The repository does not claim that the retained panel reproduces the membership of a published ASX index at every historical date.

## Licences

- Code is released under the [MIT License](LICENSE).
- Derived numerical data in `data/` are released under [CC BY 4.0](DATA_LICENSE.md).
- Annual reports and other third-party source materials are not covered by these licences.
