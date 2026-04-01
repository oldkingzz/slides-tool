# slides-tool

A CLI that creates and edits Google Slides using the Google Slides API directly — with Penn Engineering template for professional styling. Designed for AI assistants (like Claude Code) to generate polished presentations automatically.

## How it works

```
You / AI assistant
    ↓  (python edit_slides.py add "Title" "Body" --layout navy)
Python CLI + Google Slides API
    ↓  (OAuth2 authenticated API calls)
Google Slides presentation (Penn Engineering template)
```

## Quick start

### 1. Install dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib matplotlib
```

### 2. Set up Google Cloud OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project, enable **Google Slides API** and **Google Drive API**
3. Create OAuth 2.0 credentials (Desktop app)
4. Download the JSON and save as `~/credentials.json`
5. Add your Gmail as a test user in OAuth consent screen

### 3. First run (authorize)

```bash
python edit_slides.py new "My Presentation"
```

This will print a URL — open it in your browser, authorize, paste the code back.
Token saves to `~/token.json` and auto-refreshes after that.

### 4. Use it

```bash
python edit_slides.py list                              # list all slides
python edit_slides.py add "Title" "Body text"           # append (blue bar layout)
python edit_slides.py add "Title" "Body" --layout navy  # append with navy layout
python edit_slides.py set 2 "Title" "Body"              # update slide 2
python edit_slides.py delete 3                          # delete slide 3
python edit_slides.py img -1 "Title" "url" "Caption"    # append image slide
python edit_slides.py url                               # get presentation URL
```

## Available layouts

| Layout | Description |
|--------|-------------|
| `content_blue` | Blue bar header (default) |
| `content_red` | Red bar header |
| `content_gray` | Gray bar header |
| `navy` | Dark navy background |
| `title` | Presentation title |
| `divider` | Section divider with Penn logo |
| `two_column` | Side-by-side content |
| `blank` | Blank for custom images |

## Requirements

- Python 3.10+
- `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`
- A personal Gmail account with Google Cloud Console access
