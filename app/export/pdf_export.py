from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from playwright.sync_api import sync_playwright


_BROWSER_INSTALLED = False


def _ensure_playwright_chromium() -> None:
    """
    Streamlit Community Cloud installs the Python package, but not always
    the Playwright Chromium browser binary. This installs Chromium lazily
    on first PDF export.
    """
    global _BROWSER_INSTALLED

    if _BROWSER_INSTALLED:
        return

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )

    _BROWSER_INSTALLED = True


def html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> Path:
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    file_url = html_path.as_uri()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "0mm",
                    "right": "0mm",
                    "bottom": "0mm",
                    "left": "0mm",
                },
                prefer_css_page_size=True,
            )
            browser.close()

    except Exception:
        _ensure_playwright_chromium()

        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "0mm",
                    "right": "0mm",
                    "bottom": "0mm",
                    "left": "0mm",
                },
                prefer_css_page_size=True,
            )
            browser.close()

    return pdf_path
