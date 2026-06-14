#!/usr/bin/env python3
"""
Generador de AI Daily Brief con Gemini.

Lee feeds públicos de IA y papers de arXiv, selecciona candidatos con reglas
simples y usa Gemini para generar un report editorial en español.

Requiere la variable de entorno GEMINI_API_KEY.
Opcional: GEMINI_MODEL, por defecto gemini-2.5-flash-lite.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from google import genai
from google.genai import types

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
MAX_NEWS = 8
MAX_PAPERS = 6
MAX_INPUT_ITEMS = 80

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

    # Búsquedas agregadas gratuitas para cubrir fuentes sin RSS público estable, como Reuters.
    # No son URLs curadas manualmente: son feeds de búsqueda recurrentes.
    {"name": "Google News AI Reuters", "url": "https://news.google.com/rss/search?q=artificial%20intelligence%20Reuters%20when%3A7d&hl=en-US&gl=US&ceid=US:en", "kind": "news"},
    {"name": "Google News AI Research", "url": "https://news.google.com/rss/search?q=artificial%20intelligence%20research%20OR%20DeepMind%20OR%20OpenAI%20OR%20Anthropic%20when%3A7d&hl=en-US&gl=US&ceid=US:en", "kind": "news"},
]

ARXIV_QUERY_URL = (
    "https://export.arxiv.org/api/query?"
    "search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG+OR+cat:cs.CR+OR+cat:cs.SE"
    "&sortBy=submittedDate"
    "&sortOrder=descending"
    "&max_results=50"
)

CATEGORY_RULES = [
    ("Modelos fundacionales", ["llm", "large language", "foundation model", "gpt", "claude", "gemini", "llama", "mistral", "reasoning", "multimodal"]),
    ("Agentes y herramientas", ["agent", "agents", "tool use", "workflow", "automation", "coding agent", "github", "copilot", "browser"]),
    ("Investigación", ["paper", "benchmark", "dataset", "training", "inference", "alignment", "evaluation", "architecture", "post-training"]),
    ("Seguridad y privacidad", ["safety", "security", "privacy", "jailbreak", "prompt injection", "misuse", "risk", "red team", "vulnerability"]),
    ("Infraestructura", ["gpu", "chip", "nvidia", "data center", "datacenter", "compute", "server", "cloud", "tpu"]),
    ("Regulación y sociedad", ["regulation", "law", "policy", "copyright", "job", "labor", "election", "governance", "eu ai act"]),
    ("Producto y mercado", ["launch", "startup", "funding", "revenue", "product", "app", "enterprise", "customer", "ipo"]),
]

PRIORITY_SOURCES = {
    "OpenAI News": 12,
    "Anthropic News": 12,
    "Google AI Blog": 11,
    "Google DeepMind Blog": 12,
    "Meta AI Blog": 8,
    "Microsoft Research Blog": 8,
    "MIT Technology Review": 9,
    "Google News AI Reuters": 10,
    "Google News AI Research": 8,
    "arXiv": 8,
    "The Verge AI": 6,
    "TechCrunch AI": 5,
    "VentureBeat AI": 5,
    "Ars Technica": 6,
}

IMPORTANT_KEYWORDS = {
    # Modelos y arquitecturas
    "diffusiongemma": 30,
    "diffusion": 10,
    "autoregressive": 9,
    "mixture of experts": 9,
    "moe": 7,
    "open model": 8,
    "open-weight": 8,
    "open weights": 8,
    "new model": 8,
    "foundation model": 7,
    "multimodal": 7,
    "reasoning": 8,
    "inference": 7,
    "post-training": 6,

    # Agentes, evaluación y seguridad
    "agent": 8,
    "agents": 8,
    "workflow": 6,
    "tool use": 6,
    "coding agent": 9,
    "benchmark": 8,
    "evaluation": 7,
    "dataset": 6,
    "safety": 8,
    "alignment": 8,
    "security": 8,
    "prompt injection": 10,
    "jailbreak": 8,
    "red team": 7,
    "vulnerability": 7,

    # Infraestructura y mercado
    "nvidia": 8,
    "gpu": 7,
    "chip": 7,
    "data center": 7,
    "datacenter": 7,
    "compute": 6,
    "energy": 6,
    "ipo": 7,
    "funding": 4,
    "revenue": 4,

    # Sociedad, regulación y empleo
    "reuters/ipsos": 12,
    "ipsos": 9,
    "poll": 7,
    "survey": 7,
    "jobs": 7,
    "labor": 6,
    "worker": 5,
    "employment": 6,
    "regulation": 7,
    "policy": 6,
    "copyright": 6,
    "lawsuit": 5,

    # Fuentes/actores relevantes
    "openai": 6,
    "anthropic": 6,
    "deepmind": 7,
    "google": 4,
    "meta": 4,
    "microsoft": 4,
    "reuters": 8,
    "arxiv": 5,
}



def clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(" ")
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def short_text(text: str, max_chars: int = 900) -> str:
    text = clean_html(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def parse_date(entry: Any) -> str:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                return date_parser.parse(value).date().isoformat()
            except Exception:
                pass
    return dt.date.today().isoformat()


def stable_id(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()[:12]


def classify(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "IA general"


def score_item(item: dict[str, Any]) -> int:
    text = f"{item['title']} {item['summary_original']} {item['source']}".lower()
    score = PRIORITY_SOURCES.get(item.get("source", ""), 0)

    for keyword, weight in IMPORTANT_KEYWORDS.items():
        if keyword in text:
            score += weight

    # Mantener una sección de papers sólida sin eclipsar las noticias principales.
    if item["kind"] == "paper":
        score += 6

    # Bonus de actualidad.
    try:
        age_days = (dt.date.today() - dt.date.fromisoformat(item["published_date"])).days
        if age_days <= 1:
            score += 8
        elif age_days <= 3:
            score += 5
        elif age_days <= 7:
            score += 3
    except Exception:
        pass

    return score


def collect_news(max_items_per_feed: int = 12) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in SOURCES:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:max_items_per_feed]:
            title = clean_html(entry.get("title", ""))
            url = entry.get("link", "")
            summary = short_text(entry.get("summary", entry.get("description", "")), 900)
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
                "kind": "news",
                "published_date": parse_date(entry),
                "summary_original": summary,
            }
            item["category"] = classify(title, summary)
            item["score"] = score_item(item)
            items.append(item)
    return items


def collect_papers() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    feed = feedparser.parse(ARXIV_QUERY_URL)
    for entry in feed.entries:
        title = clean_html(entry.get("title", ""))
        url = entry.get("link", "")
        summary = short_text(entry.get("summary", ""), 1200)
        if not title or not url:
            continue
        authors = [a.get("name", "") for a in entry.get("authors", []) if a.get("name")]
        item = {
            "id": stable_id(url, title),
            "title": title,
            "url": url,
            "source": "arXiv",
            "kind": "paper",
            "published_date": parse_date(entry),
            "summary_original": summary,
            "authors": authors[:8],
        }
        item["category"] = classify(title, summary)
        item["score"] = score_item(item)
        items.append(item)
    return items


def collect_items() -> list[dict[str, Any]]:
    news = sorted(collect_news(max_items_per_feed=18), key=lambda x: (x["score"], x["published_date"]), reverse=True)[:50]
    papers = sorted(collect_papers(), key=lambda x: (x["score"], x["published_date"]), reverse=True)[:30]
    return news + papers


def report_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "date": {"type": "string"},
            "title": {"type": "string"},
            "language": {"type": "string"},
            "mode": {"type": "string"},
            "executive_summary": {"type": "string"},
            "news": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string"},
                        "summary": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "source": {"type": "string"},
                        "url": {"type": "string"},
                        "category": {"type": "string"},
                        "published_date": {"type": "string"},
                    },
                    "required": ["headline", "summary", "why_it_matters", "source", "url", "category", "published_date"],
                },
            },
            "papers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "technical_relevance": {"type": "string"},
                        "source": {"type": "string"},
                        "url": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "published_date": {"type": "string"},
                    },
                    "required": ["title", "summary", "technical_relevance", "source", "url", "tags", "published_date"],
                },
            },
        },
        "required": ["date", "title", "language", "mode", "executive_summary", "news", "papers"],
    }


def generate_with_gemini(items: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY. Añádela en GitHub: Settings → Secrets and variables → Actions → New repository secret."
        )

    today = dt.date.today().isoformat()
    compact_items = []
    for item in sorted(items, key=lambda x: (x["score"], x["published_date"]), reverse=True)[:MAX_INPUT_ITEMS]:
        compact_items.append({
            "kind": item["kind"],
            "title": item["title"],
            "source": item["source"],
            "url": item["url"],
            "published_date": item["published_date"],
            "category_hint": item["category"],
            "summary_or_abstract": item["summary_original"],
            "authors": item.get("authors", []),
            "score_hint": item["score"],
        })

    prompt = f"""
