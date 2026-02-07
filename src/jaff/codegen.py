"""
Code generation module for chemical reaction network ODEs.

This module provides the Codegen class which generates language-specific code
for chemical reaction networks, including rate calculations, flux computations,
ODE right-hand sides, and analytical Jacobians with optional common subexpression
elimination (CSE).

Supported languages: C++, C, Fortran90, Python
"""

import re
from collections.abc import Callable
from functools import reduce
from itertools import product
from typing import Any, List, Tuple, TypedDict

import sympy as sp

from .network import Network


class LangModifier(TypedDict):
    """
    Type definition for language-specific code generation modifiers.

    Attributes:
        brac: Bracket style for 1D arrays (e.g., "[]" for C++, "()" for Fortran)
        assignment_op: Assignment operator (typically "=")
        line_end: Statement terminator (e.g., ";" for C++, "" for Python)
        matrix_sep: Separator for 2D array indexing (e.g., "][" for C++)
        code_gen: SymPy code generation function for the target language
        idx_offset: Array indexing offset (0 for C/C++/Python, 1 for Fortran)
        comment: Comment prefix for the language (e.g., "//" for C++)
        types: Dictionary mapping type names to language-specific declarations
        extras: Additional language-specific attributes (qualifiers, specifiers, etc.)
    """

    brac: str
    assignment_op: str
    line_end: str
    matrix_sep: str
    code_gen: Callable[..., str]
    idx_offset: int
    comment: str
    types: dict[str, str]
    extras: dict[str, Any]


