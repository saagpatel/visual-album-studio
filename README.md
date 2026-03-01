# Visual Album Studio

Visual Album Studio is a local-first desktop application for generating music-synced visual videos with deterministic, resumable export pipelines and optional distribution integrations.

## Current State (2026-03-01)

- V1 closeout: complete
- V2 closeout: complete
- Post-V2 backlog waves: complete
- Next-cycle backlog (`NC-001..NC-003`, `NC-101..NC-103`, `NC-201..NC-203`): complete
- Audit follow-up remediations: complete (diagnostic scoping, non-destructive DR rehearsal, replay actor-filter correctness, redaction-safe raw exports)

Canonical source of truth for status and evidence:
- `docs/STATUS.md`

## Verification Baseline

Canonical verify command list:
- `.codex/verify.commands`

Run strict verification:

```bash
env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh
```

Run strict capstone (live closeout path):

```bash
env VAS_SECURITY_STRICT=1 \
  VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 \
  ./scripts/test/capstone_audit.sh
```

## Developer Entry Points

Primary implementation readme:
- `docs/00-readme.md`

Core planning and governance docs:
- `docs/20-phase-blueprint-v2.md`
- `docs/26-v2-test-verification.md`
- `docs/41-postv2-next-backlog.md`
- `docs/44-next-cycle-test-verification.md`
- `docs/19-risk-register.md`

## Notes

- Generated artifacts belong under `out/` and are gitignored.
- Security waivers for GA remain empty at `docs/security-waivers.json`.
