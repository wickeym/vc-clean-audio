# vc-clean-audio

`vc-clean-audio` is a Windows-first, script-driven starter project for building a GTA Vice City dialogue cleanup pipeline. The goal is to make it practical to catalog game audio, prepare it for transcription, rewrite or sanitize spoken lines, regenerate cleaned dialogue, and package outputs with as little manual work as possible.

This repo is intentionally focused on **GTA Vice City**, not San Andreas. It is also intentionally conservative at this stage: the foundation is here, but decoding, transcription, separation, TTS, alignment, and packaging are still starter implementations with clear TODOs rather than fake end-to-end claims.

## Project goals

- Keep the workflow batch-oriented and script-first.
- Separate repo code from the live game install.
- Use config-driven paths so the same pipeline can be moved or adapted later.
- Prefer free tools where practical.
- Avoid committing game assets, decoded audio, intermediate stems, or final outputs.
- Leave clean extension points for future transcription, profanity replacement, source separation, TTS, alignment, and mod packaging.

## Planned pipeline

The intended long-term flow is:

1. `catalog`: scan source audio and build a machine-readable inventory.
2. `decode`: convert game audio into a workable intermediate format when tooling is ready.
3. `classify`: separate speech-heavy assets from music, SFX, or unsupported files.
4. `transcribe`: generate transcripts for candidate dialogue assets.
5. `clean_text`: apply profanity replacement and rewrite rules.
6. `separate`: split speech from backing audio where needed.
7. `tts`: regenerate cleaned lines with the selected voice workflow.
8. `align_mix`: line up regenerated speech and prepare replacement mixes.
9. `package`: assemble outputs for reinsertion into the Vice City modding workflow.

At the moment, `catalog` is the most complete step. The rest are real starter scripts with logging, config loading, and output directory setup so we can expand them incrementally.

## Repo layout

```text
vc-clean-audio/
├── config/
│   ├── paths.example.yaml
│   ├── pipeline.example.yaml
│   ├── profanity_map.json
│   └── rewrite_rules.json
├── metadata/
│   └── .gitkeep
├── scripts/
│   ├── catalog.py
│   ├── decode.py
│   ├── classify.py
│   ├── transcribe.py
│   ├── clean_text.py
│   ├── separate.py
│   ├── tts.py
│   ├── align_mix.py
│   └── package.py
├── src/
│   └── vc_clean_audio/
│       ├── config.py
│       ├── bootstrap.py
│       ├── logging_utils.py
│       └── pipeline.py
├── .gitignore
├── README.md
├── requirements.txt
└── run_pipeline.py
```

## Getting started

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Create local config files

Copy the example configs so you can keep machine-specific paths out of git:

```powershell
Copy-Item config\paths.example.yaml config\paths.yaml
Copy-Item config\pipeline.example.yaml config\pipeline.yaml
```

The default example already points `gta_vc_root` at `C:\Games\GTA_VC`, but you should still review and adjust paths for your setup.

### 3. Run the catalog step

```powershell
python run_pipeline.py --step catalog
```

If your live config files do not exist yet, the runner will fall back to the example YAML files.

The catalog step scans `input_audio_dir` recursively and writes a CSV to `metadata/catalog.csv`.

## Configuration notes

- `config/paths*.yaml` controls physical locations such as the Vice City install, working directories, and tool directories.
- `config/pipeline*.yaml` is for per-step settings such as catalog filters, transcription defaults, separation thresholds, and packaging behavior.
- `config/profanity_map.json` is the starter replacement dictionary for profanity cleanup.
- `config/rewrite_rules.json` is the starter rewrite rules file for more contextual text changes later.

## Design choices

- `pathlib` is used throughout to keep Windows path handling readable and safe.
- Relative paths in config are resolved from the repo root, not from the `config/` folder.
- The shared code in `src/vc_clean_audio/` keeps step scripts small and easy to extend.
- The starter scripts do not assume GTA Vice City audio can already be decoded directly by Python. That work is intentionally left for a later tool integration step.

## Next sensible additions

- Add a real decoder wrapper around the chosen Vice City audio tooling.
- Add speech-file heuristics in `classify`.
- Add Whisper-based transcription as an optional module.
- Add profanity replacement and rewrite tracking with before/after audit data.
- Add packaging rules once the target reinsertion format is locked down.
