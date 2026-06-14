# AI Daily Brief — Gemini Free Tier

Web diaria sobre inteligencia artificial, desplegada con GitHub Pages y actualizada automáticamente con GitHub Actions.

Esta versión usa **Gemini API** para redactar el report en español a partir de fuentes públicas. No usa OpenAI API.

## Qué hace

- Lee fuentes RSS públicas en inglés sobre IA.
- Lee papers recientes desde arXiv.
- Añade feeds de búsqueda gratuitos de Google News para cubrir fuentes que no tienen RSS estable, como Reuters.
- Aplica un ranking previo con prioridad para fuentes de alta señal.
- Envía los mejores candidatos a Gemini.
- Gemini selecciona y redacta el report en español.
- Guarda el último report en `data/latest.json`.
- Guarda histórico por fecha en `data/archive/YYYY-MM-DD.json`.
- Publica la web en GitHub Pages.

## Criterios de selección

El script da prioridad a:

- Fuentes primarias: OpenAI, Anthropic, Google AI, Google DeepMind, Meta AI, Microsoft Research.
- Fuentes de análisis/periodismo: MIT Technology Review, Reuters vía Google News, The Verge, Ars Technica.
- Papers de arXiv en `cs.AI`, `cs.CL`, `cs.LG`, `cs.CR` y `cs.SE`.
- Temas técnicos de alta señal: agentes, benchmarks, seguridad, modelos fundacionales, difusión para texto, MoE, inference, GPUs, regulación, empleo e impacto social.

Esta versión **no incluye URLs curadas manualmente**. Todo sale de fuentes recurrentes configuradas en el código.

## Secret necesario

Necesitas crear una API key gratuita de Gemini en Google AI Studio y guardarla como secret de GitHub.

En tu repo:

```txt
Settings → Secrets and variables → Actions → New repository secret
```

Nombre exacto:

```txt
GEMINI_API_KEY
```

Valor: pega tu API key de Gemini.

## Subirlo a tu repo

```bash
unzip ai-daily-brief-gemini-priority.zip
cd ai-daily-brief-gemini-priority

git init
git branch -M main
git remote add origin https://github.com/RicardoFerreiroDev/ai-daily-brief.git

git add .
git commit -m "Improve Gemini AI Daily Brief ranking"
git push -u origin main --force
```

## Activar GitHub Pages

1. Ve a tu repo en GitHub.
2. Entra en **Settings → Pages**.
3. En **Build and deployment**, selecciona **GitHub Actions**.
4. Guarda.

## Ejecutar el primer report

1. Ve a **Actions**.
2. Abre **Generate AI Daily Brief with Gemini**.
3. Pulsa **Run workflow**.

La web quedará publicada en:

```txt
https://ricardoferreirodev.github.io/ai-daily-brief/
```

## Frecuencia diaria

El workflow está programado con:

```yaml
cron: "30 6 * * *"
```

Eso lo ejecuta cada día a las 06:30 UTC.

## Personalizar fuentes

Edita `scripts/generate_report.py` y modifica la lista `SOURCES`.

## Personalizar ranking

Edita:

- `PRIORITY_SOURCES`
- `IMPORTANT_KEYWORDS`
- `CATEGORY_RULES`

## Coste

GitHub Pages y GitHub Actions en un repo público son gratuitos para este uso. Gemini API tiene free tier sujeto a cuotas. Si no configuras billing en Google, lo normal es que al superar cuota falle la llamada en vez de generar cobros.
