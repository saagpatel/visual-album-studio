# V2 Cloud Region and Data Residency Baseline

## Decision
- Cloud provider baseline: Supabase
- Primary region: `us-west-1` (N. California)
- Residency baseline: United States

## Rationale
- Team and primary operator location are US-based.
- Baseline latency alignment for initial V2 cloud rollout.
- Simplifies initial compliance and operations boundary for Train 4 cloud GA.

## Guardrails
- Production workloads must remain local-first safe when cloud is unavailable.
- Region migration and multi-region replication are deferred to post-v2 unless required by compliance.
- Any future non-US residency requirement requires ADR and migration plan before execution.

## Operational Notes
- Secrets and signing keys must not be stored in repo; use managed secret stores.
- Region and residency assumptions must be revalidated before Train 4 GA closeout.
