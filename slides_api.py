"""
Google Slides helper — uses Google Slides API + Drive API directly.

Requires:
  - ~/credentials.json (OAuth client secret from Google Cloud Console)
  - ~/token.json (auto-generated after first auth)
  - pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Template: Penn Engineering 2025 template (copied per presentation).
"""

import json
import os
import urllib.request
import uuid
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

_HERE = Path(__file__).resolve().parent
CONFIG_PATH = _HERE / "config.json"

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]

# Penn Engineering template
TEMPLATE_ID = "1q8U2scFpU60RIRI5F0wzM8aKmu0MjQ-XpXXCVXiKh18"

# Layout IDs from the Penn template
LAYOUTS = {
    "title": "p33",                    # Presentation Title Slide - single line
    "title_double": "p34",             # Presentation Title Slide - double line
    "divider": "p37",                  # Divider White bg + logo
    "divider_gray": "p38",            # Divider Gray bg w pic
    "content_blue": "g34a6adff730_0_50",  # Title and Content - Blue Bar 1
    "content_red": "g34a6adff730_0_26",   # Title and Content - Red Bar 1
    "content_gray": "p42",             # Title and Content - Gray Bar
    "two_column": "p62",               # 1_Two Content
    "navy": "p46",                     # Navy bg Title and Content
    "picture": "p48",                  # Picture with Caption
    "red_sidebar": "p47",             # Red Sidebar + page #
    "gray_sidebar": "p49",            # Gray Sidebar
    "blank": "p54",                    # Blank
}

# EMU constants (English Metric Units, 1 pt = 12700 EMU, 1 inch = 914400 EMU)
PT = 12700
EMU_INCH = 914400
SLIDE_W = 12192000  # 13.333 inches (16:9)
SLIDE_H = 6858000   # 7.5 inches
MARGIN = 50 * PT    # 50 pt margins

# Penn colors (RGB floats 0-1)
PENN_BLUE = {"red": 0.004, "green": 0.122, "blue": 0.357}   # #011F5B
PENN_RED = {"red": 0.6, "green": 0.0, "blue": 0.0}           # #990000
ACCENT_BLUE = {"red": 0.243, "green": 0.459, "blue": 0.894}  # #3E75E4
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
LIGHT_GRAY = {"red": 0.961, "green": 0.965, "blue": 0.973}   # #F5F6F8
MID_GRAY = {"red": 0.467, "green": 0.467, "blue": 0.467}     # #777777
DARK_TEXT = {"red": 0.118, "green": 0.118, "blue": 0.157}     # #1E1E28

# Credentials paths
CREDENTIALS_PATH = Path.home() / "credentials.json"
TOKEN_PATH = Path.home() / "token.json"


def _uid():
    """Generate a unique object ID for Slides API."""
    return f"obj_{uuid.uuid4().hex[:12]}"


def _get_credentials():
    """Load or refresh OAuth credentials."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    elif not creds or not creds.valid:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Missing {CREDENTIALS_PATH}. Download OAuth client JSON from "
                "Google Cloud Console and save it as ~/credentials.json"
            )
        flow = Flow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            scopes=SCOPES,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob",
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        print(f"\nOpen this URL in your browser:\n{auth_url}\n")
        code = input("Paste the authorization code: ")
        flow.fetch_token(code=code)
        creds = flow.credentials
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def _load_config():
    """Load config.json with presentation_id."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Create it with:\n"
            '  {"presentation_id": "YOUR_PRESENTATION_ID"}'
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)


