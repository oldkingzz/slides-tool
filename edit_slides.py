#!/usr/bin/env python3
"""CLI for editing Google Slides with Penn Engineering template.

Usage:
    python edit_slides.py new "Presentation Title"
    python edit_slides.py list
    python edit_slides.py url
    python edit_slides.py add "Title" "Body"
    python edit_slides.py add "Title" "Body" --layout content_red
    python edit_slides.py insert <index> "Title" "Body" [--layout ...]
    python edit_slides.py set <index> "Title" "Body" [--layout ...]
    python edit_slides.py delete <index>
    python edit_slides.py move <from> <to>
    python edit_slides.py img <index> "Title" "<image_url>" "Caption"
    python edit_slides.py img -1 "Title" "<image_url>" "Caption"   # append
    python edit_slides.py preview                                  # all slides
    python edit_slides.py preview 0 2 4                            # specific slides

Available layouts:
    title, title_double, divider, divider_gray,
    content_blue, content_red, content_gray,
    two_column, navy, picture, red_sidebar, gray_sidebar, blank
"""

import sys


def _unescape(s: str) -> str:
    """Convert literal \\n to real newlines in CLI args."""
    return s.replace("\\n", "\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    from slides_api import SlidesHelper

    cmd = sys.argv[1]

    # "new" doesn't need an existing presentation_id
    if cmd == "new":
        title = sys.argv[2] if len(sys.argv) > 2 else "Untitled"
        s = SlidesHelper.__new__(SlidesHelper)
        from slides_api import _get_credentials, _load_config, _save_config, TEMPLATE_ID
        from googleapiclient.discovery import build
        s._creds = _get_credentials()
        s._slides = build("slides", "v1", credentials=s._creds)
        s._drive = build("drive", "v3", credentials=s._creds)
        s._cfg = {"presentation_id": ""}
        s._pres_id = ""
        s.new_presentation(title)
        return

    s = SlidesHelper()

    # Parse --layout flag from anywhere in args
    layout = "content_blue"
    args = list(sys.argv[2:])
    if "--layout" in args:
        li = args.index("--layout")
        if li + 1 < len(args):
            layout = args[li + 1]
            args = args[:li] + args[li + 2:]

    if cmd == "list":
        s.list_slides()

    elif cmd == "url":
        print(s.get_url())

    elif cmd == "add":
        title = _unescape(args[0]) if len(args) > 0 else ""
        body = _unescape(args[1]) if len(args) > 1 else ""
        s.add_slide(title, body, layout)

    elif cmd == "insert":
        idx = int(args[0])
        title = _unescape(args[1]) if len(args) > 1 else ""
        body = _unescape(args[2]) if len(args) > 2 else ""
        s.insert_slide(idx, title, body, layout)

    elif cmd == "set":
        idx = int(args[0])
        title = _unescape(args[1]) if len(args) > 1 else ""
        body = _unescape(args[2]) if len(args) > 2 else ""
        s.set_slide(idx, title, body, layout if "--layout" in sys.argv else None)

    elif cmd == "delete":
        s.delete_slide(int(args[0]))

    elif cmd == "move":
        s.move_slide(int(args[0]), int(args[1]))

    elif cmd == "img":
        idx = int(args[0])
        title = _unescape(args[1]) if len(args) > 1 else ""
        image_url = args[2] if len(args) > 2 else ""
        caption = _unescape(args[3]) if len(args) > 3 else ""
        s.img_slide(idx, title, image_url, caption, layout)

    elif cmd == "metrics":
        # Usage: python edit_slides.py metrics "Title" "value1:label1" "value2:label2" ...
        title = _unescape(args[0]) if args else ""
        metrics = []
        for a in args[1:]:
            parts = a.split(":", 1)
            metrics.append({"value": parts[0], "label": parts[1] if len(parts) > 1 else ""})
        s.metric_slide(title, metrics, layout)

    elif cmd == "steps":
        # Usage: python edit_slides.py steps "Title" "Step 1 text" "Step 2 text" ...
        title = _unescape(args[0]) if args else ""
        steps = [{"text": _unescape(a)} for a in args[1:]]
        s.steps_slide(title, steps, layout)

    elif cmd == "table":
        # Usage: python edit_slides.py table "Title" "H1,H2,H3" "r1c1,r1c2,r1c3" ...
        title = _unescape(args[0]) if args else ""
        headers = args[1].split(",") if len(args) > 1 else []
        rows = [a.split(",") for a in args[2:]]
        s.table_slide(title, headers, rows, layout)

    elif cmd == "preview":
        indices = [int(a) for a in args] if args else None
        s.preview(indices)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
