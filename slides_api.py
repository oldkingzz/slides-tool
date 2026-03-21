"""
Google Slides helper — talks to an Apps Script web app.

No OAuth or credentials.json needed. Just the web app URL in config.json.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

_HERE = Path(__file__).resolve().parent
CONFIG_PATH = _HERE / "config.json"


def _load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Create it with:\n"
            '  {"webapp_url": "https://script.google.com/macros/s/.../exec"}'
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)


def _post(payload):
    """Send a command to the Apps Script web app."""
    cfg = _load_config()
    url = cfg["webapp_url"]
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Apps Script redirects on deploy — follow it
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Apps Script error ({e.code}): {body}")

    # Apps Script web apps return a redirect (302) that urllib follows,
    # but the final response is the JSON. Parse it.
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        # Sometimes the response is HTML (auth page). Print it for debug.
        raise RuntimeError(f"Unexpected response (not JSON):\n{body[:500]}")


class SlidesHelper:
    def list_slides(self):
        """List all slides with index and preview."""
        result = _post({"command": "list"})
        if "error" in result:
            print(f"Error: {result['error']}")
            return []
        print(f"Total slides: {result['total']}")
        print("-" * 60)
        for s in result["slides"]:
            preview = s["preview"] or "(empty)"
            print(f"  [{s['index']}] {preview}")
        return result["slides"]

    def add_slide(self, title="", body=""):
        """Add a new slide at the end."""
        result = _post({"command": "add", "title": title, "body": body})
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Added slide [{result['index']}]")
        return result

    def set_slide(self, index, title="", body=""):
        """Replace slide content at given index."""
        result = _post({"command": "set", "index": index, "title": title, "body": body})
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Updated slide [{result['index']}]")
        return result

    def clear_slide(self, index):
        """Clear all content from a slide."""
        result = _post({"command": "clear", "index": index})
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Cleared slide [{result['index']}]")
        return result

    def delete_slide(self, index):
        """Delete a slide by index."""
        result = _post({"command": "delete", "index": index})
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Deleted slide [{result['index']}]")
        return result
