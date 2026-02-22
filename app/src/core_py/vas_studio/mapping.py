import ast
import math
import operator
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


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}


_UNARY_OPS = {
    ast.USub: operator.neg,
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

    def _parse_and_validate_expr(self, expr: str) -> ast.Expression:
        tree = ast.parse(expr, mode="eval")
        for node in ast.walk(tree):
            if type(node) not in _ALLOWED_NODES:
                raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported expression node: {type(node).__name__}")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported function in mapping: {ast.dump(node.func)}")
        return tree

    def _validate_expr(self, expr: str) -> None:
        self._parse_and_validate_expr(expr)

    def _eval_expr(self, tree: ast.Expression, env: Dict[str, float]) -> float:
        def _eval_node(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return float(node.value)
                raise VasError("E_MAPPING_PARSE_ERROR", "Only numeric constants are allowed")
            if isinstance(node, ast.Name):
                if node.id not in env:
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Unknown variable: {node.id}")
                val = env[node.id]
                if not isinstance(val, (int, float)):
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Invalid variable type: {node.id}")
                return float(val)
            if isinstance(node, ast.BinOp):
                op = _BIN_OPS.get(type(node.op))
                if op is None:
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported binary operator: {type(node.op).__name__}")
                return float(op(_eval_node(node.left), _eval_node(node.right)))
            if isinstance(node, ast.UnaryOp):
                op = _UNARY_OPS.get(type(node.op))
                if op is None:
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported unary operator: {type(node.op).__name__}")
                return float(op(_eval_node(node.operand)))
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise VasError("E_MAPPING_PARSE_ERROR", "Function call must reference an allowed function name")
                fn = _ALLOWED_FUNCS.get(node.func.id)
                if fn is None:
                    raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported function: {node.func.id}")
                args = [_eval_node(arg) for arg in node.args]
                return float(fn(*args))
            raise VasError("E_MAPPING_PARSE_ERROR", f"Unsupported expression node: {type(node).__name__}")

        return _eval_node(tree)

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
            tree = self._parse_and_validate_expr(expr)
            val = self._eval_expr(tree, env)
            out[param_id] = float(val)
        return dict(sorted(out.items(), key=lambda item: item[0]))
