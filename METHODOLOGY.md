# Methodology and coding framework

## Unit of analysis

The source unit is one company annual report for one reporting year. Searchable text is extracted with Poppler's `pdftotext -layout`. The denominator counts tokens matching an alphabetic-leading word pattern, including internal apostrophes and hyphens.

The principal output is term incidence per 100,000 extracted words. Annual and sector results use corpus weighting: term occurrences are summed first and divided by the corresponding sum of extracted words. Company rankings use the same aggregate weighting across years.

## Lexical coding

The primary measure combines six case-insensitive regular-expression families: regulation, compliance, burden, requirement, regulator, and legislation. Inflectional variants are defined explicitly in the extraction script rather than through stemming or lemmatization.

This approach is transparent and reproducible, but it does not resolve word sense. For example, a “capital requirement” and an environmental “reporting requirement” both contribute to the requirement family.

## Passage selection

Text is split into sentence-like or paragraph-like passages. A passage is retained when it contains either a direct regulatory cue or a support-language combination connecting governance or reporting language with cost, legal, control, or obligation language. Very short fragments are discarded.

## Themes

Retained passages can receive multiple theme codes:

- Compliance and governance
- Regulatory change and uncertainty
- Reporting, disclosure and assurance
- Direct cost and resourcing
- Systems, data and process implementation
- Licensing, approvals and market access
- Environmental and climate obligations
- Financial, tax and prudential rules
- Safety, quality and workforce obligations
- Privacy, cyber and data protection

Because theme assignment is multi-label, theme totals should not be interpreted as mutually exclusive shares of all passages.

## Frames

Each retained passage receives one frame using an ordered rule set:

- Cost or challenge
- Transition or anticipation
- Opportunity or legitimacy
- Obligation or control
- Descriptive or neutral

The frame rules are deterministic dictionaries, not a supervised classifier. They provide a consistent descriptive categorization but cannot capture every contextual nuance.

## Quality controls

The quality scripts test PDF signatures and trailers, Poppler readability, page counts, text-extraction volume, company identity, reporting-year evidence, financial-statement language, duplicate hashes, and Form 20-F indicators. Low extracted-word counts were reviewed because they can signal image-only, partial, or incorrect documents.

## Important limitations

- Annual reports are strategic disclosures, not neutral measurements of regulatory burden.
- A higher incidence may reflect more extensive reporting rather than greater underlying burden.
- OCR and PDF layout can split or merge words and sentences.
- The retained complete-coverage panel introduces survivorship and availability selection.
- Sector and company comparisons may reflect different disclosure obligations and report conventions.
- Revenue values use each report's stated currency; cross-currency scatter plots are descriptive, not directly comparable measures of economic size.
- Dictionary coding should be validated against manually coded samples before causal or legal conclusions are drawn.

