#!/usr/bin/env python3
"""CLI for editing Google Slides as a notebook.

Usage:
    uv run edit_slides.py list
    uv run edit_slides.py add "Title" "Body text"
    uv run edit_slides.py set <index> "Title" "Body text"
    uv run edit_slides.py clear <index>
    uv run edit_slides.py delete <index>
"""

import sys
from slides_api import SlidesHelper


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    s = SlidesHelper()
    cmd = sys.argv[1]

    if cmd == "list":
        s.list_slides()
    elif cmd == "add":
        title = sys.argv[2] if len(sys.argv) > 2 else ""
        body = sys.argv[3] if len(sys.argv) > 3 else ""
        s.add_slide(title, body)
    elif cmd == "set":
        idx = int(sys.argv[2])
        title = sys.argv[3] if len(sys.argv) > 3 else ""
        body = sys.argv[4] if len(sys.argv) > 4 else ""
        s.set_slide(idx, title, body)
    elif cmd == "delete":
        s.delete_slide(int(sys.argv[2]))
    elif cmd == "clear":
        s.clear_slide(int(sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
