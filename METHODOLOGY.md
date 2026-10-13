# Methodology

## Unit of analysis

The source unit is one company annual report for one reporting year. Searchable text is extracted with Poppler's `pdftotext -layout`. The denominator counts tokens matching an alphabetic-leading word pattern, including internal apostrophes and hyphens.

The principal output is term incidence per 100,000 extracted words. Annual and sector results use corpus weighting: term occurrences are summed first and divided by the corresponding sum of extracted words. Company rankings use the same aggregate weighting across years.

## Lexical coding

The measure combines six non-overlapping, case-insensitive regular-expression families: regulation, compliance, burden, requirement, regulator, and legislation. Inflectional variants are defined explicitly in the extraction script rather than through stemming or lemmatization. `Regulator` and `regulators` are excluded from the regulation family and counted only in the regulator family.

This transparent approach does not resolve word sense. For example, a "capital requirement" and an environmental "reporting requirement" both contribute to the requirement family.

## Quality controls

The quality scripts test PDF signatures and trailers, Poppler readability, page counts, text-extraction volume, company identity, reporting-year evidence, financial-statement language, duplicate hashes, and Form 20-F indicators. Low extracted-word counts were reviewed because they can signal image-only, partial, or incorrect documents.

## Removed exploratory analyses

The histogram, thematic coding, and frame analysis were removed from the main dashboard. Their final results can be exported with `scripts/archive-removed-sections.py`; they are not part of the retained analytical claims.

### Experimental thematic coding

Retained passages can receive multiple dictionary-based themes covering governance, regulatory change, reporting, direct cost, systems, licensing, environmental obligations, financial rules, workforce obligations, and privacy or cyber matters. Because assignment is multi-label, theme totals are not mutually exclusive shares. The coding rules and outputs are work in progress and have not been verified by a person.

### Experimental framing

Retained passages receive one frame from an ordered dictionary: cost or challenge, transition or anticipation, opportunity or legitimacy, obligation or control, or descriptive or neutral. Because the rules are ordered, an earlier match takes priority. The framing code and archived outputs are work in progress. Neither has been verified by a person, and no manual inter-coder validation has been completed.

## Important limitations

- Annual reports are strategic disclosures, not neutral measurements of regulatory burden.
- Higher incidence may reflect more extensive reporting rather than greater underlying burden.
- OCR and PDF layout can split or merge words.
- The retained complete-coverage panel introduces survivorship and availability selection.
- Sector and company comparisons may reflect different disclosure obligations and report conventions.
