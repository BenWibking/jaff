from typing import Any

import sympy as sp

from jaff import Network


class Codegen:
    def __init__(
        self,
        network: Network,
        lang: str = "c++",
        brac_format: str = "",
        matrix_format: str = "",
    ):
        # Supported language inputs
        __lang_aliases: dict[str, str] = {
            "c++": "cxx",
            "cpp": "cxx",
            "cxx": "cxx",
            "c": "c",
            "fortran": "fortran",
            "f90": "fortran",
            "python": "python",
            "py": "python",
        }

        # Modifiers for each language
        __lang_modifiers: dict[str, dict[str, Any]] = {
            "cxx": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.cxxcode,
                "idx_offset": 0,
                "comment": "//",
            },
            "c": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.ccode,
                "idx_offset": 0,
                "comment": "//",
            },
            "fortran": {
                "brac": "()",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": ")(",
                "code_gen": sp.fcode,
                "idx_offset": 1,
                "comment": "!",
            },
            "python": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": ", ",
                "code_gen": sp.pycode,
                "idx_offset": 0,
                "comment": "#",
            },
        }

        # 2D array formats.
        # Implemented as a dictionary to keep things flexible for the future
        __matrix_formats: dict[str, dict[str, str]] = {
            "()": {"brac": "()", "sep": ")("},
            "(,)": {"brac": "()", "sep": ", "},
            "[]": {"brac": "[]", "sep": "]["},
            "[,]": {"brac": "[]", "sep": ", "},
            "{}": {"brac": "{}", "sep": "}{"},
            "{,}": {"brac": "{}", "sep": ", "},
            "<>": {"brac": "<>", "sep": "><"},
            "<,>": {"brac": "<>", "sep": ", "},
        }

        # 1D array format
        __brack_formats: list[str] = ["()", "{}", "[]", "<>"]

        # Check if language is supported
        if lang and lang not in __lang_aliases.keys():
            raise ValueError(
                f"\n\nUnsupported language: '{lang}'"
                f"\nSupported languages: {[key for key in __lang_aliases]}\n"
            )

        # Check if 2D array format is supported
        if matrix_format and matrix_format not in __matrix_formats.keys():
            raise ValueError(
                f"\n\nUnsupported matrix format: '{matrix_format}'"
                f"\nSupported matrix formats: {[key for key in __matrix_formats]}\n"
            )

        # Check if 1D array format is supported
        if brac_format and brac_format not in __brack_formats:
            raise ValueError(
                f"\n\nUnsupported bracket format: '{brac_format}'"
                f"\nSupported bracket formats: {[key for key in __brack_formats]}\n"
            )

        # Set language
        language = __lang_aliases.get(lang, "cxx")

        # Set brackets for 1D array
        bracs = (
            brac_format
            if brac_format in __brack_formats
            else __lang_modifiers[language]["brac"]
        )

        # Set brackets for 2D array
        mbracs = (
            __matrix_formats[matrix_format]["brac"]
            if matrix_format
            else __lang_modifiers[language]["brac"]
        )

        # Set 2D array separator
        self.matrix_sep = (
            __matrix_formats[matrix_format]["sep"]
            if matrix_format
            else __lang_modifiers[language]["matrix_sep"]
        )

        # Assigen other required variables
        self.assignment_op = __lang_modifiers[language]["assignment_op"]
        self.line_end = __lang_modifiers[language]["line_end"]
        self.code_gen = __lang_modifiers[language]["code_gen"]
        self.ioff = __lang_modifiers[language]["idx_offset"]
        self.comment = __lang_modifiers[language]["comment"]

        # Set left and right brackets for 1D and 2D arrays
        self.lb, self.rb = bracs
        self.mlb, self.mrb = mbracs

        # Set network object
        self.net = network

    def get_commons(
        self, idx_offset: int = -1, idx_prefix: str = "", definition_prefix: str = ""
    ):
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        scommons = ""

        for i, s in enumerate(self.net.species):
            scommons += f"{definition_prefix}{idx_prefix}{s.fidx} = {ioff + i}\n"

        scommons += f"{definition_prefix}nspecs = {len(self.net.species)}\n"
        scommons += f"{definition_prefix}nreactions = {len(self.net.reactions)}\n"

        return scommons

    def get_rates(
        self,
        idx_offset: int = -1,
        rate_variable: str = "k",
        language: str = "python",
        use_cse: bool = True,
    ):
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        rates = ""

        # For C++ with CSE enabled, collect all rate expressions and apply CSE
        if language in ["c++", "cpp", "cxx"] and use_cse:
            # Collect all rate expressions as SymPy objects
            rate_exprs = []
            photo_indices = []
            for i, rea in enumerate(self.net.reactions):
                if type(rea.rate) is str:
                    # String rates are kept as-is (will be handled separately)
                    rate_exprs.append(None)
                elif hasattr(rea.rate, "func") and isinstance(
                    rea.rate.func, type(sp.Function("f"))
                ):
                    if rea.rate.func.__name__ == "photorates":
                        # Photorates are handled specially
                        rate_exprs.append(None)
                        photo_indices.append(i)
                    else:
                        rate_exprs.append(rea.rate)
                else:
                    rate_exprs.append(rea.rate)

            # Filter out None values for CSE
            valid_exprs = [
                (i, expr) for i, expr in enumerate(rate_exprs) if expr is not None
            ]

            if valid_exprs:
                # Apply CSE to all valid expressions
                indices, exprs = zip(*valid_exprs)
                replacements, reduced_exprs = sp.cse(exprs, optimizations="basic")

                # Prune unused CSE temporaries based on actually emitted rate expressions
                # Build the set of CSE symbols that appear in the reduced expressions
                if replacements:
                    cse_syms = [var for var, _ in replacements]
                    cse_set = set(cse_syms)
                    used = set()
                    for e in reduced_exprs:
                        used |= e.free_symbols & cse_set
                    # Propagate dependencies transitively
                    dep_map = {var: expr for var, expr in replacements}
                    changed = True
                    while changed:
                        changed = False
                        addl = set()
                        for v in list(used):
                            ev = dep_map.get(v)
                            if ev is None:
                                continue
                            deps = ev.free_symbols & cse_set
                            new_deps = deps - used
                            if new_deps:
                                addl |= new_deps
                        if addl:
                            used |= addl
                            changed = True
                    # Keep replacements in original order
                    replacements = [
                        (var, dep_map[var]) for var, _ in replacements if var in used
                    ]

                # Generate code for common subexpressions (only those actually used)
                if replacements:
                    rates += "// Common subexpressions\n"
                    for i, (var, expr) in enumerate(replacements):
                        cpp_expr = self.code_gen(expr, strict=False).replace(
                            "std::", "Kokkos::"
                        )
                        rates += f"const double {var} = {cpp_expr};\n"

                if replacements:
                    rates += "\n// Rate calculations using common subexpressions\n"

                # Generate code for reduced rate expressions
                expr_dict = dict(zip(indices, reduced_exprs))

                # Generate all rate assignments
                for i, rea in enumerate(self.net.reactions):
                    if i in expr_dict:
                        # Use CSE-optimized expression
                        cpp_code = self.code_gen(expr_dict[i], strict=False).replace(
                            "std::", "Kokkos::"
                        )
                        rates += (
                            f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {cpp_code};\n"
                        )
                    elif type(rea.rate) is str:
                        # String rate
                        rate = rea.rate
                        if rea.guess_type() == "photo":
                            rate = rate.replace("#IDX#", str(ioff + i))
                        rates += (
                            f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {rate};\n"
                        )
                    elif i in photo_indices:
                        # Photorates
                        rate = f"photorates(#IDX#, {', '.join(str(arg) for arg in rea.rate.args[1:])})"
                        rate = rate.replace("#IDX#", str(ioff + i))
                        rates += (
                            f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {rate};\n"
                        )
                    else:
                        # Fallback to regular code generation
                        rate = rea.get_cpp()
                        if rea.guess_type() == "photo":
                            rate = rate.replace("#IDX#", str(ioff + i))
                        rates += (
                            f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {rate};\n"
                        )
            else:
                # No valid expressions for CSE, use regular generation
                for i, rea in enumerate(self.net.reactions):
                    rate = rea.get_cpp()
                    if rea.guess_type() == "photo":
                        rate = rate.replace("#IDX#", str(ioff + i))
                    rates += f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {rate};\n"
        else:
            # Original behavior for non-C++ or CSE disabled
            for i, rea in enumerate(self.net.reactions):
                if language in ["python", "py"]:
                    rate = rea.get_python()
                elif language in ["fortran", "f90"]:
                    rate = rea.get_f90()
                elif language in ["c++", "cpp", "cxx"]:
                    rate = rea.get_cpp()
                else:
                    rate = rea.get_python()
                if rea.guess_type() == "photo":
                    rate = rate.replace("#IDX#", str(ioff + i))
                    rates += f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {rate}{self.line_end}\n"

        return rates

    def __prune_cse(self, repls, exprs):
        if not repls:
            return []
        _cse_syms = [v for v, _ in repls]
        _cse_set = set(_cse_syms)
        _used = set()
        for _e in exprs:
            _used |= _e.free_symbols & _cse_set
        if not _used:
            return []
        _dep_map = {v: e for v, e in repls}
        _changed = True
        while _changed:
            _changed = False
            _addl = set()
            for _v in list(_used):
                _ev = _dep_map.get(_v)
                if _ev is None:
                    continue
                _deps = _ev.free_symbols & _cse_set
                _new = _deps - _used
                if _new:
                    _addl |= _new
            if _addl:
                _used |= _addl
                _changed = True

        return [(v, _dep_map[v]) for v, _ in repls if v in _used]
