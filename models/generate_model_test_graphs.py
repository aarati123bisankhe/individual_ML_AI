from __future__ import annotations

import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports" / "model_testing"
EVAL_DIR = BASE_DIR / "models" / "evaluation_summary"
RECO_METRICS = BASE_DIR / "models" / "recommendation_engine" / "evaluation_metrics.csv"
NAV_META = BASE_DIR / "models" / "navigation_product_locator" / "model_metadata.json"
INV_META = BASE_DIR / "models" / "inventory_demand_classifier" / "model_metadata.json"
SCAN_META = BASE_DIR / "models" / "scan_to_pay_risk_classifier" / "model_metadata.json"


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7faf8"/>',
    ]


def svg_footer(lines: list[str]) -> str:
    lines.append("</svg>")
    return "\n".join(lines)


def draw_text(lines: list[str], x: float, y: float, text: str, size: int = 12, weight: str = "normal", fill: str = "#1f2937", anchor: str = "start") -> None:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    lines.append(
        f'<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{safe}</text>'
    )


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def demand_bar_chart() -> None:
    rows = load_csv_rows(EVAL_DIR / "model_metrics_detailed.csv")
    wanted = [
        ("validation_rmse", "Validation RMSE"),
        ("test_rmse", "Test RMSE"),
        ("test_mae", "Test MAE"),
    ]
    selected = []
    for metric_key, label in wanted:
        for row in rows:
            if row["model_name"] == "Demand Forecasting" and row["metric"] == metric_key:
                selected.append(
                    {
                        "label": label,
                        "baseline": float(row["baseline"]),
                        "model": float(row["model_value"]),
                        "improvement_pct": float(row["improvement_pct"]) if row["improvement_pct"] else 0.0,
                    }
                )
                break

    width, height = 920, 560
    margin_left, margin_right, margin_top, margin_bottom = 90, 60, 80, 100
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    max_val = max(max(item["baseline"], item["model"]) for item in selected) * 1.15

    lines = svg_header(width, height)
    draw_text(lines, width / 2, 38, "Demand Forecasting Model Accuracy", 24, "bold", "#1d4d3a", "middle")
    draw_text(lines, width / 2, 62, "Baseline vs ridge regression on unseen retail demand data", 12, "normal", "#4b6357", "middle")

    # axes
    x0, y0 = margin_left, height - margin_bottom
    x1, y1 = width - margin_right, margin_top
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#6b7f74" stroke-width="1.5"/>')
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#6b7f74" stroke-width="1.5"/>')

    for tick in range(6):
        val = max_val * tick / 5
        y = y0 - chart_h * tick / 5
        lines.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#d7e2dc" stroke-width="1"/>')
        draw_text(lines, x0 - 10, y + 4, f"{val:.2f}", 10, "normal", "#5b6d62", "end")

    group_width = chart_w / len(selected)
    bar_width = 56
    colors = {"baseline": "#d08c60", "model": "#2a7f62"}

    for idx, item in enumerate(selected):
        group_center = x0 + group_width * idx + group_width / 2
        for offset, key in [(-bar_width / 1.6, "baseline"), (bar_width / 1.6, "model")]:
            value = item[key]
            h = chart_h * (value / max_val)
            x = group_center + offset - bar_width / 2
            y = y0 - h
            lines.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{h}" rx="4" fill="{colors[key]}"/>')
            draw_text(lines, x + bar_width / 2, y - 8, f"{value:.3f}", 11, "bold", colors[key], "middle")
        draw_text(lines, group_center, y0 + 28, item["label"], 12, "bold", "#24342c", "middle")
        draw_text(lines, group_center, y0 + 48, f"{item['improvement_pct']:.2f}% better", 11, "bold", "#2a7f62", "middle")

    # legend
    lines.append(f'<rect x="{width - 250}" y="88" width="16" height="16" fill="{colors["baseline"]}" rx="3"/>')
    draw_text(lines, width - 228, 101, "Naive baseline", 12, "normal", "#24342c")
    lines.append(f'<rect x="{width - 250}" y="114" width="16" height="16" fill="{colors["model"]}" rx="3"/>')
    draw_text(lines, width - 228, 127, "Ridge model", 12, "normal", "#24342c")

    draw_text(lines, 22, margin_top - 8, "Error", 12, "bold", "#24342c")
    draw_text(lines, width / 2, height - 26, "Lower bars are better. Green labels show percentage improvement over baseline.", 12, "normal", "#4b6357", "middle")

    (REPORT_DIR / "demand_forecasting_bar_graph.svg").write_text(svg_footer(lines), encoding="utf-8")


