# Report Studio

A Streamlit-based geotechnical reporting prototype.

## What it does

- Upload AGS, Flowfinity-style CSV ZIPs, XLSX proformas, and mixed project packs
- Detect reportable project data
- Build a controlled reporting queue
- Review borehole logs, DCP/ICBR outputs, soakaway reports, AGS exports, and audit reports
- Export PDF and AGS packages

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Entry point

streamlit_app.py

## Status

Prototype / demo build.
