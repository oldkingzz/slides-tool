# slides-tool — AI Instructions

This tool edits Google Slides presentations using the Google Slides API directly,
with the Penn Engineering 2025 template for professional styling.

## Architecture

```
edit_slides.py (CLI) → slides_api.py → Google Slides API → Google Slides
                                      → Google Drive API  (copy template, manage files)
```

- `slides_api.py` — `SlidesHelper` class, uses Google Slides/Drive API with OAuth
- `edit_slides.py` — CLI entry point
- `config.json` — contains `presentation_id` (**gitignored**, auto-updated)
- `~/credentials.json` — OAuth client secret (from Google Cloud Console)
- `~/token.json` — auto-generated OAuth token (refreshes automatically)

## Available Layouts

Each slide uses a layout from the Penn Engineering template:

| Layout Key      | Description                          | Best For                    |
|-----------------|--------------------------------------|-----------------------------|
| `title`         | Title slide - single line            | Presentation title          |
| `title_double`  | Title slide - double line            | Long titles                 |
| `divider`       | White bg + Penn logo                 | Section dividers            |
| `divider_gray`  | Gray bg with picture area            | Section dividers with image |
| `content_blue`  | Blue bar header (DEFAULT)            | Main content slides         |
| `content_red`   | Red bar header                       | Highlighted content         |
| `content_gray`  | Gray bar header                      | Secondary content           |
| `two_column`    | Two content areas                    | Side-by-side comparison     |
| `navy`          | Dark navy background                 | Emphasis / key points       |
| `picture`       | Picture with caption                 | Image-focused slides        |
| `red_sidebar`   | Red sidebar + page number            | Detailed content            |
| `gray_sidebar`  | Gray sidebar                         | Detailed content            |
| `blank`         | Blank (no layout elements)           | Custom image slides         |

## Commands

### CLI

```bash
# Create a new presentation (copies Penn template, clears example slides)
python edit_slides.py new "My Presentation Title"

# List all slides
python edit_slides.py list

# Get presentation URL
python edit_slides.py url

# Add slide at end (default layout: content_blue)
python edit_slides.py add "Title" "Body text"
python edit_slides.py add "Title" "Body" --layout navy

# Insert slide at specific index
python edit_slides.py insert 3 "Title" "Body"

# Update existing slide content
python edit_slides.py set 3 "New Title" "New Body"
python edit_slides.py set 3 "Title" "Body" --layout content_red  # change layout too

# Delete / move slides
python edit_slides.py delete 3
python edit_slides.py move 3 1

# Image slide (index=-1 to append)
python edit_slides.py img 3 "Title" "https://..." "Caption"
python edit_slides.py img -1 "Title" "https://..." "Caption"
```

### Python API

```python
from slides_api import SlidesHelper
s = SlidesHelper()

# Create new presentation
s.new_presentation("Research Update 2026-04-01")

# Add slides with different layouts
s.add_slide("Overview", "Key findings...", layout="content_blue")
s.add_slide("Results", "Col A | Col B\n1 | 2", layout="two_column")
s.add_slide("Key Insight", "Important point", layout="navy")

# Image slides (matplotlib, plotly, or any URL)
s.img_slide(-1, "Architecture", "https://i.imgur.com/xxx.png", "System overview")

# Manage slides
s.list_slides()
s.set_slide(2, "Updated Title", "Updated body")
s.delete_slide(5)
s.move_slide(3, 1)

# Get URL to share
print(s.get_url())
```

## How to Create Slides

### For text content:
Use layout-based slides. The Penn template handles all styling automatically.

```python
s.add_slide("Section Title", "• Point 1\n• Point 2\n• Point 3", layout="content_blue")
```

### For diagrams/charts:
Use `matplotlib` or `plotly` to render high-quality images, upload to an accessible URL,
then use `img_slide()`.

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(["A", "B", "C"], [3, 7, 5])
fig.savefig("/tmp/chart.png", dpi=150, bbox_inches="tight")

# Upload to Drive or use a public URL, then:
s.img_slide(-1, "Results", image_url, "Bar chart of metrics")
```

### For section dividers:
```python
s.add_slide("Part 2: Experiments", "", layout="divider")
```

## Rules for AI Assistants

1. **Use appropriate layouts** — content_blue for most slides, navy for emphasis, divider for sections.
2. **NEVER truncate content.** Split across multiple slides if needed.
3. Keep text concise — bullet points, not paragraphs.
4. Always `list` before editing to get current indices.
5. Always `list` after editing to confirm the change.
6. For diagrams, prefer matplotlib/plotly over Mermaid — better quality and no external service dependency.
7. The `config.json` contains the presentation ID. It auto-updates when you create a new presentation.

## Setup on a New Device

1. Clone the repo and cd into this folder
2. Install dependencies:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib matplotlib
   ```
3. Place `~/credentials.json` (OAuth client secret from Google Cloud Console)
4. Run any command — first run will prompt for browser auth:
   ```bash
   python edit_slides.py list
   ```
5. Token saves to `~/token.json` and auto-refreshes

## Switching Presentations

```bash
# Create a new one (auto-switches)
python edit_slides.py new "New Presentation"

# Or manually edit config.json with an existing presentation ID
```

No Apps Script deployment needed. Any Google Slides file in your Drive works.
