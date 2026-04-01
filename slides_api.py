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

# EMU constants (English Metric Units, 1 inch = 914400 EMU)
EMU_INCH = 914400
SLIDE_W = 12192000  # 13.333 inches (16:9)
SLIDE_H = 6858000   # 7.5 inches

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