def recommendation_line_chart() -> None:
    rows = load_csv_rows(RECO_METRICS)
    hit_points = [(int(r["top_k"]), float(r["hit_rate"])) for r in rows]
    mrr_points = [(int(r["top_k"]), float(r["mrr"])) for r in rows]

    width, height = 920, 560
    margin_left, margin_right, margin_top, margin_bottom = 90, 60, 80, 100
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    max_val = max(max(v for _, v in hit_points), max(v for _, v in mrr_points)) * 1.2
    min_k = min(k for k, _ in hit_points)
    max_k = max(k for k, _ in hit_points)

    def point_xy(k: int, value: float) -> tuple[float, float]:
        if max_k == min_k:
            x = margin_left + chart_w / 2
        else:
            x = margin_left + chart_w * ((k - min_k) / (max_k - min_k))
        y = height - margin_bottom - chart_h * (value / max_val)
        return x, y

    lines = svg_header(width, height)
    draw_text(lines, width / 2, 38, "Recommendation Model Accuracy", 24, "bold", "#1d4d3a", "middle")
    draw_text(lines, width / 2, 62, "Top-k testing using hit rate and mean reciprocal rank", 12, "normal", "#4b6357", "middle")

    x0, y0 = margin_left, height - margin_bottom
    x1, y1 = width - margin_right, margin_top
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#6b7f74" stroke-width="1.5"/>')
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#6b7f74" stroke-width="1.5"/>')

    for tick in range(6):
        val = max_val * tick / 5
        y = y0 - chart_h * tick / 5
        lines.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#d7e2dc" stroke-width="1"/>')
        draw_text(lines, x0 - 10, y + 4, f"{val:.2f}", 10, "normal", "#5b6d62", "end")

    for k, _ in hit_points:
        x, _ = point_xy(k, 0)
        lines.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="#edf3ef" stroke-width="1"/>')
        draw_text(lines, x, y0 + 26, f"Top-{k}", 12, "bold", "#24342c", "middle")

    series = [
        ("Hit Rate", hit_points, "#2a7f62"),
        ("MRR", mrr_points, "#8b5fbf"),
    ]

    for label, points, color in series:
        path = []
        for idx, (k, value) in enumerate(points):
            x, y = point_xy(k, value)
            path.append(("M" if idx == 0 else "L", x, y))
        path_d = " ".join(f"{cmd} {x:.2f} {y:.2f}" for cmd, x, y in path)
        lines.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round"/>')
        for k, value in points:
            x, y = point_xy(k, value)
            lines.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>')
            draw_text(lines, x, y - 12, format_percent(value), 11, "bold", color, "middle")

    lines.append(f'<rect x="{width - 220}" y="88" width="16" height="16" fill="#2a7f62" rx="3"/>')
    draw_text(lines, width - 198, 101, "Hit Rate", 12, "normal", "#24342c")
    lines.append(f'<rect x="{width - 220}" y="114" width="16" height="16" fill="#8b5fbf" rx="3"/>')
    draw_text(lines, width - 198, 127, "MRR", 12, "normal", "#24342c")

    draw_text(lines, 22, margin_top - 8, "Score", 12, "bold", "#24342c")
    draw_text(lines, width / 2, height - 26, "Higher lines are better", 12, "normal", "#4b6357", "middle")

    (REPORT_DIR / "recommendation_accuracy_line_graph.svg").write_text(svg_footer(lines), encoding="utf-8")


