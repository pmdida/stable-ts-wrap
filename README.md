# stable-ts-wrap: Web SRT Generator for Instagram

A ready-to-deploy Gradio web app that wraps your stable-ts subtitle workflow for team usage.

## What this app supports

- Required audio upload
- Optional transcript upload:
  - if present: runs **alignment** (`model.align`)
  - if absent: runs **transcription** (`model.transcribe`)
- Language selector: English, French, Spanish, Russian
- Configurable subtitle knobs:
  - Split silence threshold
  - Merge silence threshold
  - Max characters per line
  - Subtitle end padding
- Caching of raw alignment/transcription JSON results keyed by input + params

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:7860

## Deploy (free tier recommendation): Hugging Face Spaces

1. Create a new **Gradio Space** (free tier).
2. Push this repository files to the Space.
3. Ensure `requirements.txt` is present.
4. Space will auto-build and expose the app URL for coworkers.

## Notes

- First run for each unique input/setting can be slow due to model inference.
- Cached JSON results are stored in `./cache`.
- Default model size is `small`; switch to `tiny/base` if you need faster turnaround.
