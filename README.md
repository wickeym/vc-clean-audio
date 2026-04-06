# vc-clean-audio

`vc-clean-audio` is a Windows-first starter repo for building a batch audio modding pipeline for **GTA Vice City**. The immediate goal is to inventory Vice City audio cleanly and build the project structure needed for later stages like transcription, profanity cleanup, dialogue regeneration, alignment, and packaging.

This repo is intentionally honest about its current state:

- `catalog` is usable now.
- `decode` is implemented as a first-pass FFmpeg-driven stage.
- The later stages are starter scaffolds with logging and TODOs.
- The repo does **not** claim every Vice City audio format is already supported, or that transcription, TTS, alignment, or reinsertion already work.

## What works right now

Right now, the useful implemented steps are:

- `catalog`: recursively scan an audio directory, collect file metadata, and write `metadata/catalog.csv`
- `decode`: convert supported inputs to working WAV files and update the catalog with decode results

The catalog does **not** decode game audio. It only inventories files so we can make informed decisions about decoding and later automation.

## Exact first run: catalog

From `C:\dev\vc-clean-audio`, run these commands in PowerShell:

```powershell
python -m pip install -r requirements.txt
Copy-Item config\paths.example.yaml config\paths.yaml
Copy-Item config\pipeline.example.yaml config\pipeline.yaml
python run_pipeline.py --step catalog --verbose
```

If you only want a quick smoke test first:

```powershell
python run_pipeline.py --step catalog --limit 25 --verbose
```

Expected result:

- The script scans `input_audio_dir`
- It writes `metadata/catalog.csv`
- The log tells you which config files were used
- The log prints a small extension summary

## Default config behavior

The example paths are already pointed at your current Vice City install:

- `gta_vc_root: C:/Games/GTA_VC`
- `input_audio_dir: C:/Games/GTA_VC/audio`

The runner will fall back to the example YAML files if `config/paths.yaml` or `config/pipeline.yaml` do not exist yet. That makes first-run setup easier, but copying the example files is still recommended so your local paths stay explicit.

## Repo layout

```text
vc-clean-audio/
|-- config/
|   |-- paths.example.yaml
|   |-- pipeline.example.yaml
|   |-- profanity_map.json
|   `-- rewrite_rules.json
|-- metadata/
|   `-- .gitkeep
|-- scripts/
|   |-- catalog.py
|   |-- decode.py
|   |-- classify.py
|   |-- transcribe.py
|   |-- clean_text.py
|   |-- separate.py
|   |-- tts.py
|   |-- align_mix.py
|   `-- package.py
|-- src/
|   `-- vc_clean_audio/
|       |-- bootstrap.py
|       |-- config.py
|       |-- logging_utils.py
|       `-- pipeline.py
|-- .gitignore
|-- requirements.txt
`-- run_pipeline.py
```

## Practical workflow

1. Start with `catalog` to learn what is actually in `C:\Games\GTA_VC\audio`.
2. Use that catalog to decide which file groups need custom Vice City decoding support.
3. Add decoding only after the source formats and toolchain are clear.
4. Add classification and transcription only after decoded dialogue candidates exist.
5. Add cleanup, TTS, alignment, and packaging only after there is a trustworthy manifest chain between stages.

## Current pipeline stages

### `catalog`

Implemented now.

- Loads config from YAML
- Scans `input_audio_dir` recursively
- Filters by configured file extensions
- Writes `metadata/catalog.csv`
- Records `source_path`, `relative_path`, `filename`, `extension`, `size_bytes`, and `discovered_at`

### `decode`

Implemented as a first practical stage.

- Reads `metadata/catalog.csv`
- Uses FFmpeg where available
- Writes standardized PCM WAV outputs under `work/decoded_wav`
- Updates the catalog with `decoded_wav_path`, `duration_seconds`, `sample_rate`, and `channels`
- Logs decode failures and continues instead of pretending unsupported formats work

Run it after catalog:

```powershell
python run_pipeline.py --step decode --verbose
```

### `classify`

Not implemented yet.

- Intended to separate likely dialogue assets from music, ambience, and unknown assets

### `transcribe`

Not implemented yet.

- Intended to convert candidate dialogue clips into transcript records

### `clean_text`

Not implemented yet.

- Intended to apply profanity replacements and rewrite rules to transcripts

### `separate`

Not implemented yet.

- Intended for optional speech/music separation if the chosen workflow actually benefits from it

### `tts`

Not implemented yet.

- Intended to generate replacement dialogue audio from cleaned text

### `align_mix`

Not implemented yet.

- Intended to align regenerated speech against source timing and prepare usable mixes

### `package`

Not implemented yet.

- Intended to assemble final outputs for the Vice City modding workflow

## Configuration files

### `config/paths.example.yaml`

Controls machine-specific paths:

- `gta_vc_root`
- `input_audio_dir`
- `work_dir`
- `output_dir`
- `tools_dir`

Relative paths are resolved from the repo root, not from the `config` directory.

### `config/pipeline.example.yaml`

Controls per-step behavior such as:

- which extensions `catalog` includes
- where `catalog` writes its CSV
- placeholder settings for later stages

### `config/profanity_map.json`

Starter profanity replacement map for future transcript cleanup.

### `config/rewrite_rules.json`

Starter rewrite rule file for future text normalization and protected terms.

## Windows notes

- Use `python -m pip install -r requirements.txt` instead of relying on the `py` launcher.
- Keep the repo separate from `C:\Games\GTA_VC`.
- Do not commit decoded audio, generated stems, transcripts, or packaged outputs.
- The starter config uses forward slashes in YAML because they are reliable on Windows and still resolve correctly with `pathlib`.

## Design choices

- `pathlib` is used throughout for path handling.
- The runner logs which config files were selected, including example-file fallback.
- The unfinished stages are explicit scaffolds with TODOs rather than fake functionality.
- The repo keeps code, config, metadata, and future outputs clearly separated.

## Suggested next step after catalog

Once `metadata/catalog.csv` exists, the next practical move is to inspect which Vice City audio file types and folder patterns appear most often. That should drive the real decoder integration instead of guessing up front.
