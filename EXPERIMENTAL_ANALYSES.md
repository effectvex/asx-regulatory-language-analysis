# Experimental thematic coding and frame analysis: work in progress

> **Verification status:** Neither the code nor the outputs described here have been verified by a person. No manual validation sample, inter-coder reliability study, or expert review has been completed. These materials are published to make unfinished work inspectable and reproducible; they must not be presented as validated findings.

These experimental materials are deliberately separate from the main incidence dashboard and its processed tables.

## Rule-based thematic coding

The thematic rules are implemented in `scripts/extract-regulatory-language.ps1`. A retained passage can receive multiple themes, so the totals overlap and must not be read as mutually exclusive shares.

The dedicated HTML and Excel outputs are `archive/thematic-coding-and-frame-analysis-2015-2025.html` and `archive/thematic-coding-and-frame-analysis-2015-2025.xlsx`. The workbook contains overall and year-by-year theme tables; the HTML preserves the former thematic-coding section.

## Rule-based framing

The framing rules are implemented in `scripts/extract-regulatory-language.ps1`. Each retained passage is assigned one primary frame using an ordered dictionary. The order can affect the result when a passage matches more than one frame.

The same dedicated workbook contains frame totals and year-by-year frame tables; the HTML preserves the former framing section. The helper `scripts/archive-removed-sections.py` reproduces both thematic and framing outputs from the intermediate shards.

Important limitations:

- The categories and regular expressions have not been verified by a person.
- No passages have been manually double-coded to estimate agreement.
- Dictionary matches do not reliably resolve context, negation, speaker, or rhetorical intent.
- The output is exploratory and is not included in the main dashboard.
