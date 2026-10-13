# Coding validation

## Current status

The lexical counts are covered by automated integrity tests, including a regression test proving that `regulator` is not also counted as `regulation`. Passage coding has also undergone a qualitative implementation audit. That audit identified two defects that were corrected in this release:

1. PDF layout text could produce page-sized passages, allowing unrelated language on the same page to influence a theme or frame. Passage blocks are now sentence-split and capped at 800 characters.
2. The word `risk` alone forced a passage into the `Cost or challenge` frame. It has been removed from that rule; the frame now requires explicit cost, expense, fee, burden, challenge, difficulty, complexity, resource-pressure, or delay language.

These corrections improve face validity, but they are not a substitute for independent human validation. Theme and frame results remain descriptive dictionary outputs and should not be presented as validated measurements of actual regulatory burden.

## Recommended human-validation design

Use a stratified random sample of at least 200 retained passages:

- balance early (2015-2019) and late (2021-2025) reporting periods;
- include every sector and oversample smaller sectors;
- have two reviewers independently code passage relevance, all applicable themes, and one primary frame;
- hide company, year, and automatic labels during review;
- adjudicate disagreements only after the independent round.

Report precision and recall for passage retention and each theme, plus Cohen's kappa for the mutually exclusive frame. Pre-specify an acceptable threshold before treating the categories as validated; 0.70 kappa is a reasonable exploratory benchmark, not a universal standard.

## Interpretation until validation is complete

The year, sector, and company incidence results use exact lexical counts and do not depend on the theme or frame rules. The thematic and frame sections are exploratory summaries of the language surrounding regulatory cues. They should be used to generate hypotheses, not to support causal, legal, or cost estimates.
