# AI Daily Brief

Web estática para publicar un report diario de noticias y papers de IA en español a partir de fuentes en inglés.

## Qué hace

- Lee feeds RSS de fuentes de IA y arXiv.
- Genera un brief diario usando OpenAI API.
- Guarda el resultado en `data/latest.json` y en `data/archive/YYYY-MM-DD.json`.
- Publica una página web con Astro.
- Automatiza todo con GitHub Actions y GitHub Pages.

## Puesta en marcha

1. Crea un repositorio en GitHub, por ejemplo `ai-daily-brief`.
2. Sube estos archivos.
3. En GitHub, ve a `Settings > Secrets and variables > Actions`.
4. Crea un secreto llamado `OPENAI_API_KEY`.
5. Ve a `Settings > Pages`.
6. En `Build and deployment`, selecciona `GitHub Actions`.
7. Ve a `Actions > Generate AI Daily Brief` y pulsa `Run workflow`.

## Desarrollo local

```bash
npm install
npm run dev
```

Para generar el report localmente:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="tu_api_key"
python scripts/generate_report.py
```

## Personalización

Edita `SOURCES` en `scripts/generate_report.py` para añadir o quitar fuentes.

También puedes cambiar el modelo con:

```bash
export OPENAI_MODEL="gpt-4.1-mini"
```
