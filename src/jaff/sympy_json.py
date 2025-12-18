# ABOUTME: JSON serializer/deserializer for a safe subset of SymPy expressions
# ABOUTME: Provides a versioned, cross-SymPy-compatible AST format for JAFF

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import sympy

try:
    from sympy.core.symbol import Str as _SympyStr
except Exception:  # pragma: no cover
    _SympyStr = None

try:
    from sympy.matrices.expressions.matexpr import MatrixElement as _MatrixElement
except Exception:  # pragma: no cover
    _MatrixElement = None

try:
    from sympy.functions.elementary.piecewise import ExprCondPair as _ExprCondPair
except Exception:  # pragma: no cover
    _ExprCondPair = None


SCHEMA_VERSION = 1


class SympyJsonError(ValueError):
    pass


def dumps(expr: sympy.Basic, *, indent: int = 2, sort_keys: bool = True) -> str:
    payload = {
        "format": "jaff.sympy_json",
        "schema_version": SCHEMA_VERSION,
        "sympy_version": sympy.__version__,
        "expr": to_jsonable(expr),
    }
    return json.dumps(payload, indent=indent, sort_keys=sort_keys)


def loads(s: str) -> sympy.Basic:
    payload = json.loads(s)
    if not isinstance(payload, dict) or payload.get("format") != "jaff.sympy_json":
        raise SympyJsonError("Not a jaff.sympy_json payload")
    version = payload.get("schema_version")
    if version != SCHEMA_VERSION:
        raise SympyJsonError(f"Unsupported schema_version={version!r}")
    return from_jsonable(payload.get("expr"))


def to_jsonable(expr: sympy.Basic) -> Dict[str, Any]:
    if not isinstance(expr, sympy.Basic):
        raise TypeError(f"Expected sympy.Basic, got {type(expr)!r}")
    encoder = _Encoder()
    return encoder.encode(expr)


def from_jsonable(obj: Any) -> sympy.Basic:
    decoder = _Decoder()
    return decoder.decode(obj)


@dataclass(frozen=True)
class _SymbolKey:
    name: str
    assumptions: Tuple[Tuple[str, bool], ...]


@dataclass(frozen=True)
class _MatrixSymbolKey:
    name: str
    rows: Any
    cols: Any


class _Encoder:
    def encode(self, expr: sympy.Basic) -> Dict[str, Any]:
        if expr is sympy.true:
            return {"type": "BooleanTrue"}
        if expr is sympy.false:
            return {"type": "BooleanFalse"}

        if isinstance(expr, sympy.Symbol):
            return {
                "type": "Symbol",
                "name": expr.name,
                "assumptions": _encode_assumptions(expr),
            }

        if isinstance(expr, sympy.Integer):
            return {"type": "Integer", "value": int(expr)}

        if isinstance(expr, sympy.Rational) and not isinstance(expr, sympy.Integer):
            return {"type": "Rational", "p": int(expr.p), "q": int(expr.q)}

        if isinstance(expr, sympy.Float):
            return {
                "type": "Float",
                "value": str(expr),
                "prec": int(expr._prec),
                "mpf": list(expr._mpf_),
            }

        if _SympyStr is not None and isinstance(expr, _SympyStr):
            return {"type": "Str", "value": str(expr)}

        if isinstance(expr, sympy.MatrixSymbol):
            rows, cols = expr.shape
            return {
                "type": "MatrixSymbol",
                "name": expr.name,
                "rows": self.encode(sympy.Integer(rows)) if isinstance(rows, int) else self.encode(rows),
                "cols": self.encode(sympy.Integer(cols)) if isinstance(cols, int) else self.encode(cols),
            }

        if _MatrixElement is not None and isinstance(expr, _MatrixElement):
            return {
                "type": "MatrixElement",
                "base": self.encode(expr.parent),
                "i": self.encode(expr.i),
                "j": self.encode(expr.j),
            }

        if _ExprCondPair is not None and isinstance(expr, _ExprCondPair):
            return {
                "type": "ExprCondPair",
                "expr": self.encode(expr.expr),
                "cond": self.encode(expr.cond),
            }

        if isinstance(expr, sympy.StrictLessThan):
            return {
                "type": "StrictLessThan",
                "lhs": self.encode(expr.lhs),
                "rhs": self.encode(expr.rhs),
            }

        if isinstance(expr, sympy.StrictGreaterThan):
            return {
                "type": "StrictGreaterThan",
                "lhs": self.encode(expr.lhs),
                "rhs": self.encode(expr.rhs),
            }

        if isinstance(expr, sympy.Piecewise):
            pairs = []
            for pair in expr.args:
                if _ExprCondPair is None or not isinstance(pair, _ExprCondPair):
                    raise SympyJsonError("Unexpected Piecewise arg type")
                pairs.append(self.encode(pair))
            return {"type": "Piecewise", "pairs": pairs}

        if isinstance(expr, sympy.Pow):
            base, exp = expr.args
            return {"type": "Pow", "base": self.encode(base), "exp": self.encode(exp)}

        if isinstance(expr, sympy.Add):
            args = [self.encode(a) for a in expr.args]
            return {"type": "Add", "args": args}

        if isinstance(expr, sympy.Mul):
            args = [self.encode(a) for a in expr.args]
            return {"type": "Mul", "args": args}

        func = expr.func
        if func is sympy.exp:
            return {"type": "exp", "args": [self.encode(expr.args[0])]}
        if func is sympy.log:
            return {"type": "log", "args": [self.encode(a) for a in expr.args]}
        if func is sympy.Max:
            return {"type": "Max", "args": [self.encode(a) for a in expr.args]}
        if func is sympy.Min:
            return {"type": "Min", "args": [self.encode(a) for a in expr.args]}

        raise SympyJsonError(f"Unsupported SymPy node: {type(expr).__name__}")


