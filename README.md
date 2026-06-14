# AI Daily Brief — versión gratuita

Web diaria gratuita sobre inteligencia artificial, desplegada con GitHub Pages y actualizada automáticamente con GitHub Actions.

## Qué hace

- Lee fuentes RSS públicas en inglés sobre IA.
- Selecciona noticias y papers recientes.
- Clasifica el contenido por categorías.
- Genera un report en español con contexto editorial básico.
- Guarda el último report en `data/latest.json`.
- Guarda histórico por fecha en `data/archive/YYYY-MM-DD.json`.
- Publica la web en GitHub Pages.

## Qué NO hace

Esta versión no llama a OpenAI, Anthropic ni ningún LLM de pago. Por eso:

- no necesitas `OPENAI_API_KEY`;
- no necesitas añadir secrets;
- no tiene coste de API;
- los títulos y extractos originales de fuentes inglesas pueden aparecer en inglés, aunque la estructura, categorías y contexto editorial están en español.

## Cómo subirlo a tu repo

```bash
unzip ai-daily-brief-free.zip
cd ai-daily-brief-free

git init
git branch -M main
git remote add origin https://github.com/RicardoFerreiroDev/ai-daily-brief.git

git add .
git commit -m "Initial free AI Daily Brief app"
git push -u origin main
```

Si el repo ya tiene commits:

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## Activar GitHub Pages

1. Ve a tu repo en GitHub.
2. Entra en **Settings → Pages**.
3. En **Build and deployment**, selecciona **GitHub Actions**.
4. Guarda.

## Ejecutar el primer report

1. Ve a **Actions**.
2. Abre **Generate free AI Daily Brief**.
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

## Personalizar categorías

Edita `CATEGORY_RULES` en `scripts/generate_report.py`.

## Limitaciones de la versión gratuita

Al no usar un LLM, el sistema no traduce ni resume con calidad humana. Hace una agregación editorial básica y gratuita. Si más adelante quieres resúmenes más elaborados en español, puedes crear una versión premium opcional con API key.
