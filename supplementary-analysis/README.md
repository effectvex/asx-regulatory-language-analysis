# Thematic coding and frame analysis

This folder contains an experimental supplement to the main regulatory-incidence analysis.

## Files

- [HTML report](thematic-frame-analysis.html) — readable summary tables for themes and frames, including annual results.
- [Excel workbook](thematic-frame-analysis.xlsx) — the same results in five worksheets with summary charts.

## Status

**Work in progress:** the thematic/framing code and outputs have not been verified by a person. No manual validation sample, inter-coder reliability study, or expert review has been completed. The results must not be presented as validated findings.

## Method

The rules are implemented in [`scripts/extract-regulatory-language.ps1`](../scripts/extract-regulatory-language.ps1).

- A retained passage can receive multiple themes, so theme totals overlap.
- Each retained passage receives one primary frame through an ordered dictionary; an earlier matching rule takes priority.
- Dictionary matching does not reliably resolve context, negation, speaker, or rhetorical intent.

Rebuild both files with:

```powershell
python ./scripts/export-thematic-frame-analysis.py
```
