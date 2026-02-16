from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass
class VariantSpec:
    variant_id: str
    seed: int
    params: dict
    structural_change: str


class RemixEngine:
    def generate_variants(self, base_seed: int, count: int) -> list[VariantSpec]:
        variants = []
        for i in range(count):
            seed = base_seed + i
            variants.append(
                VariantSpec(
                    variant_id=f"variant_{i:03d}",
                    seed=seed,
                    params={
                        "mp.motion.float_amp": 10.0 + (i * 0.5),
                        "mp.beat.pulse_amount": 0.2 + (i * 0.01),
                        "mp.color.grade_amount": 0.05 + (i * 0.005),
                        "mp.layout.art_scale": 0.6 + (i * 0.002),
                        "mp.motion.zoom_amp": 0.01 + (i * 0.003),
                    },
                    structural_change=["layout", "palette", "typography"][i % 3],
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

    def validate_variant(self, base: VariantSpec, candidate: VariantSpec, min_changed: int = 5, threshold: float = 0.8) -> tuple[bool, float]:
        changed = sum(1 for k, v in candidate.params.items() if base.params.get(k) != v)
        score = self.distance(base, candidate)
        return (changed >= min_changed and candidate.structural_change != base.structural_change and score >= threshold), score


class BatchPlanner:
    def create_plan(self, variants: list[VariantSpec], max_concurrent: int = 2) -> dict:
        items = []
        for v in variants:
            items.append({"variant_id": v.variant_id, "status": "pending", "seed": v.seed})
        return {
            "max_concurrent": max_concurrent,
            "items": items,
        }

    def reviewer_report(self, variants: list[VariantSpec], remix: RemixEngine) -> dict:
        distances = []
        for i in range(1, len(variants)):
            distances.append(remix.distance(variants[i - 1], variants[i]))
        return {
            "summary": {
                "count": len(variants),
                "min_distance": min(distances) if distances else 0.0,
                "avg_distance": sum(distances) / len(distances) if distances else 0.0,
                "max_distance": max(distances) if distances else 0.0,
            },
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "seed": v.seed,
                    "structural_change": v.structural_change,
                    "changed_params": sorted(v.params.keys()),
                }
                for v in variants
            ],
        }
