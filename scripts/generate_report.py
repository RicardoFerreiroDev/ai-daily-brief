import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import feedparser
from openai import OpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MAX_ITEMS_PER_FEED = int(os.getenv("MAX_ITEMS_PER_FEED", "12"))

SOURCES = [
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://www.technologyreview.com/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.LG",
    "https://arxiv.org/rss/cs.CR",
]

REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "date": {"type": "string"},
        "title": {"type": "string"},
        "executive_summary": {"type": "string"},
        "news": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "headline": {"type": "string"},
                    "summary": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": [
                    "headline",
                    "summary",
                    "why_it_matters",
                    "source",
                    "url",
                    "category",
                ],
            },
        },
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "technical_relevance": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "summary",
                    "technical_relevance",
                    "source",
                    "url",
                    "tags",
                ],
            },
        },
    },
    "required": ["date", "title", "executive_summary", "news", "papers"],
}


def collect_items(max_items_per_feed: int = MAX_ITEMS_PER_FEED) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []

    for source_url in SOURCES:
        feed = feedparser.parse(source_url)
        feed_title = feed.feed.get("title", source_url)

        for entry in feed.entries[:max_items_per_feed]:
            items.append(
                {
                    "feed": feed_title,
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                }
            )

    return items


def generate_report(items: list[dict[str, str]]) -> dict[str, Any]:
    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    today = dt.date.today().isoformat()

    prompt = f"""
Eres un analista senior de IA escribiendo para un lector con formación en Matemáticas,
Informática y Ciencia de Datos.

Genera un AI Daily Brief en español para la fecha {today}.

Criterios:
- Prioriza noticias importantes, no contenido promocional.
- Selecciona máximo 6 noticias.
- Selecciona máximo 5 papers o artículos técnicos.
- Explica por qué importa cada elemento.
- Mantén tono claro, técnico y conciso.
- No inventes fuentes ni URLs.
- Usa solo elementos presentes en el input.
- Distingue noticias de papers/artículos técnicos.

INPUT:
{json.dumps(items, ensure_ascii=False)[:60000]}
""".strip()

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "ai_daily_brief",
                "schema": REPORT_SCHEMA,
                "strict": True,
            }
        },
    )

    return json.loads(response.output_text)


def save_report(report: dict[str, Any]) -> None:
    data_dir = Path("data")
    archive_dir = data_dir / "archive"
    data_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)

    date = report["date"]
    (data_dir / "latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (archive_dir / f"{date}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    source_items = collect_items()
    daily_report = generate_report(source_items)
    save_report(daily_report)
    print(f"Generated report for {daily_report['date']}")
