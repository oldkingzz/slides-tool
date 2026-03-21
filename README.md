# slides-tool

A minimal CLI that edits Google Slides via the API — designed for AI assistants (like Claude Code) to use Google Slides as a living notebook.

No OAuth credentials or Google Cloud Console needed. It works through a small Apps Script deployed inside the presentation itself.

## How it works

```
You / AI assistant
    ↓  (uv run edit_slides.py add "Title" "Notes here")
Python CLI
    ↓  (HTTP POST with JSON)
Google Apps Script (deployed inside your Slides)
    ↓  (SlidesApp API)
Your Google Slides presentation
```

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/oldkingzz/slides-tool.git
cd slides-tool
bash setup.sh
```

### 2. Deploy the Apps Script

- Open your Google Slides presentation
- Go to **Extensions → Apps Script**
- Delete the default code, paste the contents of `appscript.js`
- Click **Deploy → New Deployment**
- Select **Web app**, set:
  - Execute as: **Me**
  - Who has access: **Anyone**
- Click **Deploy**, authorize when prompted
- Copy the web app URL

### 3. Configure

Create `config.json` in this folder:

```json
{
    "webapp_url": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
}
```

### 4. Use it

```bash
uv run edit_slides.py list                        # list all slides
uv run edit_slides.py add "Title" "Body text"     # append a slide
uv run edit_slides.py set 0 "Title" "Body text"   # replace slide 0
uv run edit_slides.py clear 2                     # clear slide 2
uv run edit_slides.py delete 3                    # delete slide 3
```

## Why?

I wanted a way for AI coding assistants to push notes directly into Google Slides during a working session — no copy-paste, no switching tabs. This is the simplest setup I could find: zero external dependencies, no API keys, works with school/work Google accounts that can't access Cloud Console.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (the setup script installs it if missing)
- A Google account that can edit the target Slides and use Apps Script
