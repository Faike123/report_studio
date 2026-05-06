from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright


def html_to_pdf(html_path, pdf_path):
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 794, "height": 1123},
            device_scale_factor=1,
        )

        page.goto(html_path.as_uri(), wait_until="networkidle")

        page.pdf(
            path=str(pdf_path),
            width="210mm",
            height="297mm",
            print_background=True,
            prefer_css_page_size=True,
            margin={
                "top": "0mm",
                "right": "0mm",
                "bottom": "0mm",
                "left": "0mm",
            },
        )

        browser.close()

    return pdf_path
