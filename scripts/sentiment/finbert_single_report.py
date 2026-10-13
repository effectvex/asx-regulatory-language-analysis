import argparse
import json
import re
from collections import Counter
from pathlib import Path

from transformers import pipeline


parser = argparse.ArgumentParser(
    description="Run FinBERT on regulatory-language passages in extracted annual-report text."
)
parser.add_argument("text", type=Path, help="UTF-8 text extracted from an annual report")
parser.add_argument("--output", type=Path, default=Path("finbert-result.json"))
parser.add_argument("--report", default="Annual report")
parser.add_argument("--source", default="")
args = parser.parse_args()

text = args.text.read_text(encoding="utf-8", errors="replace")
text = re.sub(r"\s+", " ", text).strip()
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 30]
cue = re.compile(
    r"\b(regulat\w*|complian\w*|burden|require\w*|regulator\w*|legislat\w*|"
    r"licen[cs]\w*|permit\w*|approval\w*|obligat\w*|mandat\w*|prudential|"
    r"privacy|cyber\w*|audit\w*|assurance)\b",
    re.I,
)
passages = [s for s in sentences if cue.search(s)]

classifier = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert",
    device=-1,
)
predictions = classifier(passages, batch_size=16, truncation=True, max_length=512)

counts = Counter(p["label"].lower() for p in predictions)
total = len(predictions)
shares = {k: round(v / total, 4) if total else 0 for k, v in counts.items()}
examples = {}
for label in ("positive", "neutral", "negative"):
    examples[label] = [
        {"score": round(predictions[i]["score"], 4), "text": passages[i][:500]}
        for i in range(len(passages))
        if predictions[i]["label"].lower() == label
    ][:5]

result = {
    "report": args.report,
    "source": args.source,
    "model": "ProsusAI/finbert",
    "method": "Sentence-level classification of passages containing regulatory-language cues; passages truncated at 512 tokens.",
    "extracted_words": len(re.findall(r"\b[\w’'-]+\b", text)),
    "candidate_passages": total,
    "counts": dict(counts),
    "shares": shares,
    "net_sentiment": round(
        (counts.get("positive", 0) - counts.get("negative", 0)) / total, 4
    ) if total else 0,
    "examples": examples,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: result[k] for k in (
    "report", "model", "extracted_words", "candidate_passages", "counts", "shares", "net_sentiment"
)}, indent=2))