class Codegen:
    """
    Multi-language code generator for chemical reaction networks.

    This class provides methods to generate optimized code for evaluating
    chemical reaction rates, fluxes, ODE right-hand sides, and analytical
    Jacobians in multiple programming languages.

    Attributes:
        net: Chemical reaction network object
        lang: Internal language identifier
        lb, rb: Left and right brackets for 1D arrays
        mlb, mrb: Left and right brackets for 2D arrays (matrices)
        matrix_sep: Separator for 2D array indices
        assignment_op: Assignment operator for the language
        line_end: Statement terminator
        code_gen: SymPy code generation callable
        ioff: Index offset (0 or 1 based on language)
        comment: Comment prefix
        types: Type declaration strings
        extras: Additional language-specific attributes
    """

    def __init__(
        self,
        network: Network,
        lang: str = "c++",
        brac_format: str = "",
        matrix_format: str = "",
        dedt: bool = False,
    ):
        """
        Initialize the code generator for a specific language and network.

        Args:
            network: Chemical reaction Network object containing species and reactions
            lang: Target programming language. Options: "c++", "cpp", "cxx", "c",
                  "fortran", "f90", "python", "py". Default: "c++"
            brac_format: Override for 1D array bracket style. Options: "()", "[]",
                        "{}", "<>". If empty, uses language default.
            matrix_format: Override for 2D array format. Options: "()", "(,)", "[]",
                          "[,]", "{}", "{,}", "<>", "<,>". If empty, uses language default.

        Raises:
            ValueError: If lang, brac_format, or matrix_format is not supported
        """
        __lang_aliases = self.__get_language_aliases()
        __lang_tokens = self.__get_language_tokens()
        __matrix_formats = self.__get_matrix_formats()
        __brack_formats = self.__get_bracket_formats()

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
        bracs: str = (
            brac_format
            if brac_format in __brack_formats
            else __lang_tokens[language]["brac"]
        )

        # Set brackets for 2D array
        mbracs: str = (
            __matrix_formats[matrix_format]["brac"]
            if matrix_format
            else __lang_tokens[language]["brac"]
        )

        # Set 2D array separator
        self.matrix_sep: str = (
            __matrix_formats[matrix_format]["sep"]
            if matrix_format
            else __lang_tokens[language]["matrix_sep"]
        )

        # Assigen other required variables
        self.assignment_op: str = __lang_tokens[language]["assignment_op"]
        self.line_end: str = __lang_tokens[language]["line_end"]
        self.code_gen: Callable[..., str] = __lang_tokens[language]["code_gen"]
        self.ioff: int = __lang_tokens[language]["idx_offset"]
        self.comment: str = __lang_tokens[language]["comment"]
        self.types: dict[str, str] = __lang_tokens[language]["types"]
        self.extras: dict[str, Any] = __lang_tokens[language]["extras"]
        self.lang = language

        # Set left and right brackets for 1D and 2D arrays
        self.lb, self.rb = bracs
        self.mlb, self.mrb = mbracs

        # Set network object
        self.net: Network = network
        self.dedt: bool = dedt
        self.sode: list[sp.Expr] = []

    def get_commons(
        self, idx_offset: int = -1, idx_prefix: str = "", definition_prefix: str = ""
    ) -> str:
        """
        Generate code for common constants (species indices, counts).

        This method generates index definitions for all species in the network,
        along with the total number of species and reactions.

        Args:
            idx_offset: Starting index for species (default: -1 uses language default)
            idx_prefix: Prefix to add before species index names (e.g., "idx_")
            definition_prefix: Prefix for definitions (e.g., "const int " for C++)

        Returns:
            String containing the generated code with species indices and counts

        Example output (C++):
            const int idx_h2 = 0;
            const int idx_co = 1;
            const int nspecs = 2;
            const int nreactions = 5;
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        scommons = ""

        for i, s in enumerate(self.net.species):
            scommons += (
                f"{definition_prefix}{idx_prefix}{s.fidx} = {ioff + i}{self.line_end}\n"
            )

        scommons += (
            f"{definition_prefix}nspecs = {len(self.net.species)}{self.line_end}\n"
        )
        scommons += (
            f"{definition_prefix}nreactions = {len(self.net.reactions)}{self.line_end}\n"
        )

        return scommons

    def get_rates(
        self,
        idx_offset: int = -1,
        rate_variable: str = "k",
        use_cse: bool = True,
        var_prefix: str = "",
    ) -> str:
        """
        Generate code for reaction rate coefficient calculations.

        This method generates code to compute all reaction rate coefficients,
        optionally applying common subexpression elimination (CSE) to optimize
        repeated calculations.

        Args:
            idx_offset: Starting index for rate array (default: -1 uses language default)
            rate_variable: Name of the rate array variable (default: "k")
            use_cse: Whether to apply common subexpression elimination (default: True)
            var_prefix: Prefix for CSE temporary variables (default: uses language default)

        Returns:
            String containing the generated rate calculation code

        Note:
            - String rates and photorates functions are excluded from CSE
            - CSE significantly reduces computation for complex rate expressions
            - Generated code includes comments separating CSE temps from final assignments
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            var_prefix
            if var_prefix
            else f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )
        rates = ""

        # Collect all rate expressions and apply CSE if enabled
        # CSE (Common Subexpression Elimination) identifies and extracts repeated
        # subexpressions to reduce redundant computations
        cse_dict: dict[int, sp.Expr | str] = {}
        if use_cse:
            # Collect all rate expressions as SymPy objects, excluding strings and photorates
            for i, rea in enumerate(self.net.reactions):
                if type(rea.rate) is str:
                    continue
                if (
                    hasattr(rea.rate, "func")
                    and isinstance(rea.rate.func, type(sp.Function("f")))
                    and rea.rate.func.__name__ == "photorates"
                ):
                    continue
                cse_dict[i] = rea.rate

            if cse_dict:
                # Apply CSE to all valid expressions
                exprs = cse_dict.values()
                replacements, reduced_exprs = sp.cse(exprs, optimizations="basic")

                # Prune unused CSE temporaries based on actually emitted rate expressions
                replacements = self.__prune_cse(replacements, reduced_exprs)

                # Generate code for common subexpressions (only those actually used)
                if replacements:
                    rates += f"{self.comment}Common subexpressions\n"

                    for i, (var, expr) in enumerate(replacements):
                        expr = self.code_gen(expr, strict=False)
                        rates += f"{prefix}{var} = {expr}{self.line_end}\n"

                    rates += (
                        f"\n{self.comment}Rate calculations using common subexpressions\n"
                    )

                for key, expr in zip(cse_dict.keys(), reduced_exprs):
                    cse_dict[key] = self.code_gen(expr)

                # Generate all rate assignments
        for i, rea in enumerate(self.net.reactions):
            rate = cse_dict[i] if cse_dict.get(i, "") else rea.get_code(self.lang)
            if rea.guess_type() == "photo":
                rate = rate.replace("#IDX#", str(ioff + i))
            rates += (
                f"{rate_variable}{self.lb}{ioff + i}{self.rb} = {rate}{self.line_end}\n"
            )

        return rates

    def get_flux_expressions(
        self,
        rate_var: str = "k",
        species_var: str = "y",
        idx_prefix: str = "",
        idx_offset: int = -1,
        flux_var: str = "flux",
    ) -> str:
        """
        Generate code for reaction flux calculations.

        This method generates code to compute reaction fluxes, which are the
        products of rate coefficients and reactant concentrations.

        Args:
            rate_var: Name of the rate coefficient array (default: "k")
            species_var: Name of the species concentration array (default: "y")
            idx_prefix: Prefix for species index names (default: "")
            idx_offset: Starting index for flux array (default: -1 uses language default)
            flux_var: Name of the flux array variable (default: "flux")

        Returns:
            String containing the generated flux calculation code

        Example output:
            flux[0] = k[0] * y[idx_h] * y[idx_o];
            flux[1] = k[1] * y[idx_co];
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        fluxes = ""

        for i, rea in enumerate(self.net.reactions):
            flux = rea.get_flux_expressions(
                idx=ioff + i,
                rate_variable=rate_var,
                species_variable=species_var,
                brackets=f"{self.lb}{self.rb}",
                idx_prefix=idx_prefix,
            )
            fluxes += f"flux{self.lb}{ioff + i}{self.rb} = {flux}{self.line_end}\n"

        return fluxes

    def get_ode_expressions(
        self,
        idx_offset: int = -1,
        flux_var: str = "flux",
        species_var: str = "y",
        idx_prefix: str = "",
        derivative_prefix: str = "d",
        derivative_var: str | None = None,
    ) -> str:
        """
        Generate code for ODE right-hand side (dy/dt).

        This method generates code for the time derivatives of all species
        concentrations by summing fluxes according to reaction stoichiometry.
        Reactants contribute negative terms, products contribute positive terms.

        Args:
            idx_offset: Starting index (default: -1 uses language default)
            flux_var: Name of the flux array (default: "flux")
            species_var: Name of the species array (default: "y")
            idx_prefix: Prefix for species index names (default: "")
            derivative_prefix: Prefix for derivative variable name (default: "d")
            derivative_var: Override name for derivative array (default: None uses
                           derivative_prefix + species_var)

        Returns:
            String containing the generated ODE code

        Example output:
            dy[idx_h2] = - flux[0] + flux[3];
            dy[idx_o] = - flux[1] + flux[2];
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        derivative_var = (
            f"{derivative_prefix}{species_var}"
            if derivative_var is None
            else derivative_var
        )

        # Build ODE expressions by accumulating flux contributions
        # Each reaction contributes to derivatives of its reactants (negative)
        # and products (positive)
        ode = {}
        for i, rea in enumerate(self.net.reactions):
            # Subtract flux for each reactant
            for rr in rea.reactants:
                rrfidx = idx_prefix + rr.fidx
                if rrfidx not in ode:
                    ode[rrfidx] = ""
                ode[rrfidx] += f" - {flux_var}{self.lb}{ioff + i}{self.rb}"
            # Add flux for each product
            for pp in rea.products:
                ppfidx = idx_prefix + pp.fidx
                if ppfidx not in ode:
                    ode[ppfidx] = ""
                ode[ppfidx] += f" + {flux_var}{self.lb}{ioff + i}{self.rb}"

        sode = ""
        for name, expr in ode.items():
            sode += f"{derivative_var}{self.lb}{name}{self.rb} = {expr}{self.line_end}\n"

        return sode

    def get_symbolic_ode_and_jacobian(
        self,
        idx_offset: int = 0,
        use_cse: bool = True,
        ode_var: str = "f",
        jac_var: str = "J",
        matrix_format: str = "",
        brac_format: str = "",
        var_prefix: str = "",
    ) -> Tuple[str, str]:
        """
        Generate symbolic ODE and analytical Jacobian with CSE optimization.

        This method uses symbolic differentiation to compute the analytical
        Jacobian matrix (df/dy) for the chemical ODE system. Common subexpression
        elimination is applied separately to ODE and Jacobian code for maximum
        efficiency.

        Args:
            idx_offset: Starting index for arrays (default: 0)
            use_cse: Apply common subexpression elimination (default: True)
            dedt_chem: Include chemical energy equation (default: False)
            ode_var: Name of ODE output array (default: "f")
            jac_var: Name of Jacobian matrix (default: "J")
            matrix_format: Override 2D array format (default: "" uses language default)
            brac_format: Override 1D array format (default: "" uses language default)
            var_prefix: Prefix for CSE variables (default: "" uses language default)

        Returns:
            Tuple of (ode_code, jacobian_code) strings containing:
                - ode_code: Right-hand side df/dt with CSE optimizations
                - jacobian_code: Analytical Jacobian df/dy with CSE optimizations

        Note:
            - The Jacobian accounts for rate coefficient dependencies on concentrations
            - CSE is pruned separately for ODE and Jacobian to avoid unused temporaries
            - Only non-zero Jacobian elements are generated
            - Symbolic variables y_i are mapped to nden[i] in generated code
        """

        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            var_prefix
            if var_prefix
            else f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )

        # Create symbolic variables representing species concentrations for Jacobian
        # We use temporary scalar symbols y_i for robust SymPy manipulation, then
        # remap names to `nden[i]` at codegen time to match templates.
        n_species = len(self.net.species)
        n_ode_eqns = n_species + int(self.dedt)
        y_syms = [sp.symbols(f"y_{i}") for i in range(n_species)]

        # Build mapping to replace any Indexed occurrences of nden[...] in rate expressions
        # with the corresponding scalar y_i symbols.
        nden_matrix = sp.MatrixSymbol("nden", n_species, 1)
        nden_to_y = {}
        for i in range(n_species):
            # Support both nden[i] and nden[Idx(i)] forms
            nden_to_y[nden_matrix[i, 0]] = y_syms[i]
            nden_to_y[nden_matrix[sp.Idx(i), 0]] = y_syms[i]

        # Precompute rate expressions with nden[...] mapped to y_i
        # This substitution allows SymPy to properly differentiate rates w.r.t. species
        k_exprs = [rea.rate.xreplace(nden_to_y) for rea in self.net.reactions]

        # Precompute specific internal energy equation if requested
        if self.dedt:
            den_tot = reduce(
                lambda x, y: x + y,
                [
                    specie.mass * nden_to_y[nden_matrix[i, 0]]
                    for i, specie in enumerate(self.net.species)
                ],
            )
            dedt_exp = (
                self.net.dEdt_chem.xreplace(nden_to_y)
                + self.net.dEdt_other.xreplace(nden_to_y)
            ) / den_tot

        # Dict to replace any remaining k[i] symbols defensively before differentiating
        subs_k = {
            sp.symbols(f"k[{i}]"): k_exprs[i] for i in range(len(self.net.reactions))
        }
        ode_symbols = [
            sode.xreplace({**nden_to_y, **subs_k}) for sode in self.net.get_sodes()
        ]

        # Append specific internal energy rate equation conditionally
        if self.dedt:
            ode_symbols.append(dedt_exp)

        # Compute the Jacobian matrix d(f)/d(y) via symbolic differentiation
        # This gives exact analytical derivatives for stiff ODE solvers
        jacobian_matrix = sp.Matrix(ode_symbols).jacobian(y_syms)

        if self.dedt:
            # Calculate internal energy derivatives and append as extra column
            dde = sp.zeros(n_ode_eqns, 1)
            dedot_dtgas = sp.diff(self.__get_sym_eos(), sp.symbols("tgas"))

            for i in range(n_ode_eqns):
                dxdot_dtgas = sp.diff(ode_symbols[i], sp.symbols("tgas"))
                dde[i, 0] = dxdot_dtgas / dedot_dtgas

            jacobian_matrix = jacobian_matrix.row_join(dde)

        ode_code: str = ""
        jac_code: str = ""

        # Apply common subexpression elimination if requested
        # CSE significantly reduces code size and computation time for large networks
        if use_cse:
            # Collect all ODE and Jacobian expressions for joint CSE analysis
            all_exprs = ode_symbols + list(jacobian_matrix)
            replacements, reduced_exprs = sp.cse(
                all_exprs, symbols=sp.numbered_symbols("cse")
            )

            # Split reduced expressions back
            ode_reduced = reduced_exprs[:n_ode_eqns]
            jac_reduced = reduced_exprs[n_ode_eqns:]

            # Build separate CSE blocks for RHS and Jacobian
            repls_ode = self.__prune_cse(replacements, ode_reduced)
            repls_jac = self.__prune_cse(replacements, jac_reduced)

            # Generate ODE code with only the needed CSE assignments
            for i, (var, expr) in enumerate(repls_ode):
                expr_str = self.code_gen(expr, allow_unknown_functions=True)

                for j in range(n_ode_eqns):
                    expr_str = re.sub(
                        rf"\by_{j}\b", f"nden{self.lb}{j}{self.rb}", expr_str
                    )
                expr_str = expr_str.replace("[", self.lb).replace("]", self.rb)
                ode_code += (
                    f"{prefix}{var} {self.assignment_op} {expr_str}{self.line_end}\n"
                )

            for i, expr in enumerate(ode_reduced):
                expr_str = self.code_gen(expr, allow_unknown_functions=True)

                for j in range(n_ode_eqns):
                    expr_str = re.sub(
                        rf"\by_{j}\b", f"nden{self.lb}{j}{self.rb}", expr_str
                    )
                expr_str = expr_str.replace("[", self.lb).replace("]", self.rb)
                ode_code += f"{ode_var}{self.lb}{ioff + i}{self.rb} {self.assignment_op} {expr_str}{self.line_end}\n"

            # Generate Jacobian code with only the needed CSE assignments
            for i, (var, expr) in enumerate(repls_jac):
                expr_str = self.code_gen(expr, allow_unknown_functions=True)

                for j in range(n_ode_eqns):
                    expr_str = re.sub(
                        rf"\by_{j}\b", f"nden{self.lb}{j}{self.rb}", expr_str
                    )
                expr_str = expr_str.replace("[", self.lb).replace("]", self.rb)
                jac_code += (
                    f"{prefix}{var} {self.assignment_op} {expr_str}{self.line_end}\n"
                )
            for i, j in product(range(n_ode_eqns), repeat=2):
                idx = i * n_ode_eqns + j
                expr = jac_reduced[idx]

                if expr == 0:
                    continue

                expr_str = self.code_gen(expr, allow_unknown_functions=True)

                for m in range(n_ode_eqns):
                    expr_str = re.sub(
                        rf"\by_{m}\b", f"nden{self.lb}{m}{self.rb}", expr_str
                    )
                expr_str = expr_str.replace("[", self.lb).replace("]", self.rb)
                jac_code += f"{jac_var}{self.lb}{ioff + i}{self.matrix_sep}{ioff + j}{self.rb} {self.assignment_op} {expr_str}{self.line_end}\n"

            return ode_code, jac_code

        # Generate ODE code without CSE
        for i, expr in enumerate(ode_symbols):
            expr_str = self.code_gen(expr, allow_unknown_functions=True)

            for j in range(n_ode_eqns):
                expr_str = re.sub(rf"\by_{j}\b", f"nden{self.lb}{j}{self.rb}", expr_str)
            expr_str = expr_str.replace("[", self.lb).replace("]", self.rb)
            ode_code += f"{ode_var}{self.lb}{ioff + i}{self.rb} {self.assignment_op} {expr_str}{self.line_end}\n"

        # Generate Jacobian code without CSE
        for i, j in product(range(n_ode_eqns), repeat=2):
            expr = jacobian_matrix[i, j]

            if expr == 0:
                continue

            expr_str = self.code_gen(expr, allow_unknown_functions=True)

            for m in range(n_ode_eqns):
                expr_str = re.sub(rf"\by_{m}\b", f"nden{self.lb}{m}{self.rb}", expr_str)
            expr_str = expr_str.replace("[", self.lb).replace("]", self.rb)
            jac_code += f"{jac_var}{self.lb}{ioff + i}{self.matrix_sep}{ioff + j}{self.rb} {self.assignment_op} {expr_str}{self.line_end}\n"

        return ode_code, jac_code

    @staticmethod
    def __prune_cse(
        replacements: List[Tuple[sp.Symbol, sp.Expr]], expressions: List[sp.Expr]
    ) -> List[Tuple[sp.Symbol, sp.Expr]]:
        """
        Prune unused CSE (common subexpression elimination) temporaries.

        This method performs transitive dependency analysis to identify which
        CSE temporary variables are actually used by the target expressions,
        removing unused temporaries that would waste memory and computation.

        Args:
            replacements: List of (symbol, expression) pairs from SymPy's CSE
            expressions: Target expressions that use the CSE symbols

        Returns:
            Filtered list of (symbol, expression) pairs containing only used CSE temps

        Algorithm:
            1. Build dependency map of CSE symbols
            2. Start with symbols directly used in target expressions
            3. Recursively add dependencies via depth-first search
            4. Return only the transitively required CSE replacements
        """
        if not replacements:
            return []

        dep_map = dict(replacements)
        cse_syms = set(dep_map.keys())

        used: set = set()

        # Depth-first search to find all transitively used CSE symbols
        # This ensures we keep CSE temps that are dependencies of dependencies
        def dfs(sym) -> None:
            """Recursively mark symbol and its dependencies as used."""
            if sym in used:
                return
            used.add(sym)

            expr = dep_map.get(sym)
            if expr is None:
                return

            for dep in expr.free_symbols & cse_syms:
                dfs(dep)

        for expr in expressions:
            for sym in expr.free_symbols & cse_syms:
                dfs(sym)

        return [(var, dep_map[var]) for var, _ in replacements if var in used]

    @staticmethod
    def __get_sym_eos(gamma=1.6666666666667):
        """
        Get symbolic equation of state for ideal gas specific internal energy.

        Computes the symbolic expression for specific internal energy using
        the ideal gas relation e = c_v * T, where c_v is the specific heat
        capacity at constant volume given by c_v = R / (gamma - 1).

        Args:
            gamma: Adiabatic index (heat capacity ratio). Default: 5/3 for monoatomic gas

        Returns:
            SymPy expression for specific internal energy as a function of tgas

        Formula:
            e = R / (gamma - 1) * tgas
        """

        from scipy.constants import R

        _R = R * 1e7  # cgs unit
        tgas = sp.symbols("tgas")

        return _R / (gamma - 1) * tgas

    @staticmethod
    def __get_language_aliases() -> dict[str, str]:
        """
        Get mapping of language name aliases to canonical identifiers.

        Returns:
            Dictionary mapping various language names/aliases to internal IDs
        """
        # Supported language inputs and their canonical names
        aliases: dict[str, str] = {
            "c++": "cxx",
            "cpp": "cxx",
            "cxx": "cxx",
            "c": "c",
            "fortran": "f90",
            "f90": "f90",
            "python": "py",
            "py": "py",
        }

        return aliases

    @staticmethod
    def __get_language_tokens() -> dict[str, LangModifier]:
        """
        Get language-specific code generation parameters.

        Returns:
            Dictionary mapping language IDs to their LangModifier configurations

        Languages:
            - cxx: C++ (0-indexed, semicolons, const/static qualifiers)
            - c: C (0-indexed, semicolons, const/static qualifiers)
            - f90: Fortran 90 (1-indexed, no semicolons, save qualifier)
            - py: Python (0-indexed, no semicolons, no type declarations)
        """
        # Language-specific modifiers: syntax, indexing, code generation
        tokens: dict[str, LangModifier] = {
            "cxx": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.cxxcode,
                "idx_offset": 0,
                "comment": "// ",
                "types": {
                    "int": "int ",
                    "float": "float ",
                    "double": "double ",
                    "bool": "bool ",
                },
                "extras": {
                    "type_qualifier": "const ",
                    "class_specifier": "static ",
                },
            },
            "c": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.ccode,
                "idx_offset": 0,
                "comment": "// ",
                "types": {
                    "int": "int ",
                    "float": "float ",
                    "double": "double ",
                    "bool": "_Bool ",
                },
                "extras": {
                    "type_qualifier": "const ",
                    "class_specifier": "static ",
                },
            },
            "f90": {
                "brac": "()",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": ")(",
                "code_gen": sp.fcode,
                "idx_offset": 1,
                "comment": "!! ",
                "types": {},
                "extras": {
                    "class_specifier": "save ",
                },
            },
            "py": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": ", ",
                "code_gen": sp.pycode,
                "idx_offset": 0,
                "comment": "# ",
                "types": {},
                "extras": {},
            },
        }

        return tokens

    @staticmethod
    def __get_matrix_formats() -> dict[str, dict[str, str]]:
        """
        Get available 2D array indexing formats.

        Returns:
            Dictionary of format names to bracket/separator specifications

        Formats:
            - "()", "[,]", etc.: Different combinations of bracket styles
            - Each specifies both the bracket characters and index separator
        """
        # 2D array formats for different matrix indexing styles
        # Allows flexibility for various APIs (e.g., A[i][j] vs A(i,j))
        formats: dict[str, dict[str, str]] = {
            "()": {"brac": "()", "sep": ")("},
            "(,)": {"brac": "()", "sep": ", "},
            "[]": {"brac": "[]", "sep": "]["},
            "[,]": {"brac": "[]", "sep": ", "},
            "{}": {"brac": "{}", "sep": "}{"},
            "{,}": {"brac": "{}", "sep": ", "},
            "<>": {"brac": "<>", "sep": "><"},
            "<,>": {"brac": "<>", "sep": ", "},
        }
        return formats

    @staticmethod
    def __get_bracket_formats() -> list[str]:
        """
        Get available 1D array bracket formats.

        Returns:
            List of valid bracket pair strings for 1D array indexing
        """
        # 1D array bracket formats: (), {}, [], <>
        formats: list[str] = ["()", "{}", "[]", "<>"]

        return formats
