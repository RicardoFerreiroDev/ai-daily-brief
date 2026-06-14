#!/usr/bin/env python3
"""
Generador gratuito de AI Daily Brief.

No usa OpenAI API ni ningún servicio de pago. Lee feeds RSS públicos,
clasifica las entradas con reglas simples y genera:
- data/latest.json
- data/archive/YYYY-MM-DD.json
- data/archive/index.json

El contenido editorial de resumen está en español, pero los títulos de las
fuentes pueden conservarse en inglés cuando proceden de una fuente inglesa.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

SOURCES = [
    # Labs / compañías
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml", "kind": "news"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml", "kind": "news"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "kind": "news"},
    {"name": "Google DeepMind Blog", "url": "https://deepmind.google/discover/blog/rss.xml", "kind": "news"},
    {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/rss/", "kind": "news"},
    {"name": "Microsoft Research Blog", "url": "https://www.microsoft.com/en-us/research/feed/", "kind": "news"},

    # Medios tech
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "kind": "news"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "kind": "news"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "kind": "news"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "kind": "news"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "kind": "news"},

    # Papers
    {"name": "arXiv cs.AI", "url": "https://export.arxiv.org/rss/cs.AI", "kind": "paper"},
    {"name": "arXiv cs.CL", "url": "https://export.arxiv.org/rss/cs.CL", "kind": "paper"},
    {"name": "arXiv cs.LG", "url": "https://export.arxiv.org/rss/cs.LG", "kind": "paper"},
    {"name": "arXiv cs.CR", "url": "https://export.arxiv.org/rss/cs.CR", "kind": "paper"},
    {"name": "arXiv cs.SE", "url": "https://export.arxiv.org/rss/cs.SE", "kind": "paper"},
]

CATEGORY_RULES = [
    ("Modelos fundacionales", ["llm", "large language", "foundation model", "gpt", "claude", "gemini", "llama", "mistral", "model", "reasoning"]),
    ("Agentes y herramientas", ["agent", "agents", "tool use", "workflow", "automation", "coding agent", "github", "copilot"]),
    ("Investigación", ["paper", "benchmark", "dataset", "training", "inference", "alignment", "evaluation", "architecture"]),
    ("Seguridad y privacidad", ["safety", "security", "privacy", "jailbreak", "prompt injection", "misuse", "risk", "red team"]),
    ("Infraestructura", ["gpu", "chip", "nvidia", "data center", "datacenter", "compute", "inference", "server", "cloud"]),
    ("Regulación y sociedad", ["regulation", "law", "policy", "copyright", "job", "labor", "election", "governance", "eu ai act"]),
    ("Producto y mercado", ["launch", "startup", "funding", "revenue", "product", "app", "enterprise", "customer"]),
]

IMPORTANT_KEYWORDS = {
    "release": 4,
    "launch": 4,
    "new model": 5,
    "open source": 4,
    "benchmark": 3,
    "agent": 3,
    "safety": 3,
    "security": 4,
    "regulation": 3,
    "lawsuit": 3,
    "funding": 2,
    "nvidia": 3,
    "gpu": 3,
    "chip": 3,
    "paper": 2,
    "arxiv": 2,
    "reasoning": 3,
    "evaluation": 3,
    "dataset": 3,
    "openai": 3,
    "anthropic": 3,
    "deepmind": 3,
    "google": 2,
    "meta": 2,
    "microsoft": 2,
}


def clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(" ")
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def short_text(text: str, max_chars: int = 360) -> str:
    text = clean_html(text)
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "…"


def parse_date(entry: Any) -> str:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                return date_parser.parse(value).date().isoformat()
            except Exception:
                pass
    return dt.date.today().isoformat()


def classify(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "IA general"


def score_item(item: dict[str, Any]) -> int:
    text = f"{item['title']} {item['summary']} {item['source']}".lower()
    score = 0
    for keyword, weight in IMPORTANT_KEYWORDS.items():
        if keyword in text:
            score += weight
    if item["kind"] == "paper":
        score += 2
    # Prioriza entradas recientes.
    try:
        age_days = (dt.date.today() - dt.date.fromisoformat(item["published_date"])).days
        if age_days <= 1:
            score += 5
        elif age_days <= 3:
            score += 3
        elif age_days <= 7:
            score += 1
    except Exception:
        pass
    return score


def spanish_editorial_note(category: str, kind: str) -> str:
    if kind == "paper":
        notes = {
            "Agentes y herramientas": "Interesante para seguir la evolución de agentes capaces de actuar sobre herramientas reales y flujos de trabajo complejos.",
            "Seguridad y privacidad": "Relevante para entender riesgos prácticos, modelos de amenaza y límites de despliegue seguro en sistemas de IA.",
            "Modelos fundacionales": "Aporta señal sobre nuevas capacidades, evaluación o entrenamiento de modelos fundacionales.",
            "Investigación": "Lectura útil para profundizar en métodos, benchmarks o resultados que pueden influir en próximos sistemas de IA.",
        }
        return notes.get(category, "Artículo técnico útil para detectar tendencias de investigación y posibles líneas de trabajo futuras.")

    notes = {
        "Modelos fundacionales": "Importa porque los avances en modelos base suelen trasladarse rápidamente a productos, APIs y herramientas de desarrollo.",
        "Agentes y herramientas": "Importa porque los agentes están llevando la IA desde conversación pasiva hacia ejecución de tareas y automatización real.",
        "Investigación": "Importa porque puede anticipar cambios técnicos que todavía no han llegado a productos comerciales.",
        "Seguridad y privacidad": "Importa porque la adopción de IA depende de resolver riesgos de seguridad, privacidad y abuso.",
        "Infraestructura": "Importa porque el coste y disponibilidad de cómputo condicionan qué modelos pueden entrenarse y desplegarse.",
        "Regulación y sociedad": "Importa porque la regulación, empleo y confianza pública pueden acelerar o frenar la adopción de IA.",
        "Producto y mercado": "Importa porque muestra dónde se está convirtiendo la investigación en productos, ingresos y adopción empresarial.",
    }
    return notes.get(category, "Importa porque refleja una tendencia relevante en el ecosistema actual de inteligencia artificial.")


def stable_id(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()[:12]


def collect_items(max_items_per_feed: int = 15) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source in SOURCES:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:max_items_per_feed]:
            title = clean_html(entry.get("title", ""))
            url = entry.get("link", "")
            summary = short_text(entry.get("summary", entry.get("description", "")), 500)
            if not title or not url:
                continue
            item_id = stable_id(url, title)
            if item_id in seen:
                continue
            seen.add(item_id)

            item = {
                "id": item_id,
                "title": title,
                "url": url,
                "source": source["name"],
                "kind": source["kind"],
                "published_date": parse_date(entry),
                "summary_original": summary,
            }
            item["category"] = classify(title, summary)
            item["score"] = score_item({**item, "summary": summary})
            items.append(item)

    return items


def build_report(items: list[dict[str, Any]]) -> dict[str, Any]:
    today = dt.date.today().isoformat()

    news_candidates = [i for i in items if i["kind"] == "news"]
    paper_candidates = [i for i in items if i["kind"] == "paper"]

    news = sorted(news_candidates, key=lambda x: (x["score"], x["published_date"]), reverse=True)[:8]
    papers = sorted(paper_candidates, key=lambda x: (x["score"], x["published_date"]), reverse=True)[:6]

    report_news = []
    for item in news:
        report_news.append({
            "headline": item["title"],
            "summary": "Resumen automático gratuito basado en el extracto público de la fuente: " + (item["summary_original"] or "consulta la fuente original para más detalles."),
            "why_it_matters": spanish_editorial_note(item["category"], "news"),
            "source": item["source"],
            "url": item["url"],
            "category": item["category"],
            "published_date": item["published_date"],
        })

    report_papers = []
    for item in papers:
        report_papers.append({
            "title": item["title"],
            "summary": "Resumen automático gratuito basado en el abstract/extracto público: " + (item["summary_original"] or "consulta el paper original para más detalles."),
            "technical_relevance": spanish_editorial_note(item["category"], "paper"),
            "source": item["source"],
            "url": item["url"],
            "tags": [item["category"], "paper"],
            "published_date": item["published_date"],
        })

    return {
        "date": today,
        "title": f"AI Daily Brief — {today}",
        "language": "es",
        "mode": "free-rss-no-llm",
        "executive_summary": (
            "Report diario gratuito generado a partir de fuentes públicas en inglés sobre IA. "
            "No usa API de pago: clasifica noticias y papers con reglas simples, conserva enlaces originales "
            "y añade contexto editorial en español."
        ),
        "news": report_news,
        "papers": report_papers,
    }


def save_report(report: dict[str, Any]) -> None:
    data_dir = Path("data")
    archive_dir = data_dir / "archive"
    data_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)

    date = report["date"]
    latest_path = data_dir / "latest.json"
    archive_path = archive_dir / f"{date}.json"
    index_path = archive_dir / "index.json"

    latest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    archive_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    archive_files = sorted(
        [p for p in archive_dir.glob("*.json") if p.name != "index.json"],
        reverse=True,
    )
    archive_index = []
    for file in archive_files:
        try:
            r = json.loads(file.read_text(encoding="utf-8"))
            archive_index.append({
                "date": r.get("date", file.stem),
                "title": r.get("title", f"AI Daily Brief — {file.stem}"),
                "news_count": len(r.get("news", [])),
                "papers_count": len(r.get("papers", [])),
                "file": f"/ai-daily-brief/reports/{file.stem}/",
            })
        except Exception:
            continue

    index_path.write_text(json.dumps(archive_index, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    items = collect_items()
    report = build_report(items)
    save_report(report)
