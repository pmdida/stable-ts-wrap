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

### 0) System dependencies

`stable-ts` requires `ffmpeg`.

- macOS (Homebrew): `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`

### 1) Create environment

Python 3.10 or 3.11 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel "setuptools<81"
```

### 2) Install Python dependencies

Use the provided constraints file to avoid the `pkg_resources` build error from `openai-whisper`:

```bash
pip install --no-build-isolation -c constraints.txt -r requirements.txt
```

### 3) Run the app

```bash
python app.py
```

Then open http://localhost:7860

## Deploy (free tier recommendation): Hugging Face Spaces

1. Create a new **Gradio Space** (free tier).
2. Push this repository files to the Space.
3. Ensure `requirements.txt` is present.
4. In Space settings, set Python runtime to 3.10 or 3.11.
5. Space will auto-build and expose the app URL for coworkers.

## Troubleshooting

### `ModuleNotFoundError: No module named 'pkg_resources'` when installing

This comes from `openai-whisper` build tooling when an incompatible setuptools version is used in build isolation.

Use:

```bash
python -m pip install --upgrade pip wheel "setuptools<81"
pip install --no-build-isolation -c constraints.txt -r requirements.txt
```

If needed, recreate the virtual environment and retry.

## Notes

- First run for each unique input/setting can be slow due to model inference.
- Cached JSON results are stored in `./cache`.
- Default model size is `small`; switch to `tiny/base` if you need faster turnaround.
