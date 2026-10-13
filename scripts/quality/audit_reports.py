import csv
import hashlib
import json
import re
import statistics
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "annual-reports"
OUT = BASE / "output" / "audit"
OUT.mkdir(parents=True, exist_ok=True)
PDFINFO = "pdfinfo"
PDFTOTEXT = "pdftotext"

ALIASES = {
    "ALD": ["ampol", "caltex"], "ANZ": ["anz", "australia and new zealand banking"],
    "AIA": ["auckland international airport"], "BHP": ["bhp"], "CBA": ["commonwealth bank", "commbank"],
    "CNU": ["chorus"], "FBU": ["fletcher building"], "IGO": ["igo", "independence group"],
    "IPL": ["incitec pivot"], "MTS": ["metcash"], "NAB": ["national australia bank", "nab"],
    "NEM": ["newmont"], "NWS": ["news corp", "news corporation"], "RIO": ["rio tinto"],
    "SGM": ["sims", "sims metal"], "SPK": ["spark new zealand", "spark nz"],
    "TPM": ["tpg telecom", "vodafone hutchison"], "WBC": ["westpac"], "WDS": ["woodside"],
    "WOR": ["worley", "worleyparsons"], "XRO": ["xero"],
}

def company_aliases(folder: str):
    ticker, name = folder.split(" - ", 1)
    aliases = list(ALIASES.get(ticker, []))
    cleaned = re.sub(r"\b(limited|ltd|group|holdings|corporation|company|co|ord|units?|stapled|forus|b voting|nl)\b", " ", name.lower())
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned).strip()
    if cleaned:
        aliases.append(cleaned)
    if len(ticker) >= 3:
        aliases.append(ticker.lower())
    return ticker, name, sorted(set(a for a in aliases if len(a) >= 3), key=len, reverse=True)

def audit(pdf: Path):
    folder = pdf.parent.name
    ticker, company, aliases = company_aliases(folder)
    year = int(pdf.name[:4])
    raw = pdf.read_bytes()
    signature = raw[:5] == b"%PDF-"
    eof = b"%%EOF" in raw[-4096:]
    digest = hashlib.sha256(raw).hexdigest()
    info = subprocess.run([str(PDFINFO), str(pdf)], capture_output=True, text=True, errors="replace", timeout=90)
    pages = 0
    title = ""
    if info.returncode == 0:
        m = re.search(r"^Pages:\s+(\d+)", info.stdout, re.M)
        pages = int(m.group(1)) if m else 0
        m = re.search(r"^Title:\s*(.*)$", info.stdout, re.M)
        title = m.group(1).strip() if m else ""
    text_run = subprocess.run([str(PDFTOTEXT), "-layout", str(pdf), "-"], capture_output=True, timeout=180)
    text = text_run.stdout.decode("utf-8", "replace") if text_run.returncode == 0 else ""
    normalized = re.sub(r"\s+", " ", text.lower())
    full_words = len(re.findall(r"\b[\w'-]+\b", normalized))
    alias_hits = [a for a in aliases if a in normalized or a in title.lower()]
    year_hit = str(year) in normalized or str(year) in title
    annual_review = bool(re.search(r"\bannual review\b", normalized))
    independent_auditor = bool(re.search(r"\bindependent auditor(?:['’]s|s)? report\b", normalized))
    financial_statements = bool(re.search(r"\b(?:consolidated )?financial statements\b", normalized))
    # Treat this as an incompleteness signal only when the PDF does not itself
    # contain an independent auditor's report. Full reports often use the same
    # phrase when discussing parent-entity or subsidiary statements.
    explicit_separate_financials = (pages < 100 and not independent_auditor) and bool(re.search(
        r"does not (?:contain|include).{0,160}financial statements|"
        r"annual review is not a.{0,160}(?:concise|directors.? report|financial statements)|"
        r"financial statements (?:are|is) available separately", normalized))
    if pages < 80 and not independent_auditor and re.search(r"financial statements (?:are|is) available", normalized):
        explicit_separate_financials = True
    amendment_only = bool(re.search(r"form\s+20-f/a|amendment no\.\s*1", normalized[:30000]))
    return {
        "Ticker": ticker, "Company": company, "Year": year, "Path": str(pdf.relative_to(ROOT.parent)),
        "Bytes": len(raw), "Pages": pages, "ExtractedWords": full_words, "WordsPerPage": round(full_words / pages, 1) if pages else 0, "SHA256": digest,
        "PDFSignatureOK": signature, "EOFTrailerOK": eof, "PdfInfoOK": info.returncode == 0,
        "TextExtractOK": text_run.returncode == 0 and full_words > 50,
        "CompanyIdentityHit": bool(alias_hits), "MatchedAlias": alias_hits[0] if alias_hits else "",
        "YearHitDocument": year_hit, "MetadataTitle": title,
        "AnnualReviewLanguage": annual_review, "HasFinancialStatementsLanguage": financial_statements,
        "HasIndependentAuditorReport": independent_auditor,
        "ExplicitSeparateFinancialStatements": explicit_separate_financials, "AmendmentOnlySignal": amendment_only,
    }

