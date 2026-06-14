# AI Daily Brief — Gemini free tier

Web diaria sobre inteligencia artificial en español, desplegada con GitHub Pages y actualizada automáticamente con GitHub Actions.

Esta versión usa **Gemini API** para redactar el report en español a partir de fuentes públicas en inglés y papers de arXiv.

## Qué hace

- Lee fuentes RSS públicas en inglés sobre IA.
- Consulta papers recientes desde arXiv Atom API.
- Selecciona candidatos con reglas simples de relevancia.
- Usa Gemini para generar el report editorial en español.
- Guarda el último report en `data/latest.json`.
- Guarda histórico por fecha en `data/archive/YYYY-MM-DD.json`.
- Publica la web en GitHub Pages.

## Coste

La app no usa OpenAI ni servicios de pago obligatorios. Usa Gemini API con free tier. Aun así, debes vigilar los límites y cuotas de Google AI Studio, porque pueden variar por modelo, país, proyecto y uso.

## Secret necesario

Necesitas guardar tu clave de Gemini como secret de GitHub:

```txt
GEMINI_API_KEY
```

No la subas nunca al código.

## Dónde conseguir la clave

1. Entra en Google AI Studio.
2. Ve a **Get API key** o **API keys**.
3. Crea una API key.
4. Copia la clave.

## Dónde ponerla en GitHub

En tu repo:

1. **Settings**
2. **Secrets and variables**
3. **Actions**
4. **New repository secret**
5. Name:

```txt
GEMINI_API_KEY
```

6. Secret: pega tu clave de Gemini.
7. Pulsa **Add secret**.

## Cómo subirlo a tu repo

```bash
unzip ai-daily-brief-gemini.zip
cd ai-daily-brief-gemini

git init
git branch -M main
git remote add origin https://github.com/RicardoFerreiroDev/ai-daily-brief.git

git add .
git commit -m "Use Gemini for AI Daily Brief"
git push -u origin main --force
```

Si prefieres no usar `--force`, copia los archivos encima de tu repo actual y haz commit normal.

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

## Probar en local

Necesitas Node 22+ y Python 3.11+.

```bash
npm install
python -m pip install -r requirements.txt

export GEMINI_API_KEY="tu_clave"
python scripts/generate_report.py
npm run build
npm run dev
```

En Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="tu_clave"
python scripts/generate_report.py
npm run build
npm run dev
```

## Cambiar modelo

Por defecto usa:

```txt
gemini-2.5-flash-lite
```

Puedes cambiarlo en `.github/workflows/daily.yml` o definiendo:

```txt
GEMINI_MODEL
```

## Frecuencia diaria

El workflow está programado con:

```yaml
cron: "30 6 * * *"
```

Eso lo ejecuta cada día a las 06:30 UTC.
