# ASX regulatory-language analysis

Code and derived data for a balanced-panel analysis of regulatory language in 1,045 annual reports from 95 companies, covering 2015–2025.

The principal measure is the combined incidence of six regulatory term families per 100,000 extracted words. Results are available by year, sector, and company.

## Start here

| Resource | Description |
| --- | --- |
| [Methodology](METHODOLOGY.md) | Definitions, aggregation method, quality controls, and limitations |
| [Company-year dataset](data/processed/company-year-analysis.csv) | 1,045 observations used by the dashboard |
| [Graph-ready data](data/graph-data/) | Annual, sector, and company summary tables |
| [Thematic and frame analysis](supplementary-analysis/) | Experimental HTML and Excel supplement |
| [Analysis scripts](scripts/) | Extraction, processing, reporting, and quality-control code |

## Scope

The analysis tracks these non-overlapping term families:

1. regulation
2. compliance
3. burden
4. requirement
5. regulator
6. legislation

Incidence is calculated as:

```text
100,000 × tracked-term occurrences ÷ extracted words
```

Annual and sector values are corpus-weighted: occurrences are summed before division by total extracted words.

## Repository structure

```text
data/
  processed/              company-year dataset
  graph-data/             annual, sector, and company summaries
  intermediate/           extraction shards
  manifests/              company and panel metadata
scripts/
  quality/                PDF and data-quality checks
supplementary-analysis/   thematic and frame outputs
tests/                    automated integrity checks
```

Annual-report PDFs are not included because they remain subject to their publishers’ rights. Place locally obtained reports in `annual-reports/` using this structure:

```text
annual-reports/
  CBA - Commonwealth Bank/
    2015 - Annual Report.pdf
    ...
    2025 - Annual Report.pdf
```

## Reproduce the analysis

Requirements:

- PowerShell 7 or Windows PowerShell 5.1
- Python 3.10+
- [Poppler](https://poppler.freedesktop.org/) commands `pdftotext` and `pdfinfo` on `PATH`
- Microsoft Excel on Windows for the COM-based Excel export

```powershell
python -m pip install -r requirements.txt
./scripts/run-analysis.ps1
```

Generate the thematic and frame supplement separately:

```powershell
python ./scripts/export-thematic-frame-analysis.py
```

## Interpretation

Incidence measures disclosure-language frequency, not compliance expenditure, legal exposure, regulatory quality, or causal regulatory burden. Results can also reflect report length, reporting conventions, OCR quality, corporate structure, and sector-specific vocabulary.

The thematic and frame supplement is clearly marked as work in progress. Its code and outputs have not been verified by a person and are not validated findings.

## Tests

```powershell
python -m unittest discover -s tests -v
```

GitHub Actions runs the integrity tests and parses every PowerShell script on each push and pull request.

## Licences

- Code: [MIT License](LICENSE)
- Derived numerical data: [CC BY 4.0](DATA_LICENSE.md)
- Annual reports and other third-party materials are not covered by these licences.
