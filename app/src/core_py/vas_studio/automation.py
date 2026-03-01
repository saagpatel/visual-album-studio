from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VariantSpec:
    variant_id: str
    variant_spec_id: str
    source_rule_hash: str
    seed: int
    duration_sec: int
    params: dict
    structural_change: str
    grading_profile: str
    thumbnail_layout_rule: str
    palette_profile: str
    typography_profile: str
    audio_swap_id: str

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "variant_spec_id": self.variant_spec_id,
            "source_rule_hash": self.source_rule_hash,
            "seed": self.seed,
            "duration_sec": self.duration_sec,
            "params": dict(self.params),
            "structural_change": self.structural_change,
            "grading_profile": self.grading_profile,
            "thumbnail_layout_rule": self.thumbnail_layout_rule,
            "palette_profile": self.palette_profile,
            "typography_profile": self.typography_profile,
            "audio_swap_id": self.audio_swap_id,
        }


class RemixEngine:
    DEFAULT_RULE_SPEC = {
        "grading_profiles": ["clean", "cinematic", "high_contrast"],
        "thumbnail_layout_rules": ["safe_center", "safe_left", "safe_right"],
        "duration_cycle_sec": [10, 30, 600, 7200],
        "audio_swap_ids": [""],
        "palette_profiles": ["warm", "cool", "mono"],
        "typography_profiles": ["grotesk", "serif", "display"],
    }

    def generate_variants(self, base_seed: int, count: int, rule_spec: dict | None = None) -> list[VariantSpec]:
        normalized = self._normalize_rule_spec(rule_spec or {})
        spec_id = self._rule_spec_id(normalized)
        variants = []
        for i in range(count):
            seed = base_seed + i
            variants.append(
                VariantSpec(
                    variant_id=f"variant_{i:03d}",
                    variant_spec_id=spec_id,
                    source_rule_hash=spec_id,
                    seed=seed,
                    duration_sec=int(normalized["duration_cycle_sec"][i % len(normalized["duration_cycle_sec"])]),
                    params={
                        "mp.motion.float_amp": 10.0 + (i * 0.5),
                        "mp.beat.pulse_amount": 0.2 + (i * 0.01),
                        "mp.color.grade_amount": 0.05 + (i * 0.005),
                        "mp.layout.art_scale": 0.6 + (i * 0.002),
                        "mp.motion.zoom_amp": 0.01 + (i * 0.003),
                    },
                    structural_change=["layout", "palette", "typography"][i % 3],
                    grading_profile=str(normalized["grading_profiles"][i % len(normalized["grading_profiles"])]),
                    thumbnail_layout_rule=str(normalized["thumbnail_layout_rules"][i % len(normalized["thumbnail_layout_rules"])]),
                    palette_profile=str(normalized["palette_profiles"][i % len(normalized["palette_profiles"])]),
                    typography_profile=str(normalized["typography_profiles"][i % len(normalized["typography_profiles"])]),
                    audio_swap_id=str(normalized["audio_swap_ids"][i % len(normalized["audio_swap_ids"])]),
                )
            )
        return variants

    def distance(self, a: VariantSpec, b: VariantSpec) -> float:
        keys = sorted(set(a.params) | set(b.params))
        score = 0.0
        for k in keys:
            av = float(a.params.get(k, 0.0))
            bv = float(b.params.get(k, 0.0))
            score += abs(av - bv)
        if a.structural_change != b.structural_change:
            score += 1.0
        return score

    def validate_variant(
        self,
        base: VariantSpec,
        candidate: VariantSpec,
        min_changed: int = 5,
        threshold: float = 0.8,
        structural_change_required: bool = True,
    ) -> dict:
        changed = sum(1 for k, v in candidate.params.items() if base.params.get(k) != v)
        score = self.distance(base, candidate)
        has_structural_change = candidate.structural_change != base.structural_change
        rejection_code = ""
        if changed < min_changed:
            rejection_code = "E_VARIANT_CHANGED_PARAMS"
        elif structural_change_required and not has_structural_change:
            rejection_code = "E_VARIANT_STRUCTURAL_REQUIRED"
        elif score < threshold:
            rejection_code = "E_VARIANT_DISTANCE_TOO_LOW"
        return {
            "ok": rejection_code == "",
            "score": score,
            "changed_count": changed,
            "has_structural_change": has_structural_change,
            "rejection_code": rejection_code,
        }

    def _normalize_rule_spec(self, rule_spec: dict) -> dict:
        normalized = json.loads(json.dumps(self.DEFAULT_RULE_SPEC))
        for key, value in rule_spec.items():
            normalized[key] = value
        required = [
            "grading_profiles",
            "thumbnail_layout_rules",
            "duration_cycle_sec",
            "audio_swap_ids",
            "palette_profiles",
            "typography_profiles",
        ]
        for key in required:
            if not normalized.get(key):
                normalized[key] = list(self.DEFAULT_RULE_SPEC[key])
        return normalized

    def _rule_spec_id(self, spec: dict) -> str:
        payload = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return f"spec_{hashlib.sha256(payload).hexdigest()[:16]}"


