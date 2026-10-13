import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import torch
from transformers import pipeline

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "annual-reports"
BANK_DIRS = [
    "WBC - Westpac",
    "NAB - National Australia Bank",
    "ANZ - ANZ Group",
    "BOQ - Bank of Queensland",
    "CBA - Commonwealth Bank",
    "BEN - Bendigo and Adelaide Bank",
]
LOG = BASE / "output" / "banks-finbert-run.log"
OUT = BASE / "output" / "banks-2015-2025-finbert.json"
PDFTOTEXT = "pdftotext"
OUT.parent.mkdir(parents=True, exist_ok=True)
CUE = re.compile(r"\b(regulat\w*|complian\w*|burden|require\w*|regulator\w*|legislat\w*|licen[cs]\w*|permit\w*|approval\w*|obligat\w*|mandat\w*|prudential|privacy|cyber\w*|audit\w*|assurance)\b", re.I)

def extract(pdf: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        target = Path(tmp.name)
    try:
        subprocess.run([str(PDFTOTEXT), "-layout", str(pdf), str(target)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return re.sub(r"\s+", " ", target.read_text(encoding="utf-8", errors="replace")).strip()
    finally:
        target.unlink(missing_ok=True)

torch.set_num_threads(2)
classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert", tokenizer="ProsusAI/finbert", device=-1)

bank_results = []
if LOG.exists():
    prior = []
    for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        if '"company": "WBC - Westpac"' in line:
            try: prior.append(json.loads(line))
            except json.JSONDecodeError: pass
    if len(prior) == 11:
        cc = Counter(); words = passages = 0
        for row in prior:
            cc.update(row["counts"]); words += row["extracted_words"]; passages += row["candidate_passages"]
        bank_results.append({"company": "WBC - Westpac", "reports": 11, "extracted_words": words, "candidate_passages": passages, "counts": dict(cc), "shares": {k: round(v/passages,4) for k,v in cc.items()}, "net_sentiment": round((cc.get("positive",0)-cc.get("negative",0))/passages,4), "by_year": prior})

for dirname in BANK_DIRS[1:]:
    company_dir = ROOT / dirname
    files = sorted(company_dir.glob("*- Annual Report.pdf"), key=lambda p: int(p.name[:4]))
    company_counts = Counter(); company_words = company_passages = 0; by_year = []
    for pdf in files:
        year = int(pdf.name[:4]); text = extract(pdf)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 30]
        passages = [s for s in sentences if CUE.search(s)]
        predictions = classifier(passages, batch_size=16, truncation=True, max_length=512)
        counts = Counter(p["label"].lower() for p in predictions); total = len(predictions)
        words = len(re.findall(r"\b[\wâ€™'-]+\b", text))
        company_counts.update(counts); company_words += words; company_passages += total
        row = {"year": year, "extracted_words": words, "candidate_passages": total, "counts": dict(counts), "shares": {k: round(v/total,4) if total else 0 for k,v in counts.items()}, "net_sentiment": round((counts.get("positive",0)-counts.get("negative",0))/total,4) if total else 0}
        by_year.append(row); print(json.dumps({"company": dirname, **row}), flush=True)
    bank_results.append({"company": dirname, "reports": len(by_year), "extracted_words": company_words, "candidate_passages": company_passages, "counts": dict(company_counts), "shares": {k: round(v/company_passages,4) if company_passages else 0 for k,v in company_counts.items()}, "net_sentiment": round((company_counts.get("positive",0)-company_counts.get("negative",0))/company_passages,4) if company_passages else 0, "by_year": by_year})

all_counts = Counter(); all_words = all_passages = 0
for b in bank_results:
    all_counts.update(b["counts"]); all_words += b["extracted_words"]; all_passages += b["candidate_passages"]
result = {"subsector":"Banks", "period":"2015-2025", "model":"ProsusAI/finbert", "method":"Sentence-level classification of passages containing regulatory-language cues; passages truncated at 512 tokens.", "companies":len(bank_results), "reports":sum(b["reports"] for b in bank_results), "extracted_words":all_words, "candidate_passages":all_passages, "counts":dict(all_counts), "shares":{k:round(v/all_passages,4) for k,v in all_counts.items()}, "net_sentiment":round((all_counts.get("positive",0)-all_counts.get("negative",0))/all_passages,4), "by_company":bank_results}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: result[k] for k in ("companies","reports","extracted_words","candidate_passages","counts","shares","net_sentiment")}, indent=2), flush=True)
