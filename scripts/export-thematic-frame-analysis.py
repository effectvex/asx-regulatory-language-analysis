"""Export the experimental thematic-coding and frame-analysis supplement."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill


NOTICE = (
    "Work in progress. The thematic and framing code and outputs have not "
    "been verified by a person."
)


def load_records(directory: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(directory.glob("balanced-regulatory-shard-*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8-sig")))
    if not records:
        raise ValueError(f"No extraction shards found in {directory}")
    return records


def aggregate(records: list[dict]) -> dict:
    themes = list(records[0]["Themes"])
    frames = list(records[0]["Frames"])
    theme_totals: Counter = Counter()
    frame_totals: Counter = Counter()
    themes_by_year: dict[int, Counter] = defaultdict(Counter)
    frames_by_year: dict[int, Counter] = defaultdict(Counter)
    theme_companies = {theme: set() for theme in themes}

    for record in records:
        year = int(record["Year"])
        ticker = record["Ticker"]
        for theme in themes:
            count = int(record["Themes"][theme])
            theme_totals[theme] += count
            themes_by_year[year][theme] += count
            if count:
                theme_companies[theme].add(ticker)
        for frame in frames:
            count = int(record["Frames"][frame])
            frame_totals[frame] += count
            frames_by_year[year][frame] += count

    return {
        "themes": themes,
        "frames": frames,
        "theme_totals": theme_totals,
        "frame_totals": frame_totals,
        "themes_by_year": themes_by_year,
        "frames_by_year": frames_by_year,
        "theme_companies": theme_companies,
        "reports": len(records),
        "companies": len({record["Ticker"] for record in records}),
        "years": sorted({int(record["Year"]) for record in records}),
    }


def style_sheet(sheet) -> None:
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1769AA")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column in sheet.columns:
        values = [str(cell.value or "") for cell in column[:100]]
        width = min(48, max(10, max(map(len, values), default=10) + 2))
        sheet.column_dimensions[column[0].column_letter].width = width


def write_workbook(summary: dict, output: Path) -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)

    theme_sheet = workbook.create_sheet("Theme Totals")
    theme_sheet.append(["Theme", "Assignments", "Companies mentioning", "Share of assignments"])
    theme_denominator = sum(summary["theme_totals"].values())
    for theme, count in summary["theme_totals"].most_common():
        theme_sheet.append([
            theme,
            count,
            len(summary["theme_companies"][theme]),
            count / theme_denominator if theme_denominator else 0,
        ])
    style_sheet(theme_sheet)
    for cell in theme_sheet["D"][1:]:
        cell.number_format = "0.0%"

    theme_year = workbook.create_sheet("Themes by Year")
    theme_year.append(["Year", *summary["themes"]])
    for year in summary["years"]:
        theme_year.append([year, *(summary["themes_by_year"][year][theme] for theme in summary["themes"])])
    style_sheet(theme_year)

    frame_sheet = workbook.create_sheet("Frame Totals")
    frame_sheet.append(["Frame", "Passages", "Share of coded passages"])
    frame_denominator = sum(summary["frame_totals"].values())
    for frame, count in summary["frame_totals"].most_common():
        frame_sheet.append([frame, count, count / frame_denominator if frame_denominator else 0])
    style_sheet(frame_sheet)
    for cell in frame_sheet["C"][1:]:
        cell.number_format = "0.0%"

    frame_year = workbook.create_sheet("Frames by Year")
    frame_year.append(["Year", *summary["frames"]])
    for year in summary["years"]:
        frame_year.append([year, *(summary["frames_by_year"][year][frame] for frame in summary["frames"])])
    style_sheet(frame_year)

    notes = workbook.create_sheet("Read Me")
    notes.append(["Item", "Description"])
    notes.append(["Status", NOTICE])
    notes.append(["Themes", "Deterministic multi-label dictionary codes; one passage can receive multiple themes."])
    notes.append(["Frames", "One deterministic primary frame is assigned to each retained passage using ordered rules."])
    notes.append(["Validation", "No manual validation sample, inter-coder reliability study, or expert review has been completed."])
    notes.append(["Use", "Exploratory supplement only; these outputs are not part of the main incidence dashboard."])
    style_sheet(notes)

    for sheet, title in ((theme_sheet, "Theme assignments"), (frame_sheet, "Primary frame assignments")):
        chart = BarChart()
        chart.title = title
        chart.y_axis.title = "Passages"
        chart.add_data(Reference(sheet, min_col=2, min_row=1, max_row=sheet.max_row), titles_from_data=True)
        chart.set_categories(Reference(sheet, min_col=1, min_row=2, max_row=sheet.max_row))
        chart.height = 8
        chart.width = 18
        sheet.add_chart(chart, "F2")

    output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output)


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th scope='col'>{escape(value)}</th>" for value in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{value}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def write_html(summary: dict, output: Path) -> None:
    theme_denominator = sum(summary["theme_totals"].values())
    frame_denominator = sum(summary["frame_totals"].values())
    theme_rows = []
    for theme, count in summary["theme_totals"].most_common():
        share = 100 * count / theme_denominator if theme_denominator else 0
        theme_rows.append([
            f"<strong>{escape(theme)}</strong>", f"{count:,}",
            f"{len(summary['theme_companies'][theme]):,}", f"{share:.1f}%",
        ])
    frame_rows = []
    for frame, count in summary["frame_totals"].most_common():
        share = 100 * count / frame_denominator if frame_denominator else 0
        frame_rows.append([f"<strong>{escape(frame)}</strong>", f"{count:,}", f"{share:.1f}%"])

    theme_year_rows = [
        [str(year), *(f"{summary['themes_by_year'][year][theme]:,}" for theme in summary["themes"])]
        for year in summary["years"]
    ]
    frame_year_rows = [
        [str(year), *(f"{summary['frames_by_year'][year][frame]:,}" for frame in summary["frames"])]
        for year in summary["years"]
    ]

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thematic coding and frame analysis</title>
<style>
:root{{--ink:#17242d;--muted:#566772;--blue:#1769aa;--pale:#eef5f8;--line:#d5e0e6}}*{{box-sizing:border-box}}
body{{margin:0;background:#f5f8fa;color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:auto;padding:32px 20px 60px}}header,.panel{{background:white;border:1px solid var(--line);border-radius:12px;padding:24px;margin-bottom:20px}}
h1{{margin:0 0 8px;font-size:clamp(1.8rem,4vw,2.7rem)}}h2{{margin-top:0}}.notice{{border-left:5px solid #b45309;background:#fff7ed;padding:14px 16px;margin-top:20px}}
.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}}.meta span{{background:var(--pale);border-radius:999px;padding:5px 10px}}.muted{{color:var(--muted)}}
.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--pale)}}td:not(:first-child),th:not(:first-child){{text-align:right}}
footer{{margin-top:32px;color:var(--muted)}}
</style></head><body><main>
<header><h1>Thematic coding and frame analysis</h1><p class="muted">Exploratory analysis of a balanced panel of ASX annual reports, 2015–2025.</p>
<div class="meta"><span>{summary['companies']} companies</span><span>{summary['reports']:,} reports</span><span>2015–2025</span></div>
<div class="notice"><strong>Work in progress.</strong> The thematic/framing code and outputs have not been verified by a person. No manual coding validation or expert review has been completed.</div></header>
<section class="panel"><h2>1. Thematic coding</h2><p>Passages can receive more than one theme. Percentages therefore describe shares of all theme assignments, not mutually exclusive shares of passages.</p>
{table(['Theme','Assignments','Companies mentioning','Share'], theme_rows)}
<h3>Theme assignments by year</h3>{table(['Year', *summary['themes']], theme_year_rows)}</section>
<section class="panel"><h2>2. Frame analysis</h2><p>Each retained passage receives one primary frame from an ordered dictionary. An earlier matching rule takes priority when a passage contains cues for more than one frame.</p>
{table(['Frame','Passages','Share'], frame_rows)}
<h3>Primary frames by year</h3>{table(['Year', *summary['frames']], frame_year_rows)}</section>
<footer>Exploratory supplement. See the repository methodology for definitions and limitations.</footer>
</main></body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shards", type=Path, default=root / "data" / "intermediate")
    parser.add_argument("--output-directory", type=Path, default=root / "supplementary-analysis")
    args = parser.parse_args()

    summary = aggregate(load_records(args.shards))
    write_html(summary, args.output_directory / "thematic-frame-analysis.html")
    write_workbook(summary, args.output_directory / "thematic-frame-analysis.xlsx")
    print(f"written={args.output_directory.resolve()}")


if __name__ == "__main__":
    main()
