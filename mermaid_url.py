"""Generate mermaid.ink image URLs from Mermaid diagram code."""

import base64
import sys


def mermaid_to_url(code: str, fmt: str = "img") -> str:
    """Convert Mermaid code to a mermaid.ink URL.

    Args:
        code: Mermaid diagram source code
        fmt: 'img' for PNG, 'svg' for SVG
    """
    encoded = base64.urlsafe_b64encode(code.encode()).decode()
    return f"https://mermaid.ink/{fmt}/{encoded}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        code = sys.stdin.read()
    print(mermaid_to_url(code.strip()))
