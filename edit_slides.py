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

Available layouts:
    title, title_double, divider, divider_gray,
    content_blue, content_red, content_gray,
    two_column, navy, picture, red_sidebar, gray_sidebar, blank
"""

import sys


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
        title = args[0] if len(args) > 0 else ""
        body = args[1] if len(args) > 1 else ""
        s.add_slide(title, body, layout)

    elif cmd == "insert":
        idx = int(args[0])
        title = args[1] if len(args) > 1 else ""
        body = args[2] if len(args) > 2 else ""
        s.insert_slide(idx, title, body, layout)

    elif cmd == "set":
        idx = int(args[0])
        title = args[1] if len(args) > 1 else ""
        body = args[2] if len(args) > 2 else ""
        s.set_slide(idx, title, body, layout if "--layout" in sys.argv else None)

    elif cmd == "delete":
        s.delete_slide(int(args[0]))

    elif cmd == "move":
        s.move_slide(int(args[0]), int(args[1]))

    elif cmd == "img":
        idx = int(args[0])
        title = args[1] if len(args) > 1 else ""
        image_url = args[2] if len(args) > 2 else ""
        caption = args[3] if len(args) > 3 else ""
        s.img_slide(idx, title, image_url, caption, layout)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
