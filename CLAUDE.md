# slides-tool — AI Instructions

This tool edits a Google Slides presentation via an Apps Script web app.
It is used as a **notebook** — not a polished presentation.

## Architecture

```
edit_slides.py  (CLI)  -->  slides_api.py  -->  POST JSON  -->  Apps Script web app  -->  Google Slides
```

- `appscript.js` — source of the Apps Script deployed inside the Google Slides
- `slides_api.py` — `SlidesHelper` class, sends HTTP POST to the web app
- `edit_slides.py` — CLI entry point
- `config.json` — contains `webapp_url` (**gitignored**, must be created manually on each device)

## Commands

Run from this directory:

```bash
uv run edit_slides.py list                        # list all slides with previews
uv run edit_slides.py add "Title" "Body"          # append a new slide
uv run edit_slides.py set <index> "Title" "Body"  # replace slide content
uv run edit_slides.py clear <index>               # clear a slide's content
uv run edit_slides.py delete <index>              # remove a slide entirely
```

## Rules for AI Assistants

1. **NEVER truncate content.** If text is long, split across multiple slides. Every word the user wants must appear.
2. Slides are plain-text notes, not fancy presentations. Keep it simple.
3. Each slide should be concise — but completeness beats brevity. Add more slides rather than cutting content.
4. Always `list` before editing to get current indices.
5. Always `list` after editing to confirm the change.
6. When setting a slide, pass both title and body. Use empty string "" to skip one.
7. The `config.json` contains the web app URL. Never modify it unless the user asks to switch presentations.

## Setup on a New Device

1. Clone the repo and cd into this folder
2. Run `bash setup.sh` (installs uv + dependencies)
3. Create `config.json` with your Apps Script web app URL:

```json
{
    "webapp_url": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
}
```

To get the URL (if you don't have it):
- Open the target Google Slides
- Extensions > Apps Script
- If the script is already there: Deploy > Manage deployments > copy the URL
- If not: paste `appscript.js` > Deploy > New Deployment > Web app > Execute as "Me" > Access "Anyone" > Deploy > copy URL

4. Test: `uv run edit_slides.py list`

## Switching to a Different Presentation

1. Open the new Google Slides
2. Extensions > Apps Script > paste `appscript.js` > Deploy as web app
3. Update `webapp_url` in `config.json`