pdfs = sorted(ROOT.glob("*/* - Annual Report.pdf"))
rows = []
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = {pool.submit(audit, p): p for p in pdfs}
    for i, future in enumerate(as_completed(futures), 1):
        try:
            rows.append(future.result())
        except Exception as exc:
            p = futures[future]
            ticker, company, _ = company_aliases(p.parent.name)
            rows.append({"Ticker": ticker, "Company": company, "Year": int(p.name[:4]), "Path": str(p.relative_to(ROOT.parent)), "Error": repr(exc)})
        if i % 100 == 0:
            print(f"audited {i}/{len(pdfs)}", flush=True)

rows.sort(key=lambda r: (r.get("Ticker", ""), r.get("Year", 0)))
hash_groups = {}
for r in rows:
    if r.get("SHA256"):
        hash_groups.setdefault(r["SHA256"], []).append(r["Path"])
duplicates = {h: ps for h, ps in hash_groups.items() if len(ps) > 1}

page_values = [r["Pages"] for r in rows if r.get("Pages", 0) > 0]
page_median = statistics.median(page_values)
page_sd = statistics.pstdev(page_values)
low_page_threshold = max(1, page_median - 2 * page_sd)
for r in rows:
    reasons = []
    if r.get("Error"): reasons.append("audit_error")
    if not r.get("PDFSignatureOK", False): reasons.append("bad_pdf_signature")
    if not r.get("EOFTrailerOK", False): reasons.append("missing_eof_trailer")
    if not r.get("PdfInfoOK", False): reasons.append("pdfinfo_failed")
    if not r.get("TextExtractOK", False): reasons.append("text_extraction_failed_or_sparse")
    if r.get("Pages", 0) and r["Pages"] < low_page_threshold: reasons.append("pages_below_median_minus_2sd")
    if r.get("Bytes", 0) < 100_000: reasons.append("file_under_100kb")
    if not r.get("CompanyIdentityHit", False): reasons.append("company_not_found_document")
    if not r.get("YearHitDocument", False): reasons.append("year_not_found_document")
    if r.get("ExtractedWords", 0) < 1000: reasons.append("fewer_than_1000_extracted_words")
    if r.get("Pages", 0) >= 50 and r.get("WordsPerPage", 0) < 20: reasons.append("very_low_text_density")
    if r.get("ExplicitSeparateFinancialStatements", False): reasons.append("financial_statements_separate")
    if r.get("AmendmentOnlySignal", False): reasons.append("amendment_only_signal")
    if r.get("AnnualReviewLanguage", False) and not r.get("HasIndependentAuditorReport", False) and not r.get("HasFinancialStatementsLanguage", False): reasons.append("annual_review_without_financials")
    if r.get("SHA256") in duplicates: reasons.append("exact_duplicate")
    r["Flags"] = ";".join(reasons)

fields = sorted(set().union(*(r.keys() for r in rows)))
with (OUT / "asx200-annual-report-audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(rows)
flagged = [r for r in rows if r.get("Flags")]
with (OUT / "asx200-annual-report-flagged.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(flagged)

coverage = {}
for folder in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    found = sorted(int(p.name[:4]) for p in folder.glob("* - Annual Report.pdf") if re.match(r"^20\d{2}", p.name))
    coverage[folder.name] = {"found": found, "missing": sorted(set(range(2015, 2026)) - set(found)), "extra": sorted(set(found) - set(range(2015, 2026)))}
summary = {
    "folders": len(coverage), "pdfs": len(pdfs), "expected_pdfs": len(coverage) * 11,
    "missing_reports": sum(len(v["missing"]) for v in coverage.values()),
    "duplicate_hash_groups": len(duplicates), "flagged_reports": len(flagged),
    "page_median": page_median, "page_sd": page_sd, "low_page_threshold": low_page_threshold,
    "flag_counts": {}, "coverage_issues": {k:v for k,v in coverage.items() if v["missing"] or v["extra"]},
    "duplicates": duplicates,
}
for r in flagged:
    for reason in r["Flags"].split(";"):
        summary["flag_counts"][reason] = summary["flag_counts"].get(reason, 0) + 1
(OUT / "asx200-annual-report-audit-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2), flush=True)