class _Decoder:
    def __init__(self) -> None:
        self._symbol_cache: Dict[_SymbolKey, sympy.Symbol] = {}
        self._matrix_symbol_cache: Dict[_MatrixSymbolKey, sympy.MatrixSymbol] = {}

    def decode(self, obj: Any) -> sympy.Basic:
        if not isinstance(obj, dict):
            raise SympyJsonError(f"Expected dict node, got {type(obj)!r}")
        t = obj.get("type")
        if not isinstance(t, str):
            raise SympyJsonError("Missing/invalid node type")

        if t == "BooleanTrue":
            return sympy.true
        if t == "BooleanFalse":
            return sympy.false

        if t == "Symbol":
            name = obj.get("name")
            if not isinstance(name, str):
                raise SympyJsonError("Symbol.name must be a string")
            assumptions = obj.get("assumptions") or {}
            if not isinstance(assumptions, dict):
                raise SympyJsonError("Symbol.assumptions must be a dict")
            cleaned = _decode_assumptions(assumptions)
            key = _SymbolKey(name=name, assumptions=tuple(sorted(cleaned.items())))
            sym = self._symbol_cache.get(key)
            if sym is None:
                sym = sympy.Symbol(name, **cleaned)
                self._symbol_cache[key] = sym
            return sym

        if t == "Integer":
            value = obj.get("value")
            if not isinstance(value, int):
                raise SympyJsonError("Integer.value must be an int")
            return sympy.Integer(value)

        if t == "Rational":
            p = obj.get("p")
            q = obj.get("q")
            if not isinstance(p, int) or not isinstance(q, int):
                raise SympyJsonError("Rational.p and Rational.q must be ints")
            return sympy.Rational(p, q)

        if t == "Float":
            prec = obj.get("prec")
            mpf = obj.get("mpf")
            value = obj.get("value")
            if not isinstance(prec, int):
                raise SympyJsonError("Float.prec must be int")
            if not isinstance(value, str):
                raise SympyJsonError("Float.value must be str")
            if isinstance(mpf, list) and len(mpf) == 4 and all(isinstance(x, int) for x in mpf):
                if tuple(mpf) == (0, 0, 0, 0):
                    # Preserve Float(0.0) without canonicalizing to Integer(0)
                    return sympy.Float._new(tuple(mpf), prec, zero=False)
                try:
                    return sympy.Float._new(tuple(mpf), prec)
                except Exception:
                    pass
            return sympy.Float(value, prec)

        if t == "Str":
            value = obj.get("value")
            if not isinstance(value, str):
                raise SympyJsonError("Str.value must be a string")
            if _SympyStr is None:
                raise SympyJsonError("Str node unsupported in this SymPy build")
            return _SympyStr(value)

        if t == "MatrixSymbol":
            name = obj.get("name")
            if not isinstance(name, str):
                raise SympyJsonError("MatrixSymbol.name must be a string")
            rows = self.decode(obj.get("rows"))
            cols = self.decode(obj.get("cols"))
            key = _MatrixSymbolKey(name=name, rows=rows, cols=cols)
            msym = self._matrix_symbol_cache.get(key)
            if msym is None:
                msym = sympy.MatrixSymbol(name, rows, cols)
                self._matrix_symbol_cache[key] = msym
            return msym

        if t == "MatrixElement":
            base = self.decode(obj.get("base"))
            i = self.decode(obj.get("i"))
            j = self.decode(obj.get("j"))
            if _MatrixElement is None:
                raise SympyJsonError("MatrixElement node unsupported in this SymPy build")
            return _MatrixElement(base, i, j)

        if t == "ExprCondPair":
            expr = self.decode(obj.get("expr"))
            cond = self.decode(obj.get("cond"))
            if _ExprCondPair is None:
                raise SympyJsonError("ExprCondPair node unsupported in this SymPy build")
            return _ExprCondPair(expr, cond)

        if t == "StrictLessThan":
            lhs = self.decode(obj.get("lhs"))
            rhs = self.decode(obj.get("rhs"))
            return sympy.StrictLessThan(lhs, rhs)

        if t == "StrictGreaterThan":
            lhs = self.decode(obj.get("lhs"))
            rhs = self.decode(obj.get("rhs"))
            return sympy.StrictGreaterThan(lhs, rhs)

        if t == "Piecewise":
            pairs_obj = obj.get("pairs")
            if not isinstance(pairs_obj, list):
                raise SympyJsonError("Piecewise.pairs must be a list")
            pairs = []
            for p in pairs_obj:
                pair = self.decode(p)
                if _ExprCondPair is None or not isinstance(pair, _ExprCondPair):
                    raise SympyJsonError("Piecewise.pairs must contain ExprCondPair nodes")
                pairs.append((pair.expr, pair.cond))
            return sympy.Piecewise(*pairs, evaluate=False)

        if t == "Pow":
            base = self.decode(obj.get("base"))
            exp = self.decode(obj.get("exp"))
            return sympy.Pow(base, exp, evaluate=False)

        if t == "Add":
            args = _decode_args_list(obj.get("args"))
            return sympy.Add(*[self.decode(a) for a in args], evaluate=False)

        if t == "Mul":
            args = _decode_args_list(obj.get("args"))
            return sympy.Mul(*[self.decode(a) for a in args], evaluate=False)

        if t == "exp":
            args = _decode_args_list(obj.get("args"))
            if len(args) != 1:
                raise SympyJsonError("exp expects 1 arg")
            return sympy.exp(self.decode(args[0]))

        if t == "log":
            args = _decode_args_list(obj.get("args"))
            if len(args) not in (1, 2):
                raise SympyJsonError("log expects 1 or 2 args")
            return sympy.log(*[self.decode(a) for a in args])

        if t == "Max":
            args = _decode_args_list(obj.get("args"))
            return sympy.Max(*[self.decode(a) for a in args], evaluate=False)

        if t == "Min":
            args = _decode_args_list(obj.get("args"))
            return sympy.Min(*[self.decode(a) for a in args], evaluate=False)

        raise SympyJsonError(f"Unsupported node type: {t!r}")


def _decode_args_list(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        raise SympyJsonError("args must be a list")
    for item in value:
        if not isinstance(item, dict):
            raise SympyJsonError("args must contain dict nodes")
    return value


def _encode_assumptions(sym: sympy.Symbol) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for k, v in (sym.assumptions0 or {}).items():
        if isinstance(k, str) and isinstance(v, bool):
            out[k] = v
    return out


def _decode_assumptions(assumptions: Mapping[str, Any]) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for k, v in assumptions.items():
        if isinstance(k, str) and isinstance(v, bool):
            out[k] = v
    return out