def _save_config(cfg):
    """Write config back."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


class SlidesHelper:
    def __init__(self):
        self._creds = _get_credentials()
        self._slides = build("slides", "v1", credentials=self._creds)
        self._drive = build("drive", "v3", credentials=self._creds)
        self._cfg = _load_config()
        self._pres_id = self._cfg["presentation_id"]

    # ------------------------------------------------------------------
    # Presentation management
    # ------------------------------------------------------------------

    def new_presentation(self, title: str) -> str:
        """Create a new presentation by copying the Penn template."""
        copied = self._drive.files().copy(
            fileId=TEMPLATE_ID,
            body={"name": title},
        ).execute()
        pres_id = copied["id"]

        # Remove all template example slides (keep only masters/layouts)
        pres = self._slides.presentations().get(
            presentationId=pres_id
        ).execute()
        slide_ids = [s["objectId"] for s in pres.get("slides", [])]

        if slide_ids:
            requests = [
                {"deleteObject": {"objectId": sid}}
                for sid in slide_ids
            ]
            self._slides.presentations().batchUpdate(
                presentationId=pres_id,
                body={"requests": requests},
            ).execute()

        # Save as current presentation
        self._cfg["presentation_id"] = pres_id
        _save_config(self._cfg)
        self._pres_id = pres_id

        url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
        print(f"Created presentation: {title}")
        print(f"  URL: {url}")
        print(f"  ID: {pres_id}")
        return pres_id

    def get_url(self) -> str:
        """Return the URL of the current presentation."""
        return f"https://docs.google.com/presentation/d/{self._pres_id}/edit"

    # ------------------------------------------------------------------
    # Slide operations
    # ------------------------------------------------------------------

    def list_slides(self):
        """List all slides with index and text preview."""
        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()
        slides = pres.get("slides", [])
        print(f"Total slides: {len(slides)}")
        print(f"URL: {self.get_url()}")
        print("-" * 60)

        result = []
        for i, slide in enumerate(slides):
            text = self._extract_text(slide)
            preview = text[:120] if text else "(empty)"
            print(f"  [{i}] {preview}")
            result.append({"index": i, "preview": preview, "id": slide["objectId"]})
        return result

    def add_slide(self, title: str = "", body: str = "",
                  layout: str = "content_blue") -> dict:
        """Add a new slide at the end using a template layout."""
        layout_id = LAYOUTS.get(layout, LAYOUTS["content_blue"])
        slide_id = _uid()

        requests = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"layoutId": layout_id},
                }
            }
        ]

        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": requests},
        ).execute()

        # Now fill in the placeholders
        self._fill_placeholders(slide_id, title, body, layout)

        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()
        idx = len(pres.get("slides", [])) - 1
        print(f"Added slide [{idx}] (layout: {layout})")
        return {"index": idx, "id": slide_id}

    def insert_slide(self, index: int, title: str = "", body: str = "",
                     layout: str = "content_blue") -> dict:
        """Insert a new slide at a specific index."""
        layout_id = LAYOUTS.get(layout, LAYOUTS["content_blue"])
        slide_id = _uid()

        requests = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": index,
                    "slideLayoutReference": {"layoutId": layout_id},
                }
            }
        ]

        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": requests},
        ).execute()

        self._fill_placeholders(slide_id, title, body, layout)
        print(f"Inserted slide [{index}] (layout: {layout})")
        return {"index": index, "id": slide_id}

    def set_slide(self, index: int, title: str = "", body: str = "",
                  layout: Optional[str] = None) -> dict:
        """Replace slide content. If layout given, delete and recreate."""
        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()
        slides = pres.get("slides", [])

        if index < 0 or index >= len(slides):
            print(f"Error: index {index} out of range (0-{len(slides)-1})")
            return {"error": "index out of range"}

        if layout:
            # Delete old slide and insert new one at same position
            old_id = slides[index]["objectId"]
            self._slides.presentations().batchUpdate(
                presentationId=self._pres_id,
                body={"requests": [{"deleteObject": {"objectId": old_id}}]},
            ).execute()
            return self.insert_slide(index, title, body, layout)

        # Just update text in existing placeholders
        slide = slides[index]
        slide_id = slide["objectId"]
        self._clear_and_fill(slide, title, body)
        print(f"Updated slide [{index}]")
        return {"index": index, "id": slide_id}

    def delete_slide(self, index: int) -> dict:
        """Delete a slide by index."""
        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()
        slides = pres.get("slides", [])

        if index < 0 or index >= len(slides):
            print(f"Error: index {index} out of range")
            return {"error": "index out of range"}

        slide_id = slides[index]["objectId"]
        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": [{"deleteObject": {"objectId": slide_id}}]},
        ).execute()
        print(f"Deleted slide [{index}]")
        return {"index": index, "status": "deleted"}

    def move_slide(self, from_index: int, to_index: int) -> dict:
        """Move a slide from one position to another."""
        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()
        slides = pres.get("slides", [])

        if from_index < 0 or from_index >= len(slides):
            print(f"Error: from_index {from_index} out of range")
            return {"error": "index out of range"}

        slide_id = slides[from_index]["objectId"]
        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": [{
                "updateSlidesPosition": {
                    "slideObjectIds": [slide_id],
                    "insertionIndex": to_index,
                }
            }]},
        ).execute()
        print(f"Moved slide [{from_index}] → [{to_index}]")
        return {"from": from_index, "to": to_index}

    def img_slide(self, index: int, title: str = "",
                  image_url: str = "", caption: str = "",
                  layout: str = "blank") -> dict:
        """Set a slide with an image. Replaces existing slide at index,
        or appends if index == -1."""
        if index == -1:
            result = self.add_slide(title, "", layout)
            slide_id = result["id"]
            index = result["index"]
        else:
            pres = self._slides.presentations().get(
                presentationId=self._pres_id
            ).execute()
            slides = pres.get("slides", [])
            if index < 0 or index >= len(slides):
                print(f"Error: index {index} out of range")
                return {"error": "index out of range"}

            # Delete and recreate with blank layout
            old_id = slides[index]["objectId"]
            self._slides.presentations().batchUpdate(
                presentationId=self._pres_id,
                body={"requests": [{"deleteObject": {"objectId": old_id}}]},
            ).execute()
            result = self.insert_slide(index, "", "", layout)
            slide_id = result["id"]

        # Add title, image, and caption as custom elements
        requests = []
        y_cursor = 200000  # start y position in EMU

        if title:
            title_id = _uid()
            requests.append({
                "createShape": {
                    "objectId": title_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": 10800000, "unit": "EMU"},
                            "height": {"magnitude": 600000, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": 696000,
                            "translateY": y_cursor,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "insertText": {
                    "objectId": title_id,
                    "text": title,
                }
            })
            requests.append({
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": {
                        "bold": True,
                        "fontSize": {"magnitude": 24, "unit": "PT"},
                        "foregroundColor": {
                            "opaqueColor": {"rgbColor": {"red": 0.0, "green": 0.12, "blue": 0.36}}
                        },
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor",
                }
            })
            y_cursor += 700000

        if image_url:
            img_id = _uid()
            img_height = 4800000 if not caption else 4400000
            requests.append({
                "createImage": {
                    "objectId": img_id,
                    "url": image_url,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": 10800000, "unit": "EMU"},
                            "height": {"magnitude": img_height, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": 696000,
                            "translateY": y_cursor,
                            "unit": "EMU",
                        },
                    },
                }
            })
            y_cursor += img_height + 100000

        if caption:
            cap_id = _uid()
            requests.append({
                "createShape": {
                    "objectId": cap_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": 10800000, "unit": "EMU"},
                            "height": {"magnitude": 400000, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": 696000,
                            "translateY": y_cursor,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "insertText": {"objectId": cap_id, "text": caption}
            })
            requests.append({
                "updateTextStyle": {
                    "objectId": cap_id,
                    "style": {
                        "fontSize": {"magnitude": 11, "unit": "PT"},
                        "foregroundColor": {
                            "opaqueColor": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}
                        },
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "fontSize,foregroundColor",
                }
            })

        if requests:
            self._slides.presentations().batchUpdate(
                presentationId=self._pres_id,
                body={"requests": requests},
            ).execute()

        print(f"Image set on slide [{index}]")
        return {"index": index, "id": slide_id}

    # ------------------------------------------------------------------
    # Visual composition methods
    # ------------------------------------------------------------------

    def metric_slide(self, title: str, metrics: list[dict],
                     layout: str = "blank") -> dict:
        """Create a slide with metric cards.

        Args:
            title: slide title
            metrics: list of {"value": "4,006", "label": "episodes"} dicts (max 4)
            layout: base layout to use
        Returns:
            {"index": N, "id": slide_id}
        """
        result = self.add_slide(title or "", "", layout)
        slide_id = result["id"]
        index = result["index"]

        n = len(metrics)
        card_gap = 30 * PT
        total_w = SLIDE_W - 2 * MARGIN
        card_w = (total_w - (n - 1) * card_gap) // n
        card_h = 180 * PT
        card_y = SLIDE_H // 2 - card_h // 2 + 30 * PT  # slightly below center

        requests = []

        # Title at top
        if title:
            title_id = _uid()
            requests.extend(self._make_text_box(
                title_id, slide_id,
                x=MARGIN, y=35 * PT,
                w=total_w, h=50 * PT,
                text=title,
                font_size=36, bold=True, color=PENN_BLUE,
            ))

        # Metric cards
        for i, m in enumerate(metrics):
            card_x = MARGIN + i * (card_w + card_gap)

            # Card background (rounded rectangle)
            card_id = _uid()
            requests.append({
                "createShape": {
                    "objectId": card_id,
                    "shapeType": "ROUND_RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": card_w, "unit": "EMU"},
                            "height": {"magnitude": card_h, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": card_x, "translateY": card_y,
                            "unit": "EMU",
                        },
                    },
                }
            })
            # Style the card
            card_color = m.get("color", LIGHT_GRAY)
            requests.append({
                "updateShapeProperties": {
                    "objectId": card_id,
                    "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState",
                    "shapeProperties": {
                        "shapeBackgroundFill": {
                            "solidFill": {"color": {"rgbColor": card_color}}
                        },
                        "outline": {"propertyState": "NOT_RENDERED"},
                    },
                }
            })

            # Accent bar at top of card
            bar_id = _uid()
            bar_color = m.get("accent", ACCENT_BLUE)
            requests.append({
                "createShape": {
                    "objectId": bar_id,
                    "shapeType": "RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": card_w, "unit": "EMU"},
                            "height": {"magnitude": 5 * PT, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": card_x, "translateY": card_y,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "updateShapeProperties": {
                    "objectId": bar_id,
                    "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState",
                    "shapeProperties": {
                        "shapeBackgroundFill": {
                            "solidFill": {"color": {"rgbColor": bar_color}}
                        },
                        "outline": {"propertyState": "NOT_RENDERED"},
                    },
                }
            })

            # Big number
            val_id = _uid()
            text_color = WHITE if m.get("dark") else PENN_BLUE
            requests.extend(self._make_text_box(
                val_id, slide_id,
                x=card_x, y=card_y + 30 * PT,
                w=card_w, h=70 * PT,
                text=m["value"],
                font_size=48, bold=True, color=text_color,
                alignment="CENTER",
            ))

            # Label below number
            lbl_id = _uid()
            lbl_color = MID_GRAY if not m.get("dark") else {"red": 0.75, "green": 0.78, "blue": 0.82}
            requests.extend(self._make_text_box(
                lbl_id, slide_id,
                x=card_x, y=card_y + 105 * PT,
                w=card_w, h=40 * PT,
                text=m["label"],
                font_size=16, bold=False, color=lbl_color,
                alignment="CENTER",
            ))

        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": requests},
        ).execute()

        print(f"Metric slide [{index}]: {n} cards")
        return {"index": index, "id": slide_id}

    def steps_slide(self, title: str, steps: list[dict],
                    layout: str = "blank") -> dict:
        """Create a slide with numbered step cards.

        Args:
            title: slide title
            steps: list of {"number": "1", "text": "Description"} dicts
            layout: base layout
        """
        result = self.add_slide(title or "", "", layout)
        slide_id = result["id"]
        index = result["index"]

        n = len(steps)
        card_gap = 24 * PT
        total_w = SLIDE_W - 2 * MARGIN
        card_w = (total_w - (n - 1) * card_gap) // n
        card_h = 200 * PT
        card_y = SLIDE_H // 2 - card_h // 2 + 30 * PT

        requests = []

        for i, step in enumerate(steps):
            card_x = MARGIN + i * (card_w + card_gap)

            # Card bg
            card_id = _uid()
            requests.append({
                "createShape": {
                    "objectId": card_id,
                    "shapeType": "ROUND_RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": card_w, "unit": "EMU"},
                            "height": {"magnitude": card_h, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": card_x, "translateY": card_y,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "updateShapeProperties": {
                    "objectId": card_id,
                    "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState",
                    "shapeProperties": {
                        "shapeBackgroundFill": {
                            "solidFill": {"color": {"rgbColor": LIGHT_GRAY}}
                        },
                        "outline": {"propertyState": "NOT_RENDERED"},
                    },
                }
            })

            # Step number (large, accent colored)
            num_id = _uid()
            requests.extend(self._make_text_box(
                num_id, slide_id,
                x=card_x, y=card_y + 20 * PT,
                w=card_w, h=60 * PT,
                text=step.get("number", str(i + 1)),
                font_size=40, bold=True, color=ACCENT_BLUE,
                alignment="CENTER",
            ))

            # Step text
            txt_id = _uid()
            requests.extend(self._make_text_box(
                txt_id, slide_id,
                x=card_x + 15 * PT, y=card_y + 90 * PT,
                w=card_w - 30 * PT, h=90 * PT,
                text=step["text"],
                font_size=14, bold=False, color=DARK_TEXT,
                alignment="CENTER",
            ))

        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": requests},
        ).execute()

        print(f"Steps slide [{index}]: {n} steps")
        return {"index": index, "id": slide_id}

    def table_slide(self, title: str, headers: list[str],
                    rows: list[list[str]], layout: str = "blank") -> dict:
        """Create a slide with a styled table.

        Args:
            title: slide title
            headers: column header strings
            rows: list of row data (each row is a list of strings)
            layout: base layout
        """
        result = self.add_slide(title or "", "", layout)
        slide_id = result["id"]
        index = result["index"]

        requests = []

        if title:
            title_id = _uid()
            total_w = SLIDE_W - 2 * MARGIN
            requests.extend(self._make_text_box(
                title_id, slide_id,
                x=MARGIN, y=35 * PT,
                w=total_w, h=50 * PT,
                text=title,
                font_size=36, bold=True, color=PENN_BLUE,
            ))

        # Create table
        table_id = _uid()
        n_rows = len(rows) + 1  # +1 for header
        n_cols = len(headers)
        table_w = SLIDE_W - 2 * MARGIN
        table_h = min(n_rows * 50 * PT, SLIDE_H - 150 * PT)

        requests.append({
            "createTable": {
                "objectId": table_id,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": table_w, "unit": "EMU"},
                        "height": {"magnitude": table_h, "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": MARGIN,
                        "translateY": 110 * PT,
                        "unit": "EMU",
                    },
                },
                "rows": n_rows,
                "columns": n_cols,
            }
        })

        # Must batch-execute table creation first, then style it
        self._slides.presentations().batchUpdate(
            presentationId=self._pres_id,
            body={"requests": requests},
        ).execute()

        # Now fill and style the table
        requests2 = []

        # Header row - fill cells with Penn Blue
        for c, header in enumerate(headers):
            requests2.append({
                "insertText": {
                    "objectId": table_id,
                    "cellLocation": {"rowIndex": 0, "columnIndex": c},
                    "text": header,
                }
            })
            requests2.append({
                "updateTextStyle": {
                    "objectId": table_id,
                    "cellLocation": {"rowIndex": 0, "columnIndex": c},
                    "style": {
                        "bold": True,
                        "fontSize": {"magnitude": 14, "unit": "PT"},
                        "foregroundColor": {"opaqueColor": {"rgbColor": WHITE}},
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor",
                }
            })
            requests2.append({
                "updateTableCellProperties": {
                    "objectId": table_id,
                    "tableRange": {
                        "location": {"rowIndex": 0, "columnIndex": c},
                        "rowSpan": 1, "columnSpan": 1,
                    },
                    "tableCellProperties": {
                        "tableCellBackgroundFill": {
                            "solidFill": {"color": {"rgbColor": PENN_BLUE}}
                        }
                    },
                    "fields": "tableCellBackgroundFill.solidFill.color",
                }
            })

        # Data rows
        for r, row_data in enumerate(rows):
            for c, cell in enumerate(row_data):
                requests2.append({
                    "insertText": {
                        "objectId": table_id,
                        "cellLocation": {"rowIndex": r + 1, "columnIndex": c},
                        "text": cell,
                    }
                })
                requests2.append({
                    "updateTextStyle": {
                        "objectId": table_id,
                        "cellLocation": {"rowIndex": r + 1, "columnIndex": c},
                        "style": {
                            "fontSize": {"magnitude": 12, "unit": "PT"},
                            "foregroundColor": {"opaqueColor": {"rgbColor": DARK_TEXT}},
                        },
                        "textRange": {"type": "ALL"},
                        "fields": "fontSize,foregroundColor",
                    }
                })
                # Alternate row colors
                if r % 2 == 1:
                    requests2.append({
                        "updateTableCellProperties": {
                            "objectId": table_id,
                            "tableRange": {
                                "location": {"rowIndex": r + 1, "columnIndex": c},
                                "rowSpan": 1, "columnSpan": 1,
                            },
                            "tableCellProperties": {
                                "tableCellBackgroundFill": {
                                    "solidFill": {"color": {"rgbColor": LIGHT_GRAY}}
                                }
                            },
                            "fields": "tableCellBackgroundFill.solidFill.color",
                        }
                    })

        if requests2:
            self._slides.presentations().batchUpdate(
                presentationId=self._pres_id,
                body={"requests": requests2},
            ).execute()

        print(f"Table slide [{index}]: {n_rows}x{n_cols}")
        return {"index": index, "id": slide_id}

    # ------------------------------------------------------------------
    # Shape/text primitives
    # ------------------------------------------------------------------

    @staticmethod
    def _make_text_box(obj_id, page_id, x, y, w, h,
                       text, font_size=14, bold=False,
                       color=None, alignment="START"):
        """Return a list of API requests to create a styled text box."""
        color = color or DARK_TEXT
        requests = [
            {
                "createShape": {
                    "objectId": obj_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": page_id,
                        "size": {
                            "width": {"magnitude": w, "unit": "EMU"},
                            "height": {"magnitude": h, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": x, "translateY": y,
                            "unit": "EMU",
                        },
                    },
                }
            },
            {
                "insertText": {
                    "objectId": obj_id,
                    "text": text,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": obj_id,
                    "style": {
                        "bold": bold,
                        "fontSize": {"magnitude": font_size, "unit": "PT"},
                        "foregroundColor": {"opaqueColor": {"rgbColor": color}},
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor",
                }
            },
            {
                "updateParagraphStyle": {
                    "objectId": obj_id,
                    "style": {"alignment": alignment},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            },
        ]
        return requests

    # ------------------------------------------------------------------
    # Preview / thumbnail
    # ------------------------------------------------------------------

    def preview(self, indices=None, out_dir="/tmp/slide_preview"):
        """Download slide thumbnails as PNG for visual review.

        Args:
            indices: list of slide indices to preview, or None for all.
            out_dir: directory to save PNGs.
        Returns:
            list of saved file paths.
        """
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()
        slides = pres.get("slides", [])

        if indices is None:
            indices = list(range(len(slides)))

        saved = []
        for i in indices:
            if i < 0 or i >= len(slides):
                print(f"  Skipping index {i} (out of range)")
                continue

            page_id = slides[i]["objectId"]
            result = self._slides.presentations().pages().getThumbnail(
                presentationId=self._pres_id,
                pageObjectId=page_id,
                thumbnailProperties_thumbnailSize="LARGE",
                thumbnailProperties_mimeType="PNG",
            ).execute()

            url = result["contentUrl"]
            token = self._creds.token
            req = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req) as resp:
                data = resp.read()

            fpath = out_path / f"slide_{i:03d}.png"
            fpath.write_bytes(data)
            saved.append(str(fpath))
            print(f"  [{i}] → {fpath}")

        return saved

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_text(self, slide: dict) -> str:
        """Extract all text from a slide's page elements."""
        texts = []
        for elem in slide.get("pageElements", []):
            shape = elem.get("shape", {})
            for te in shape.get("text", {}).get("textElements", []):
                run = te.get("textRun", {})
                content = run.get("content", "").strip()
                if content:
                    texts.append(content)
        return " | ".join(texts)

    def _fill_placeholders(self, slide_id: str, title: str, body: str,
                           layout: str):
        """Fill placeholder text boxes in a layout-based slide."""
        # Re-fetch the slide to get placeholder IDs
        pres = self._slides.presentations().get(
            presentationId=self._pres_id
        ).execute()

        target_slide = None
        for s in pres.get("slides", []):
            if s["objectId"] == slide_id:
                target_slide = s
                break

        if not target_slide:
            return

        requests = []
        for elem in target_slide.get("pageElements", []):
            ph = elem.get("shape", {}).get("placeholder", {})
            ph_type = ph.get("type", "")
            obj_id = elem["objectId"]

            if ph_type in ("TITLE", "CENTERED_TITLE") and title:
                requests.append({
                    "insertText": {
                        "objectId": obj_id,
                        "text": title,
                    }
                })
            elif ph_type in ("BODY", "SUBTITLE") and body:
                if ph.get("index", 0) == 0:
                    requests.append({
                        "insertText": {
                            "objectId": obj_id,
                            "text": body,
                        }
                    })

        if requests:
            self._slides.presentations().batchUpdate(
                presentationId=self._pres_id,
                body={"requests": requests},
            ).execute()

    def _clear_and_fill(self, slide: dict, title: str, body: str):
        """Clear existing text in placeholders and refill."""
        requests = []

        for elem in slide.get("pageElements", []):
            shape = elem.get("shape", {})
            ph = shape.get("placeholder", {})
            ph_type = ph.get("type", "")
            obj_id = elem["objectId"]

            # Check if shape has text
            text_elems = shape.get("text", {}).get("textElements", [])
            has_text = any(
                te.get("textRun", {}).get("content", "").strip()
                for te in text_elems
            )

            if ph_type in ("TITLE", "CENTERED_TITLE"):
                if has_text:
                    requests.append({
                        "deleteText": {
                            "objectId": obj_id,
                            "textRange": {"type": "ALL"},
                        }
                    })
                if title:
                    requests.append({
                        "insertText": {
                            "objectId": obj_id,
                            "text": title,
                        }
                    })
            elif ph_type in ("BODY", "SUBTITLE") and ph.get("index", 0) == 0:
                if has_text:
                    requests.append({
                        "deleteText": {
                            "objectId": obj_id,
                            "textRange": {"type": "ALL"},
                        }
                    })
                if body:
                    requests.append({
                        "insertText": {
                            "objectId": obj_id,
                            "text": body,
                        }
                    })

        if requests:
            self._slides.presentations().batchUpdate(
                presentationId=self._pres_id,
                body={"requests": requests},
            ).execute()