class BatchPlanner:
    def create_plan(self, variants: list[VariantSpec], max_concurrent: int = 2, options: dict | None = None) -> dict:
        opts = options or {}
        now = int(time.time())
        window_start = str(opts.get("window_start", "22:00"))
        window_end = str(opts.get("window_end", "06:00"))
        retry_limit = int(opts.get("retry_limit", 2))
        backoff_policy = {
            "base_seconds": int(opts.get("backoff_base_seconds", 30)),
            "factor": int(opts.get("backoff_factor", 2)),
            "max_seconds": int(opts.get("backoff_max_seconds", 600)),
        }
        disk_guard_min_bytes = int(opts.get("disk_guard_min_bytes", 10 * 1024 * 1024 * 1024))
        output_dir = Path(str(opts.get("output_dir", ".")))
        disk_free_bytes = int(opts.get("disk_free_bytes", shutil.disk_usage(output_dir).free))
        status = "planned"
        blocked_reason = ""
        if disk_free_bytes < disk_guard_min_bytes:
            status = "blocked"
            blocked_reason = "E_DISK_GUARD_BLOCKED"

        items = []
        for v in variants:
            items.append(
                {
                    "variant_id": v.variant_id,
                    "status": "pending",
                    "seed": v.seed,
                    "attempts": 0,
                    "last_error_json": {},
                    "scheduled_at": now,
                }
            )
        return {
            "schema_version": 1,
            "status": status,
            "blocked_reason": blocked_reason,
            "max_concurrent": max_concurrent,
            "window_start": window_start,
            "window_end": window_end,
            "retry_limit": retry_limit,
            "backoff_policy": backoff_policy,
            "disk_guard_min_bytes": disk_guard_min_bytes,
            "disk_free_bytes": disk_free_bytes,
            "circuit_breaker": {
                "failure_threshold": int(opts.get("circuit_failure_threshold", 5)),
                "window_seconds": int(opts.get("circuit_window_seconds", 600)),
                "circuit_open": False,
            },
            "items": items,
        }

    def reviewer_report(self, variants: list[VariantSpec], remix: RemixEngine, near_duplicate_threshold: float = 0.8) -> dict:
        distances = []
        near_duplicates = []
        for i in range(1, len(variants)):
            score = remix.distance(variants[i - 1], variants[i])
            distances.append(score)
            if score < near_duplicate_threshold:
                near_duplicates.append(
                    {
                        "variant_a": variants[i - 1].variant_id,
                        "variant_b": variants[i].variant_id,
                        "distance_score": score,
                        "rejection_code": "E_VARIANT_DISTANCE_TOO_LOW",
                    }
                )
        return {
            "schema_version": 1,
            "summary": {
                "count": len(variants),
                "min_distance": min(distances) if distances else 0.0,
                "avg_distance": sum(distances) / len(distances) if distances else 0.0,
                "max_distance": max(distances) if distances else 0.0,
            },
            "flagged_near_duplicates": near_duplicates,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "variant_spec_id": v.variant_spec_id,
                    "seed": v.seed,
                    "structural_change": v.structural_change,
                    "changed_params_summary": {
                        "count": len(v.params),
                        "keys": sorted(v.params.keys()),
                    },
                    "changed_params": sorted(v.params.keys()),
                }
                for v in variants
            ],
        }

    def evaluate_circuit_breaker(self, failure_timestamps: list[int], now_ts: int | None = None, threshold: int = 5, window_seconds: int = 600) -> dict:
        now = int(time.time()) if now_ts is None else int(now_ts)
        recent = sum(1 for ts in failure_timestamps if now - int(ts) <= window_seconds)
        return {
            "recent_failures": recent,
            "circuit_open": recent >= threshold,
            "threshold": threshold,
            "window_seconds": window_seconds,
        }

    def mark_item_failure(self, item: dict, error_code: str, retry_limit: int = 2) -> dict:
        out = dict(item)
        attempts = int(out.get("attempts", 0)) + 1
        out["attempts"] = attempts
        out["last_error_json"] = {"error_code": error_code}
        out["status"] = "failed" if attempts > retry_limit else "pending"
        return out
