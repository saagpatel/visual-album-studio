# Audio Engine (Import, Analysis, Mixing)

This document specifies audio handling across the full project.

## Goals
- Deterministic audio decoding and analysis.
- Stable mapping signals for visuals (beat phase, onset, energy).
- Deterministic offline bounce for multi-track soundscapes (Phase 3).
- Loop-safe audio for long-duration renders.

## Audio import (Phase 1)

### Supported input formats
Supported via FFmpeg decode:
- WAV
- MP3
- FLAC
- AAC / M4A
- AIFF

Implementation rule:
- If FFmpeg can decode it, it can be imported, but **acceptance tests** only guarantee the formats above.

### Canonical WAV cache (RQ-002)
All imported audio is converted into a canonical WAV for downstream use.

**Canonical format (locked):**
- Sample rate: **48,000 Hz**
- Channels: **2 (stereo)**
- Sample format: **PCM s16le**
- Container: **WAV**

Rationale:
- 48kHz aligns cleanly with 30 fps (48,000 / 30 = 1600 samples per frame), preventing A/V drift in frame-stepped exports.

### Canonical decode command (reference)
Exact flags may vary by platform but must be equivalent.

```bash
ffmpeg -y -i "<input>"   -vn -ac 2 -ar 48000 -sample_fmt s16   "<library>/audio/<sha256>.wav"
```

## Audio analysis (Phase 1 baseline, Phase 3 expanded)

### Worker model
- Audio analysis runs in a **separate local Python worker process**.
- IPC is newline-delimited JSON messages + file paths. No raw audio bytes in IPC.

### Phase 1 analysis outputs (minimum)
- `tempo_bpm` (float)
- `beat_times_sec` (array of float seconds)
- `duration_sec`
- `analysis_profile_id`
- `analysis_version`

### Phase 3 analysis enhancements (planned)
- Onset envelope / onset strength
- RMS energy
- Spectral centroid / rolloff
- (Optional) chroma features

### Analysis profiles and versioning
- An **analysis_profile** defines:
  - sample rate used by analysis (may downsample from canonical)
  - hop length
  - algorithm settings
- `analysis_version` is a deterministic string containing:
  - librosa version
  - numpy/scipy versions
  - analysis_profile_id
  - algorithm settings hash

Cache key:
- `(audio_sha256, analysis_profile_id, analysis_version)`

### Cache invalidation rules
- If canonical WAV changes (hash changes): recompute analysis.
- If analysis_version changes: recompute analysis.
- Old cached versions are preserved for reproducibility of historical exports.

## Mapping signals (stable interface)

The mapping engine consumes a stable set of audio-derived signals. These names are stable contract keys used by mappings.

### Phase 1 stable signals
- `tempo_bpm`
- `beat_index` (integer at time t)
- `beat_phase` (0..1 between beats)
- `is_beat` (bool at frame boundary)
- `time_sec`

### Phase 3 additional signals
- `onset_strength` (float)
- `rms` (float)
- `spectral_centroid` (float)

Rules:
- Signals must be computed deterministically from cached analysis.
- If a signal is unavailable, mapping evaluation must fall back to default values and log a non-fatal warning.

## Mixing and soundscape design (Phase 3)

### Data model (minimum)
Per track:
- volume (dB)
- pan (-1..+1)
- start offset (ms)
- loop region (start/end ms)
- fade in/out (ms)

Project-level:
- master gain
- optional limiter preset
- target duration / loop behavior

### Offline bounce (authoritative approach)
- Use FFmpeg filtergraphs for mixing:
  - `amix` for summing
  - `acrossfade` for transitions (optional)
  - `aloop` for looping where needed

#### Bounce requirements
- Deterministic: identical inputs → identical WAV hash (same pinned FFmpeg build).
- Loop-safe: no audible click at loop boundary.

### Reference filtergraph patterns

#### Basic mix (two tracks)
```bash
ffmpeg -y   -i track1.wav -i track2.wav   -filter_complex "[0:a]volume=0dB[a0];[1:a]volume=-3dB[a1];[a0][a1]amix=inputs=2:normalize=0[m]"   -map "[m]" -ac 2 -ar 48000 -sample_fmt s16 "<out>.wav"
```

#### Looping a single source to duration
```bash
ffmpeg -y -stream_loop -1 -i source.wav -t <seconds> -c copy "<out>.wav"
```

(Implementation note: for click-free loops, Phase 3 must support crossfade or exact loop point selection.)

### Loudness and clipping
- Default behavior must avoid clipping:
  - Either scale the mix (conservative gain) or provide an optional limiter.
- If limiter is used, record the preset and parameters in build_manifest/provenance.

## Verification (audio)
- Phase 1: A/V sync drift < 1 frame at end for reference projects.
- Phase 3: Sample-level loop boundary test:
  - compare N samples before end and after start; ensure diff below threshold.
