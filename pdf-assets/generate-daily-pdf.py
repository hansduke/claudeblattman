#!/Users/michaelwredding/.claude-assistant/venv/bin/python3
"""
Generate a daily brief PDF from JSON data.

Usage:
    echo '{"date": "2026-05-16", ...}' | python generate-daily-pdf.py
    python generate-daily-pdf.py --input data.json --output daily.pdf
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from jinja2 import Template
    from weasyprint import HTML
except ImportError:
    print("Missing dependencies. Install with: pip install weasyprint jinja2", file=sys.stderr)
    sys.exit(1)


def get_week_days(target_date: datetime) -> list:
    """Generate week day data for the mini calendar."""
    monday = target_date - timedelta(days=target_date.weekday())
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        days.append({
            "day": d.day,
            "is_today": d.date() == target_date.date(),
            "is_weekend": i >= 5
        })
    return days


def get_week_number(target_date: datetime) -> int:
    """Get ISO week number."""
    return target_date.isocalendar()[1]


def render_pdf(data: dict, template_path: Path, output_path: Path) -> None:
    """Render the PDF from data and template."""
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    context = {
        "day_name": target_date.strftime("%A").upper(),
        "day": target_date.day,
        "month_name": target_date.strftime("%B").upper(),
        "week_number": get_week_number(target_date),
        "week_days": get_week_days(target_date),
        "date_formatted": date_str,
        # Content sections
        "calendar_events": data.get("calendar_events", []),
        "today_urgent": data.get("today_urgent", []),
        "today_quick": data.get("today_quick", []),
        "projects": data.get("projects", []),
        "due_items": data.get("due_items", []),
        "pending_items": data.get("pending_items", []),
    }

    template_content = template_path.read_text()
    template = Template(template_content)
    html_content = template.render(**context)

    HTML(string=html_content).write_pdf(output_path)
    print(f"Generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate daily brief PDF")
    parser.add_argument("--input", "-i", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", "-o", help="Output PDF path")
    parser.add_argument("--template", "-t", help="HTML template path")
    args = parser.parse_args()

    base_dir = Path.home() / ".claude-assistant"
    template_path = Path(args.template) if args.template else base_dir / "templates" / "daily-brief.html"

    if args.input:
        data = json.loads(Path(args.input).read_text())
    else:
        data = json.load(sys.stdin)

    if args.output:
        output_path = Path(args.output)
    else:
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        output_path = base_dir / "output" / f"daily-{date_str}.pdf"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(data, template_path, output_path)


if __name__ == "__main__":
    main()
