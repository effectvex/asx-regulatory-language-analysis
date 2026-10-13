import csv
import json
import math
import re
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARDS = ROOT / "data" / "intermediate"
PROCESSED = ROOT / "data" / "processed" / "company-year-analysis.csv"
ANNUAL = ROOT / "data" / "graph-data" / "annual-incidence.csv"
EXTRACTOR = ROOT / "scripts" / "extract-regulatory-language.ps1"
REPORT_GENERATOR = ROOT / "scripts" / "generate-html-report.ps1"
EXPERIMENTAL_DOC = ROOT / "EXPERIMENTAL_ANALYSES.md"
TERM_KEYS = ("regulation", "compliance", "burden", "requirement", "regulator", "legislation")


def load_records():
    records = []
    for path in sorted(SHARDS.glob("balanced-regulatory-shard-*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8-sig")))
    return records


class DataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_records()

    def test_balanced_panel_shape(self):
        self.assertEqual(len(self.records), 1045)
        keys = {(row["Ticker"], int(row["Year"])) for row in self.records}
        self.assertEqual(len(keys), 1045)
        self.assertEqual(len({ticker for ticker, _ in keys}), 95)
        self.assertEqual({year for _, year in keys}, set(range(2015, 2026)))

    def test_non_overlapping_term_definitions(self):
        text = "regulation regulations regulatory regulator regulators"
        regulation = re.findall(r"\bregulat(?:ion|ions|ory)\b", text, re.I)
        regulator = re.findall(r"\bregulators?\b", text, re.I)
        self.assertEqual(len(regulation), 3)
        self.assertEqual(len(regulator), 2)
        self.assertTrue(set(regulation).isdisjoint(regulator))

    def test_report_generator_has_no_revenue_analysis(self):
        source = REPORT_GENERATOR.read_text(encoding="utf-8-sig").lower()
        self.assertNotIn("revenuemillions", source)
        self.assertNotIn("annual revenue", source)

    def test_main_report_composes_only_three_retained_sections(self):
        source = REPORT_GENERATOR.read_text(encoding="utf-8-sig")
        self.assertIn(
            "$html=$prefix+$yearSection+$sectorSection+$companySection+$footer",
            source,
        )
        self.assertNotIn("+$histogramSection+$themeSection+$frameSection+", source)

    def test_counts_are_nonnegative(self):
        for row in self.records:
            self.assertGreater(int(row["Words"]), 0)
            self.assertEqual(set(row["Terms"]), set(TERM_KEYS))
            self.assertTrue(all(int(value) >= 0 for value in row["Terms"].values()))

    def test_public_shards_contain_no_report_extracts(self):
        self.assertTrue(all(not row.get("Evidence") for row in self.records))

    def test_experimental_coding_is_structurally_consistent_and_clearly_unverified(self):
        for row in self.records:
            self.assertEqual(sum(int(value) for value in row["Frames"].values()), int(row["Coded"]))
            self.assertTrue(all(int(value) >= 0 for value in row["Themes"].values()))
        warning = EXPERIMENTAL_DOC.read_text(encoding="utf-8-sig").lower()
        self.assertIn("neither the code nor the outputs", warning)
        self.assertIn("verified by a person", warning)

    def test_processed_table_matches_shards(self):
        with PROCESSED.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1045)
        self.assertNotIn("AnnualRevenueMillions", rows[0])
        self.assertNotIn("RevenueCurrency", rows[0])
        self.assertNotIn("CodedPassages", rows[0])
        shard_by_key = {(row["Ticker"], int(row["Year"])): row for row in self.records}
        for row in rows:
            source = shard_by_key[(row["Ticker"], int(row["Year"]))]
            occurrences = sum(int(source["Terms"][key]) for key in TERM_KEYS)
            expected = 100000 * occurrences / int(source["Words"])
            self.assertTrue(math.isclose(float(row["SixTermIncidencePer100k"]), expected, rel_tol=1e-12))
            self.assertEqual(int(row["ExtractedWords"]), int(source["Words"]))

    def test_annual_aggregation_is_corpus_weighted(self):
        by_year = defaultdict(lambda: {"words": 0, "occurrences": 0})
        for row in self.records:
            year = int(row["Year"])
            by_year[year]["words"] += int(row["Words"])
            by_year[year]["occurrences"] += sum(int(row["Terms"][key]) for key in TERM_KEYS)
        with ANNUAL.open(newline="", encoding="utf-8-sig") as handle:
            annual = {int(row["Year"]): row for row in csv.DictReader(handle)}
        for year, totals in by_year.items():
            expected = 100000 * totals["occurrences"] / totals["words"]
            self.assertTrue(math.isclose(float(annual[year]["SixTermIncidencePer100k"]), expected, rel_tol=1e-12))


if __name__ == "__main__":
    unittest.main()

