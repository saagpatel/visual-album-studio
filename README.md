# Visual Album Studio

[![Python](https://img.shields.io/badge/python-%233776ab?style=flat-square&logo=python)](#) [![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](#)

> Your music, made visual — frame-accurate, resumable, and ready to distribute.

Visual Album Studio is a local-first desktop application for generating music-synced visual videos with deterministic, resumable export pipelines and optional distribution integrations. V1 and V2 are complete; the next-cycle roadmap covers provider policy watching, anomaly auto-triage, and scheduler simulation overlays.

## Features

- **Music-synced video generation** — frame-accurate visual output aligned to audio beat and structure
- **Deterministic export** — same inputs always produce the same output; full content hashing with BLAKE3
- **Resumable pipelines** — interrupted exports resume from the last verified checkpoint
- **DR rehearsal automation** — non-destructive disaster recovery rehearsal built into the verification suite
- **Anomaly auto-triage** — enriched anomaly detection with structured triage output
- **Provider policy watching** — NC-003 diff watcher ingests provider changelog and emits recommendations
- **Replay actor-filter correctness** — redaction-safe raw exports with verified replay integrity
- **Distribution integrations** — optional hooks for YouTube and other platforms

## Quick Start

### Prerequisites
- Python 3.11+
- ffmpeg

### Installation
```bash
git clone https://github.com/saagpatel/visual-album-studio
cd visual-album-studio
pip install -r app/requirements.txt
```

### Usage
```bash
# Run strict verification
env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh

# Run capstone audit (requires test video)
env VAS_SECURITY_STRICT=1 \
  VAS_YT_TEST_VIDEO_PATH=/path/to/test_video.mp4 \
  ./scripts/test/capstone_audit.sh
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Core | Custom pipeline engine (vas_studio) |
| Export verification | BLAKE3 content hashing |
| Database | SQLite (migrations in migrations/) |
| Testing | pytest (unit, integration, acceptance) |

## License

MIT