Eres un analista senior de inteligencia artificial. Escribes para un lector técnico con formación en Matemáticas, Informática y Ciencia de Datos.

Genera un AI Daily Brief en español para la fecha {today}.

Objetivo:
- Selecciona las noticias de IA más importantes a partir del input.
- Selecciona papers interesantes de arXiv; la sección de papers NO debe estar vacía si hay papers en el input.
- Prioriza fuentes primarias y de alta señal: OpenAI, Anthropic, Google AI, Google DeepMind, Meta AI, Microsoft Research, MIT Technology Review, Reuters vía Google News y arXiv.
- Da prioridad a avances técnicos de arquitectura/modelos, agentes, evaluación, seguridad, infraestructura, regulación y señales sociales/económicas importantes.
- Si aparece una noticia sobre modelos de difusión para texto, DiffusionGemma, MoE, generación no autoregresiva o encuestas Reuters/Ipsos sobre IA, trátala como candidata de alta relevancia.
- Redacta en español claro, técnico y conciso.
- No inventes URLs, fuentes, autores ni claims no contenidos en el input.
- Puedes conservar nombres propios y títulos de papers en inglés si es lo natural, pero los resúmenes deben estar en español.

Restricciones de salida:
- Devuelve JSON válido, sin markdown.
- Máximo {MAX_NEWS} noticias.
- Máximo {MAX_PAPERS} papers.
- Cada noticia debe tener: titular, resumen de 2-4 frases, por qué importa, fuente, URL, categoría y fecha.
- Cada paper debe tener: título, resumen de 2-4 frases, relevancia técnica, fuente, URL, tags y fecha.
- Campo mode debe ser "gemini-free-tier".

Input JSON:
{json.dumps(compact_items, ensure_ascii=False)}
"""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.25,
            response_mime_type="application/json",
            response_schema=report_schema(),
        ),
    )

    text = response.text or ""
    report = json.loads(text)
    report["date"] = today
    report["language"] = "es"
    report["mode"] = "gemini-free-tier"
    if not report.get("title"):
        report["title"] = f"AI Daily Brief — {today}"
    return report


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

    archive_files = sorted([p for p in archive_dir.glob("*.json") if p.name != "index.json"], reverse=True)
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
    start = time.time()
    items = collect_items()
    if not items:
        raise RuntimeError("No se han encontrado noticias ni papers en las fuentes configuradas.")
    report = generate_with_gemini(items)
    save_report(report)
    print(f"Generated report with {len(report.get('news', []))} news and {len(report.get('papers', []))} papers in {time.time() - start:.1f}s")
