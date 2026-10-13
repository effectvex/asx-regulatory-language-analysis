import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

base = Path(__file__).resolve().parents[2]
root = base / "annual-reports"
pdftotext = "pdftotext"
pdfs = sorted(root.glob("*/* - Annual Report.pdf"))

def scan(pdf):
    run = subprocess.run([str(pdftotext), "-f", "1", "-l", "25", "-layout", str(pdf), "-"], capture_output=True, timeout=120)
    text = run.stdout.decode("utf-8", "replace")
    form20f_mention = bool(re.search(r"\bFORM\s+20-F\b", text, re.I))
    sec_cover = bool(re.search(r"SECURITIES\s+AND\s+EXCHANGE\s+COMMISSION", text, re.I))
    form20f = form20f_mention and sec_cover
    statutory_wrapper = bool(re.search(r"Irish\s+Statutory\s+Accounts|Statutory\s+Accounts", text, re.I))
    standalone_form20f = form20f and not statutory_wrapper
    amendment = bool(re.search(r"\bFORM\s+20-F/A\b|\b20-F/A\b|Amendment\s+No\.\s*1", text, re.I))
    ticker = pdf.parent.name.split(" - ", 1)[0]
    return {"Ticker": ticker, "CompanyFolder": pdf.parent.name, "Year": int(pdf.name[:4]),
            "ContainsForm20F": form20f, "StandaloneForm20F": standalone_form20f,
            "StatutoryAccountsWrapper": statutory_wrapper, "Amendment": amendment,
            "Path": str(pdf.relative_to(root.parent))}

with ThreadPoolExecutor(max_workers=6) as pool:
    rows = list(pool.map(scan, pdfs))
hits = [r for r in rows if r["ContainsForm20F"]]
out = base / "output" / "audit" / "form-20f-reports.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=hits[0].keys() if hits else ["Ticker", "CompanyFolder", "Year", "ContainsForm20F", "StandaloneForm20F", "StatutoryAccountsWrapper", "Amendment", "Path"])
    writer.writeheader(); writer.writerows(hits)
standalone = [r for r in hits if r["StandaloneForm20F"]]
wrapped = [r for r in hits if r["StatutoryAccountsWrapper"]]
print(f"standalone={len(standalone)} statutory_wrappers={len(wrapped)} embedded_total={len(hits)} amendments={sum(r['Amendment'] for r in hits)}")
for r in hits:
    kind = "standalone 20-F" if r["StandaloneForm20F"] else "statutory accounts containing 20-F appendix"
    print(f"{r['Ticker']} {r['Year']} {kind}")
