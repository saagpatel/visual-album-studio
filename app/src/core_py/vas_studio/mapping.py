import ast
import math
from dataclasses import dataclass
from typing import Dict

from .errors import VasError


@dataclass
class MappingContext:
    time_sec: float
    beat_phase: float
    tempo_bpm: float
    seed: int


_ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.Call,
}


_ALLOWED_FUNCS = {
    "sin": math.sin,
    "cos": math.cos,
    "clamp": lambda x, lo, hi: max(lo, min(x, hi)),
}


class MappingService:
    def validate_mapping(self, mapping_dsl: str) -> bool:
        for raw in mapping_dsl.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise VasError("E_MAPPING_PARSE_ERROR", f"Invalid mapping line: {line}")
            _, expr = line.split("=", 1)
            self._validate_expr(expr.strip())
        return True

    def _validate_expr(self, expr: str) -> None:
        tree = ast.parse(expr, mode="eval")
        for node in ast.walk(tree):
            if type(node) not in _ALLOWED_NODES:
                raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported expression node: {type(node).__name__}")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported function in mapping: {ast.dump(node.func)}")

    def evaluate(self, mapping_dsl: str, ctx: MappingContext) -> Dict[str, float]:
        env = {
            "time_sec": ctx.time_sec,
            "beat_phase": ctx.beat_phase,
            "tempo_bpm": ctx.tempo_bpm,
        }
        env.update(_ALLOWED_FUNCS)

        out: Dict[str, float] = {}
        for raw in mapping_dsl.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            param_id, expr = [p.strip() for p in line.split("=", 1)]
            self._validate_expr(expr)
            val = eval(compile(ast.parse(expr, mode="eval"), "<mapping>", "eval"), {"__builtins__": {}}, env)
            out[param_id] = float(val)
        return dict(sorted(out.items(), key=lambda item: item[0]))
