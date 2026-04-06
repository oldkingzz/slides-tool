---
name: slides
description: Manage Google Slides presentations with Penn Engineering template. List, add, preview, delete, modify slides, add tables, metrics, diagrams.
argument-hint: [list|preview|add|set|delete|move|table|metric|steps|mermaid]
disable-model-invocation: true
---

# Google Slides Manager

Manage Google Slides using the SlidesHelper API.

**Python:** `python3` (use system or conda python)
**Script:** `slides_api.py` (in repo root)
**Working dir:** repo root

## How to use

`cd` into the slides-tool repo first, then run Python commands with `python3 -c "..."`.

## Available Operations

### List slides
```python
from slides_api import SlidesHelper
s = SlidesHelper()
s.list_slides()
```

### Preview slides (saves PNG to /tmp/slide_preview/)
```python
s.preview([0, 1, 2])  # specific slides
s.preview(list(range(20)))  # all
```

### Add a slide
```python
s.add_slide("Title", "Body text", layout="content_blue")
# Layouts: title, divider, divider_gray, content_blue, content_red, content_gray,
#          two_column, navy, picture, red_sidebar, gray_sidebar, blank
```

### Modify a slide
```python
s.set_slide(index, "New Title", "New Body")
```

### Delete / Move
```python
s.delete_slide(index)
s.move_slide(from_index, to_index)
```

### Table slide
```python
s.table_slide("Title", ["Col1", "Col2"], [["r1c1", "r1c2"], ["r2c1", "r2c2"]], layout="blank")
```

### Metric cards
```python
s.metric_slide("Title", [{"value": "99%", "label": "accuracy"}, {"value": "4x", "label": "speedup"}], layout="blank")
```

### Steps slide
```python
s.steps_slide("Title", [{"text": "Step 1\nDetails"}, {"text": "Step 2\nMore"}], layout="blank")
```

### Mermaid diagram (renders via mermaid.ink, inserts as image)
```python
s.add_mermaid("slide_object_id", "graph LR; A-->B", x_pt, y_pt, w_pt, h_pt)
```

## Important
- Always preview after changes to verify
- Penn Engineering template with Penn colors (blue #011F5B, red #990000)
- config.json has the presentation_id
- Credentials at ~/credentials.json and ~/token.json (never commit these)