def overall_accuracy_bar() -> None:
    rows = load_csv_rows(EVAL_DIR / "model_overview.csv")
    width, height = 980, 580
    margin_left, margin_right, margin_top, margin_bottom = 120, 50, 80, 80
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    max_val = max(float(r["metric_value"]) for r in rows) * 1.2

    lines = svg_header(width, height)
    draw_text(lines, width / 2, 38, "Overall Model Testing Snapshot", 24, "bold", "#1d4d3a", "middle")
    draw_text(lines, width / 2, 62, "Primary metric used for each current AI/ML model", 12, "normal", "#4b6357", "middle")

    x0, y0 = margin_left, height - margin_bottom
    x1, y1 = width - margin_right, margin_top
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#6b7f74" stroke-width="1.5"/>')
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#6b7f74" stroke-width="1.5"/>')

    for tick in range(6):
        val = max_val * tick / 5
        y = y0 - chart_h * tick / 5
        lines.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#d7e2dc" stroke-width="1"/>')
        draw_text(lines, x0 - 10, y + 4, f"{val:.2f}", 10, "normal", "#5b6d62", "end")

    bar_height = chart_h / len(rows) * 0.5
    palette = ["#2a7f62", "#d08c60", "#8b5fbf", "#2e6ea6"]

    for idx, row in enumerate(rows):
        y = margin_top + (idx + 0.5) * (chart_h / len(rows))
        value = float(row["metric_value"])
        w = chart_w * (value / max_val)
        lines.append(f'<rect x="{x0}" y="{y - bar_height/2}" width="{w}" height="{bar_height}" fill="{palette[idx % len(palette)]}" rx="5"/>')
        draw_text(lines, x0 - 15, y + 4, row["model_name"], 12, "bold", "#24342c", "end")
        display = format_percent(value) if value <= 1 else f"{value:.4f}"
        draw_text(lines, x0 + w + 10, y + 4, display, 12, "bold", palette[idx % len(palette)])

    draw_text(lines, width / 2, height - 24, "Percentage labels are shown where the metric is naturally bounded between 0 and 1.", 12, "normal", "#4b6357", "middle")
    (REPORT_DIR / "overall_model_accuracy_bar_graph.svg").write_text(svg_footer(lines), encoding="utf-8")


def project_accuracy_bar() -> None:
    nav = load_json(NAV_META)
    inv = load_json(INV_META)
    scan = load_json(SCAN_META)

    rows = [
        ("Product Navigation Accuracy", nav["top_1_navigation_accuracy"], "#2a7f62"),
        ("Inventory Demand Accuracy", inv["test_metrics"]["accuracy"], "#d08c60"),
        ("Scan-to-Pay Risk Accuracy", scan["test_metrics"]["accuracy"], "#2e6ea6"),
    ]

    width, height = 980, 580
    margin_left, margin_right, margin_top, margin_bottom = 170, 60, 80, 90
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    max_val = 1.05

    lines = svg_header(width, height)
    draw_text(lines, width / 2, 38, "Project AI Model Accuracy", 24, "bold", "#1d4d3a", "middle")
    draw_text(lines, width / 2, 62, "Accuracy percentages for the app-aligned AI models", 12, "normal", "#4b6357", "middle")

    x0, y0 = margin_left, height - margin_bottom
    x1, y1 = width - margin_right, margin_top
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#6b7f74" stroke-width="1.5"/>')
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#6b7f74" stroke-width="1.5"/>')

    for tick in range(6):
        val = max_val * tick / 5
        y = y0 - chart_h * tick / 5
        lines.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#d7e2dc" stroke-width="1"/>')
        draw_text(lines, x0 - 10, y + 4, format_percent(val), 10, "normal", "#5b6d62", "end")

    bar_height = chart_h / len(rows) * 0.52

    for idx, (label, value, color) in enumerate(rows):
        y = margin_top + (idx + 0.5) * (chart_h / len(rows))
        w = chart_w * (value / max_val)
        lines.append(f'<rect x="{x0}" y="{y - bar_height/2}" width="{w}" height="{bar_height}" fill="{color}" rx="6"/>')
        draw_text(lines, x0 - 18, y + 4, label, 12, "bold", "#24342c", "end")
        draw_text(lines, x0 + w - 12, y + 4, format_percent(value), 13, "bold", "#ffffff", "end")

    draw_text(lines, width / 2, height - 26, "All three percentages are shown directly inside the bars.", 12, "normal", "#4b6357", "middle")
    (REPORT_DIR / "project_ai_accuracy_bar_graph.svg").write_text(svg_footer(lines), encoding="utf-8")


def project_accuracy_line() -> None:
    nav = load_json(NAV_META)
    inv = load_json(INV_META)
    scan = load_json(SCAN_META)

    points = [
        ("Navigation", nav["top_1_navigation_accuracy"]),
        ("Inventory", inv["test_metrics"]["accuracy"]),
        ("Scan-to-Pay", scan["test_metrics"]["accuracy"]),
    ]

    width, height = 960, 560
    margin_left, margin_right, margin_top, margin_bottom = 90, 60, 80, 100
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    max_val = 1.05

    def point_xy(idx: int, value: float) -> tuple[float, float]:
        x = margin_left + chart_w * (idx / (len(points) - 1))
        y = height - margin_bottom - chart_h * (value / max_val)
        return x, y

    lines = svg_header(width, height)
    draw_text(lines, width / 2, 38, "Project AI Accuracy Trend", 24, "bold", "#1d4d3a", "middle")
    draw_text(lines, width / 2, 62, "Percentage accuracy shown for each app-focused model", 12, "normal", "#4b6357", "middle")

    x0, y0 = margin_left, height - margin_bottom
    x1, y1 = width - margin_right, margin_top
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#6b7f74" stroke-width="1.5"/>')
    lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#6b7f74" stroke-width="1.5"/>')

    for tick in range(6):
        val = max_val * tick / 5
        y = y0 - chart_h * tick / 5
        lines.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#d7e2dc" stroke-width="1"/>')
        draw_text(lines, x0 - 10, y + 4, format_percent(val), 10, "normal", "#5b6d62", "end")

    path_parts = []
    for idx, (_, value) in enumerate(points):
        x, y = point_xy(idx, value)
        path_parts.append(("M" if idx == 0 else "L", x, y))
    path_d = " ".join(f"{cmd} {x:.2f} {y:.2f}" for cmd, x, y in path_parts)
    lines.append(f'<path d="{path_d}" fill="none" stroke="#2a7f62" stroke-width="5" stroke-linecap="round"/>')

    for idx, (label, value) in enumerate(points):
        x, y = point_xy(idx, value)
        lines.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#2a7f62"/>')
        draw_text(lines, x, y - 14, format_percent(value), 12, "bold", "#2a7f62", "middle")
        draw_text(lines, x, y0 + 28, label, 12, "bold", "#24342c", "middle")

    draw_text(lines, width / 2, height - 26, "Higher points are better. Percentage accuracy is shown above each point.", 12, "normal", "#4b6357", "middle")
    (REPORT_DIR / "project_ai_accuracy_line_graph.svg").write_text(svg_footer(lines), encoding="utf-8")


def write_summary_markdown() -> None:
    text = """# Model Testing Graph Guide

This folder contains visual testing artifacts for the AI/ML models.

- `demand_forecasting_bar_graph.svg`
  Compares the naive baseline and ridge forecasting model on validation RMSE, test RMSE, and test MAE.

- `recommendation_accuracy_line_graph.svg`
  Shows recommendation quality across top-k using Hit Rate and MRR.

- `overall_model_accuracy_bar_graph.svg`
  Gives a compact snapshot of the main metric used for each current model.

- `project_ai_accuracy_bar_graph.svg`
  Shows the percentage accuracy of the three app-aligned AI models directly inside the bars.

- `project_ai_accuracy_line_graph.svg`
  Shows the same three app-aligned model percentages in a line graph.

These graphs are suitable for thesis results, presentations, and viva explanation.
"""
    (REPORT_DIR / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dir()
    demand_bar_chart()
    recommendation_line_chart()
    overall_accuracy_bar()
    project_accuracy_bar()
    project_accuracy_line()
    write_summary_markdown()
    print(f"Model testing graphs written to: {REPORT_DIR}")


if __name__ == "__main__":
    main()
