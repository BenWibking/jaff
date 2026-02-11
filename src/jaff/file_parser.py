"""
Template file parser for JAFF code generation.

This module implements a sophisticated template parser that processes files containing
JAFF (Just Another File Format) directives to generate code for chemical reaction networks.
The parser supports multiple programming languages (C, C++, Fortran) and provides various
commands for iterating over network components, substituting values, and generating
complex expressions for rates, ODEs, Jacobians, and more.

Supported JAFF Commands:
    - SUB: Substitute token values (e.g., species count, network label)
    - REPEAT: Iterate over network components (reactions, species, elements)
    - GET: Retrieve specific properties for entities (species index, mass, charge)
    - HAS: Check for existence of entities in the network
    - END: Mark the end of a parsing block

Example Template Syntax:
    // $JAFF SUB nspec
    const int NUM_SPECIES = $nspec$;
    // $JAFF END

    // $JAFF REPEAT idx IN species
    species[$idx$] = "$specie$";
    // $JAFF END
"""

import re
from pathlib import Path
from typing import Any, Callable, TypedDict

from jaff import Codegen, Network
from jaff.elements import Elements


class IdxSpanResult(TypedDict):
    """
    Result structure for index span detection.

    Attributes:
        offset: List of integer offsets for each index (e.g., from $idx+2$)
        span: List of tuples containing (start, end) positions of each index token
    """

    offset: list[int]
    span: list[tuple[int, int]]


class CommandProps(TypedDict):
    """
    Properties defining a JAFF command.

    Attributes:
        func: Callable function that handles the command
        props: Dictionary mapping property names to their function handlers and metadata
    """

    func: Callable[..., Any]
    props: dict[str, dict[str, Any]]


class CseProps(TypedDict):
    """
    Common Subexpression Elimination (CSE) properties.

    Tracks state for CSE optimization when generating expressions.

    Attributes:
        parsed: Whether CSE declaration has been parsed
        prefix: Prefix string for CSE variable definitions
        var: Variable name used for CSE storage
    """

    parsed: bool
    prefix: str
    var: str


class Fileparser:
    """
    Parser for template files containing JAFF directives.

    This class processes template files line-by-line, detecting JAFF commands and
    generating appropriate code based on a chemical reaction network. It supports
    multiple programming languages and provides extensive code generation capabilities
    for reaction rates, ODEs, Jacobians, and other chemical kinetics expressions.

    Attributes:
        net: Chemical reaction network being processed
        file: Path to the template file being parsed
        elems: Elements analyzer for the network
        parsing_enabled: Whether parsing is currently active
        parse_function: Function to call for processing subsequent lines
        line: Current line being processed (stripped)
        og_line: Original line including whitespace
        modified: Accumulated output text
        indent: Indentation string for current line
        cse_props: Properties for Common Subexpression Elimination
        cg: Code generator for the target language
        parser_dict: Dictionary mapping command names to their handlers

    Example:
        >>> net = Network("networks/react_COthin")
        >>> parser = Fileparser(net, Path("template.cpp"))
        >>> output = parser.parse_file()
    """

    def __init__(self, network: Network, file: Path) -> None:
        """
        Initialize the file parser for a given network and template file.

        Args:
            network: Chemical reaction network to use for code generation
            file: Path to template file to parse

        Raises:
            RuntimeError: If the file extension is not supported
        """
        self.net = network
        self.file = file
        self.elems: Elements = Elements(self.net)
        self.parsing_enabled: bool = True
        self.parse_function: Callable[[], None] | None = None
        self.line: str = ""
        self.og_line: str = ""
        self.modified: str = ""
        self.indent: str = ""
        self.cse_props: CseProps = {"parsed": False, "prefix": "", "var": ""}

        ext: str = self.file.suffix[1:].lower()
        ext_map: dict[str, str] = {
            "cpp": "cxx",
            "cxx": "cxx",
            "cc": "cxx",
            "hpp": "cxx",
            "hxx": "cxx",
            "hh": "cxx",
            "h": "cxx",
            "c": "c",
            "f": "f90",
            "for": "f90",
            "f90": "f90",
            "f95": "f90",
            "f03": "f90",
            "f08": "f90",
        }
        if ext not in ext_map.keys():
            raise RuntimeError(f"{ext} files are not yet supprted")

        self.cg: Codegen = Codegen(network=self.net, lang=ext_map[ext])
        self.parser_dict: dict[str, CommandProps] = self.__get_parser_dict()

    def parse_file(self) -> str:
        """
        Parse the entire template file and generate code.

        Reads the template file line by line, processing JAFF directives and
        generating output based on the chemical reaction network.

        Returns:
            Generated code as a string with all JAFF directives expanded
        """
        with open(self.file, "r") as f:
            for line in f:
                self.og_line = line
                self.__parse_line(line)

        return self.modified

    def __parse_line(self, line: str) -> None:
        """
        Parse a single line and handle JAFF commands or regular content.

        Detects JAFF directives (lines starting with comment + "$JAFF") and
        either executes active parse functions or processes new commands.

        Args:
            line: Line of text to parse
        """
        comment: str = self.cg.comment
        # Extract indentation from the original line
        self.indent = line[: len(line) - len(line.lstrip(" "))]
        line = line.strip()
        self.line = line

        # Check if this is a JAFF directive line
        if not line.startswith(f"{comment}$JAFF"):
            # Not a JAFF line - either execute active parse function or copy line as-is
            if self.parsing_enabled and self.parse_function is not None:
                self.parse_function()
                return
            self.modified += self.og_line
            return

        # JAFF directive found - preserve the original line and process the command
        self.modified += self.og_line
        self.__set_parser_active()
        # Strip the JAFF prefix to extract the command
        line = line.lstrip(f"{comment}$JAFF").lstrip()
        command = line.split()[0]

        # Execute the appropriate command handler with remaining parameters
        self.__get_command_func(command)(line.lstrip(command).lstrip())

    def __set_parser_inactive(self) -> None:
        """Disable the parser to stop processing subsequent lines."""
        self.parsing_enabled = False

    def __set_parser_active(self) -> None:
        """Enable the parser to resume processing lines."""
        self.parsing_enabled = True

    def __end(self, _: str) -> None:
        """
        Handle the END command to stop parsing and reset CSE state.

        Args:
            _: Unused argument (command parameters)
        """
        self.__set_parser_inactive()
        if self.cse_props["parsed"]:
            self.cse_props["parsed"] = False
            self.cse_props["prefix"] = ""
            self.cse_props["var"] = ""

    def __sub(self, tokens: str) -> None:
        """
        Handle the SUB command for token substitution.

        Sets up the parser to substitute tokens like $nspec$, $label$, etc.
        with their actual values from the network.

        Args:
            tokens: Comma-separated list of tokens to substitute
        """
        token_list: list[str] = self.__get_stripped_tokens(tokens)
        self.parse_function = lambda: self.__substitute_tokens(token_list, "SUB")

    def __repeat(self, rest: str) -> None:
        """
        Handle the REPEAT command for iterating over network components.

        Processes syntax like "REPEAT idx, specie IN species" to iterate over
        all species, reactions, elements, etc., generating code for each item.

        Args:
            rest: Command parameters in format "vars IN property [extras]"

        Raises:
            ValueError: If IN keyword is missing or arguments are invalid
        """
        if "IN" not in rest:
            raise ValueError(f"IN keyword not found in {self.line}")

        # Parse "vars IN property [extras]" syntax
        arg: str
        arg, rest = rest.split("IN")
        props: list[str] = self.__get_stripped_tokens(rest, sep=" ")
        args: list[str] = self.__get_stripped_tokens(arg)

        # Extract property name and optional modifiers
        prop: str = props[0]
        extras: list[str] = props[1:]

        # Get property configuration from parser dictionary
        prop_dict: dict[str, Any] = self.__get_command_props("REPEAT")[prop]
        vars: list[str] = prop_dict["vars"]
        func: Callable[..., Any] = prop_dict["func"]

        # Validate that all arguments are supported for this property
        for arg in args:
            if arg not in vars:
                raise ValueError(
                    f"Unsupported argument in line {self.line}\n"
                    f"Supported arguments for {prop} are: {vars}\n"
                )
        is_itterable: bool = prop_dict["itterable"]

        # Choose appropriate repeat handler based on iterability
        if not is_itterable:
            # Non-iterable: generates code structures (rates, ODEs, Jacobian)
            self.parse_function = lambda: self.__do_non_itterative_repeat(
                args, func, extras, vars
            )
            return

        # Iterable: loops over lists (species, reactions, elements)
        self.parse_function = lambda: self.__do_itterative_repeat(
            args, func, extras, vars
        )

    def __get(self, rest: str) -> None:
        """
        Handle the GET command to retrieve specific entity properties.

        Processes syntax like "GET specie_idx FOR CO" to get the index of
        a specific species, or similar queries for mass, charge, etc.

        Args:
            rest: Command parameters in format "props FOR entity"

        Raises:
            ValueError: If FOR keyword is missing
        """
        if "FOR" not in rest:
            raise ValueError(f"FOR keyword not found in {self.line}")
        # Parse "props FOR entity" syntax
        props_str: str
        entity: str
        props_str, entity = rest.split("FOR")
        props: list[str] = [prop.strip() for prop in props_str.split(",")]
        entity = entity.strip()

        # Set up token substitution for the requested properties
        self.parse_function = lambda: self.__substitute_tokens(props, "GET", entity)

    def __has(self, rest: str) -> None:
        """
        Handle the HAS command to check entity existence.

        Checks if a species, reaction, or element exists in the network,
        returning 1 if it exists, 0 otherwise.

        Args:
            rest: Command parameters specifying entity type and name
        """
        tokens: list[str] = [token.strip() for token in rest.split()]
        identity: str = tokens[0]
        entity: str = " ".join(tokens[1:])

        self.parse_function = lambda: self.__get_truth_value(identity, entity)

    def __get_truth_value(self, identity: str, entity: str) -> None:
        """
        Get the truth value (0 or 1) for entity existence.

        Args:
            identity: Type of entity (specie, reaction, element)
            entity: Name of the entity to check
        """
        self.__substitute_tokens([identity], "HAS", entity)

    def __do_non_itterative_repeat(
        self,
        vars: list[str],
        func: Callable[..., Any],
        extras: list[str],
        expected_vars: list[str],
    ) -> None:
        """
        Execute non-iterable REPEAT commands (rates, ODEs, Jacobian, etc.).

        These commands generate multi-line output based on the network structure
        but don't iterate over lists. Used for generating rate equations, ODEs,
        and Jacobian expressions.

        Args:
            vars: Variables specified in the REPEAT command
            func: Function to call for generating output
            extras: Additional command modifiers
            expected_vars: Variables expected by the command

        Raises:
            ValueError: If required idx variable is missing
        """
        if "idx" not in vars:
            raise ValueError(f"$idx$ variable is missing in {self.line}")

        # Build keyword arguments for the generator function
        kwargs: dict[str, Any] = {"extras": extras}

        # Check if CSE (Common Subexpression Elimination) is supported and requested
        if "cse" in expected_vars:
            cse: bool = False
            if "cse" in vars:
                cse = True
            kwargs["use_cse"] = cse

        # Call the code generation function
        func(**kwargs)

    def __do_itterative_repeat(
        self,
        vars: list[str],
        func: Callable[..., Any],
        extras: list[str],
        expected_vars: list[str],
    ) -> None:
        """
        Execute iterable REPEAT commands (species, reactions, elements, etc.).

        Iterates over lists of network components and generates code for each item.
        Supports vertical mode (with indices) and horizontal mode (inline arrays).

        Args:
            vars: Variables specified in the REPEAT command
            func: Function that returns the list to iterate over
            extras: Additional command modifiers (e.g., SORT)
            expected_vars: Variables expected by the command

        Raises:
            ValueError: If variables don't match expected parameters
        """
        for var in vars:
            if var not in expected_vars:
                raise ValueError(f"Supported parameters are: {expected_vars}")

        if expected_vars[1] not in self.line:
            self.modified += self.og_line
            return

        output: str = ""
        vertical: bool = False  # Whether to use vertical (indexed) format
        sort: bool = False

        # Vertical mode: one item per line with indices
        if "idx" in vars:
            vertical = True

        # Sort modifier: alphabetically sort the output list
        if "SORT" in extras:
            sort = True

        # Get the list to iterate over
        out_list: Any = func()
        dim: int = self.__get_list_dimension(out_list)

        if sort:
            out_list.sort()

        # Vertical mode: generate separate lines for each item with indices
        if vertical:
            if "$idx" not in self.line:
                self.modified += self.og_line
                return

            # Find all $idx$ tokens in the template line
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)

            # Ensure number of index tokens matches list dimension
            if len(idx_span["span"]) != dim:
                raise ValueError(f"{self.line} must have exactly {dim} idx")

            # 1D list: single index substitution
            if dim == 1:
                # Extract index offset and position
                ioff: int = idx_span["offset"][0]
                idx_begin: int
                idx_end: int
                idx_begin, idx_end = idx_span["span"][0]

                # Generate one line per item
                for i, val in enumerate(out_list):
                    line: str = self.line
                    # Replace $idx$ with actual index
                    line = line[:idx_begin] + str(i + ioff) + line[idx_end:]
                    # Replace value token (e.g., $specie$) with actual value
                    line = line.replace(f"${expected_vars[1]}$", str(val))

                    output += self.indent + f"{line}\n"

            # 2D list: nested index substitution
            if dim == 2:
                ioff1: int
                ioff2: int
                ioff1, ioff2 = idx_span["offset"][0], idx_span["offset"][1]
                idx1_begin: int
                idx1_end: int
                idx2_begin: int
                idx2_end: int
                idx1_begin, idx1_end = idx_span["span"][0]
                idx2_begin, idx2_end = idx_span["span"][1]
                # Iterate over 2D structure
                for i, items in enumerate(out_list):
                    for j, item in enumerate(items):
                        line = self.line
                        # Sort replacements in reverse order to avoid index shifting
                        replacements: list[tuple[int, int, str]] = sorted(
                            [
                                (idx1_begin, idx1_end, str(i + ioff1)),
                                (idx2_begin, idx2_end, str(j + ioff2)),
                            ],
                            reverse=True,
                        )

                        # Apply index replacements from right to left
                        begin: int
                        end: int
                        val: str
                        for begin, end, val in replacements:
                            line = line[:begin] + val + line[end:]
                        # Replace value token with actual item
                        line = line.replace(f"${expected_vars[1]}$", str(item))

                        output += self.indent + f"{line}\n"

            self.modified += output
            return

        # Horizontal mode: generate inline array/list
        pattern: re.Pattern[str] = re.compile(
            rf"""
            ([\(\{{<\[])
            \s*
            (["']?)
            \${expected_vars[1]}\$
            \2
            ([,\;\:\s]*)
            \s*
            ([\)\}}>\]])
            """,
            re.VERBOSE,
        )
        # Try to find array/list pattern in the line
        match: re.Match[str] | None = pattern.search(self.line)

        if not match:
            # No pattern found, copy line as-is
            self.modified += self.og_line
            return

        # Extract bracket/delimiter characters and separator
        lb: str = match.group(1)  # Left bracket
        rb: str = match.group(4)  # Right bracket
        quote: str = match.group(2)  # Quote character (if any)
        sep: str = match.group(3) if match.group(3) else ", "  # Separator
        begin, end = match.span()
        line = self.line
        items: str = ""

        # 1D list: generate flat array
        if dim == 1:
            items = lb + sep.join([f"{quote}{item}{quote}" for item in out_list]) + rb

        # 2D list: generate nested array structure
        if dim == 2:
            # Build nested structure
            for i, inner_items in enumerate(out_list):
                # Create inner array
                inner_item = (
                    lb + sep.join([f"{quote}{item}{quote}" for item in inner_items]) + rb
                )

                # Add separator between inner arrays (but not after the last one)
                items += (
                    f"{inner_item}{sep}" if i != len(out_list) - 1 else f"{inner_item}"
                )

            # Wrap in outer brackets
            items = f"{lb}{items}{rb}"

        # Replace the matched pattern with the generated items
        line = line[:begin] + items + line[end:]

        self.modified += self.indent + line + "\n"

    def __get_list_dimension(self, items: Any) -> int:
        """
        Recursively determine the dimensionality of a list.

        Args:
            items: List or nested list structure to analyze

        Returns:
            Dimension count (1 for flat list, 2 for list of lists, etc.)
        """
        dim: int = 0
        if isinstance(items, list):
            # Recursively check first element if list is not empty
            if items:
                dim = self.__get_list_dimension(items[0])
            # Add 1 for this level
            dim += 1

        return dim

    def __substitute_tokens(self, tokens: list[str], command: str, *args: Any) -> None:
        """
        Substitute tokens in the current line with their values.

        Replaces tokens like $nspec$, $label$, $specie_idx$ with actual values
        from the network. Supports arithmetic operations like $nspec+1$.

        Args:
            tokens: List of token names to substitute
            command: Command type (SUB, GET, HAS) to determine value source
            *args: Additional arguments passed to token value functions
        """
        pattern_str: str = "|".join(re.escape(token) for token in tokens)
        # Compile regex to match tokens with optional arithmetic (e.g., $nspec+1$)
        pattern: re.Pattern[str] = re.compile(
            rf"\$(?:{pattern_str})(\s*[+*-/]\s*\d+)?\s*\$"
        )

        def repl(match: re.Match[str]) -> str:
            """Replace a single token match with its value."""
            full_match: str = match.group(0)
            op_num: str | None = match.group(1)  # Optional arithmetic operation

            # Extract base token name (without $ and arithmetic)
            base: str = full_match[1:-1]
            if op_num:
                base = base[: -len(op_num)].strip()

            # Get the value for this token
            token_val: Any = self.__get_command_props(command)[base]["func"](*args)

            # Apply arithmetic if present and value is numeric
            if op_num and isinstance(token_val, int):
                return str(eval(f"{token_val} {op_num}"))

            return str(token_val)

        # Perform all token substitutions in the line
        line: str = pattern.sub(repl, self.line)
        self.modified += self.indent + line + "\n"

    def __get_command_props(self, command: str) -> dict[str, dict[str, Any]]:
        """Get properties dictionary for a specific command."""
        return self.parser_dict[command]["props"]

    def __get_command_func(self, command: str) -> Callable[..., Any]:
        """Get the handler function for a specific command."""
        return self.parser_dict[command]["func"]

    def __get_rates(self, use_cse: bool, **kwargs: Any) -> None:
        """
        Generate reaction rate expressions.

        Creates code to compute reaction rates, optionally using Common
        Subexpression Elimination (CSE) for optimization.

        Args:
            use_cse: Whether to use CSE optimization
            **kwargs: Additional keyword arguments
        """
        if "$idx" not in self.line:
            self.modified += self.og_line
            return

        var_prefix: str = self.cse_props["prefix"]
        cse_var: str = self.cse_props["var"]
        # Handle CSE (Common Subexpression Elimination) declaration line
        if use_cse and not self.cse_props["parsed"] and "$cse$" in self.line:
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 cse")

            # Extract CSE variable name and prefix from the declaration
            idx_begin: int
            idx_begin, _ = idx_span["span"][0]
            cse_var = self.line[:idx_begin].split()[-1]
            cse_var_idx: int = self.line.find(cse_var)
            var_prefix = self.line[:cse_var_idx]

            # Store CSE configuration for subsequent lines
            self.cse_props["parsed"] = True
            self.cse_props["var"] = cse_var
            self.cse_props["prefix"] = var_prefix

            return

        # Generate rate expressions
        if "$rate$" in self.line:
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)
            rate_span: tuple[int, int] = self.__find_word_span(self.line, "$rate$")

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 idx")

            idx_begin, idx_end = idx_span["span"][0]
            rate_begin: int
            rate_end: int
            rate_begin, rate_end = rate_span

            # Extract formatting information from template line
            ioff: int = idx_span["offset"][0]  # Index offset
            lb: str = self.line[idx_begin - 1]  # Left bracket
            rb: str = self.line[idx_end]  # Right bracket
            assign_op: str = self.line[idx_end + 1 : rate_begin]  # Assignment operator
            rate_var: str = self.line[: idx_begin - 1].split()[-1]  # Variable name
            line_end: str = self.line[rate_end:]  # Text after $rate$

            self.modified += (
                self.indent
                + self.cg.get_rates(
                    ioff,
                    rate_var,
                    f"{lb}{rb}",
                    use_cse,
                    cse_var,
                    var_prefix,
                    assign_op,
                    line_end,
                ).replace("\n", f"\n{self.indent}")
                + "\n"
            )

    def __get_odes(self, use_cse: bool, **kwargs: Any) -> None:
        """
        Generate ODE (ordinary differential equation) expressions.

        Creates code to compute time derivatives of species concentrations,
        optionally using CSE optimization.

        Args:
            use_cse: Whether to use CSE optimization
            **kwargs: Additional keyword arguments
        """
        if "$idx" not in self.line:
            self.modified += self.og_line
            return

        var_prefix: str = self.cse_props["prefix"]
        cse_var: str = self.cse_props["var"]
        if use_cse and not self.cse_props["parsed"] and "$cse$" in self.line:
            idx_span = self.__find_idx_span(self.line)

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 cse")

            idx_begin: int
            idx_begin, _ = idx_span["span"][0]
            cse_var = self.line[:idx_begin].split()[-1]
            cse_var_idx: int = self.line.find(cse_var)
            var_prefix = self.line[:cse_var_idx]

            self.cse_props["parsed"] = True
            self.cse_props["var"] = cse_var
            self.cse_props["prefix"] = var_prefix

            return

        if "$ode$" in self.line:
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)
            ode_span: tuple[int, int] = self.__find_word_span(self.line, "$ode$")

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 idx")

            idx_begin, idx_end = idx_span["span"][0]
            ode_begin: int
            ode_end: int
            ode_begin, ode_end = ode_span

            ioff: int = idx_span["offset"][0]
            lb: str = self.line[idx_begin - 1]
            rb: str = self.line[idx_end]
            assign_op: str = self.line[idx_end + 1 : ode_begin]
            ode_var: str = self.line[: idx_begin - 1].split()[-1]
            line_end: str = self.line[ode_end:]

            self.modified += (
                self.indent
                + self.cg.get_ode(
                    idx_offset=ioff,
                    ode_var=ode_var,
                    brac_format=f"{lb}{rb}",
                    use_cse=use_cse,
                    cse_var=cse_var,
                    def_prefix=var_prefix,
                    assignment_op=assign_op,
                    line_end=line_end,
                ).replace("\n", f"\n{self.indent}")
                + "\n"
            )

    def __get_rhses(self, use_cse: bool, **kwargs: Any) -> None:
        """
        Generate right-hand side (RHS) expressions for ODEs.

        Similar to __get_odes but may have different formatting or use cases.

        Args:
            use_cse: Whether to use CSE optimization
            **kwargs: Additional keyword arguments
        """
        if "$idx" not in self.line:
            self.modified += self.og_line
            return

        var_prefix: str = self.cse_props["prefix"]
        cse_var: str = self.cse_props["var"]
        if use_cse and not self.cse_props["parsed"] and "$cse$" in self.line:
            idx_span = self.__find_idx_span(self.line)

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 cse")

            idx_begin: int
            idx_begin, _ = idx_span["span"][0]
            cse_var = self.line[:idx_begin].split()[-1]
            cse_var_idx: int = self.line.find(cse_var)
            var_prefix = self.line[:cse_var_idx]

            self.cse_props["parsed"] = True
            self.cse_props["var"] = cse_var
            self.cse_props["prefix"] = var_prefix

            return

        if "$rhs$" in self.line:
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)
            rhs_span: tuple[int, int] = self.__find_word_span(self.line, "$rhs$")

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 idx")

            idx_begin, idx_end = idx_span["span"][0]
            rhs_begin: int
            rhs_end: int
            rhs_begin, rhs_end = rhs_span

            ioff: int = idx_span["offset"][0]
            lb: str = self.line[idx_begin - 1]
            rb: str = self.line[idx_end]
            assign_op: str = self.line[idx_end + 1 : rhs_begin]
            rhs_var: str = self.line[: idx_begin - 1].split()[-1]
            line_end: str = self.line[rhs_end:]

            self.modified += (
                self.indent
                + self.cg.get_rhs(
                    idx_offset=ioff,
                    ode_var=rhs_var,
                    brac_format=f"{lb}{rb}",
                    use_cse=use_cse,
                    cse_var=cse_var,
                    def_prefix=var_prefix,
                    assignment_op=assign_op,
                    line_end=line_end,
                ).replace("\n", f"\n{self.indent}")
                + "\n"
            )

    def __get_jacobian(self, use_cse: bool, extras: list[str], **kwargs: Any) -> None:
        """
        Generate analytical Jacobian matrix expressions.

        Creates code to compute the Jacobian matrix (partial derivatives of
        species rates with respect to species concentrations).

        Args:
            use_cse: Whether to use CSE optimization
            extras: Additional modifiers (e.g., DEDT for time derivatives)
            **kwargs: Additional keyword arguments
        """
        if "$idx" not in self.line:
            self.modified += self.og_line
            return

        use_dedt: bool = False
        if extras and "DEDT" in extras:
            dedt: str = extras[extras.index("DEDT") + 1]
            if dedt not in ["TRUE", "FALSE"]:
                raise ValueError("Invalid value for DEDT")

            use_dedt = True if dedt == "TRUE" else False

        var_prefix: str = self.cse_props["prefix"]
        cse_var: str = self.cse_props["var"]
        if use_cse and not self.cse_props["parsed"] and "$cse$" in self.line:
            idx_span = self.__find_idx_span(self.line)

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 cse")

            idx_begin: int
            idx_begin, _ = idx_span["span"][0]
            cse_var = self.line[:idx_begin].split()[-1]
            cse_var_idx: int = self.line.find(cse_var)
            var_prefix = self.line[:cse_var_idx]

            self.cse_props["parsed"] = True
            self.cse_props["var"] = cse_var
            self.cse_props["prefix"] = var_prefix

            return

        if "$expr$" in self.line:
            idx_span = self.__find_idx_span(self.line)
            expr_span: tuple[int, int] = self.__find_word_span(self.line, "$expr$")

            if len(idx_span["span"]) != 2:
                raise ValueError(f"{self.line} must have exactly 2 idx")

            idx1_begin: int
            idx1_end: int
            idx2_begin: int
            idx2_end: int
            idx1_begin, idx1_end = idx_span["span"][0]
            idx2_begin, idx2_end = idx_span["span"][1]
            expr_begin: int
            expr_end: int
            expr_begin, expr_end = expr_span

            if idx_span["offset"][0] != idx_span["offset"][1]:
                raise ValueError(f"Both index offsets in {self.line} must be same")

            ioff: int = idx_span["offset"][0]
            lb: str = self.line[idx1_begin - 1]
            rb: str = self.line[idx2_end]
            sep: str = self.line[idx1_end:idx2_begin]
            assign_op: str = self.line[idx2_end + 1 : expr_begin]
            jac_var: str = self.line[: idx1_begin - 1].split()[-1]
            line_end: str = self.line[expr_end:]

            self.modified += (
                self.indent
                + self.cg.get_jacobian(
                    use_dedt=use_dedt,
                    idx_offset=ioff,
                    jac_var=jac_var,
                    matrix_format=f"{lb}{sep.strip()}{rb}",
                    use_cse=use_cse,
                    cse_var=cse_var,
                    var_prefix=var_prefix,
                    assignment_op=assign_op,
                    line_end=line_end,
                ).replace("\n", f"\n{self.indent}")
                + "\n"
            )

    def __get_flux_expressions(self, **kwargs: Any) -> None:
        """
        Generate flux expressions for reactions.

        Creates code to compute reaction fluxes (forward and reverse rates).

        Args:
            **kwargs: Additional keyword arguments
        """
        if "$idx" not in self.line:
            self.modified += self.og_line
            return

        if "$flux_expression$" in self.line:
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)
            flux_span: tuple[int, int] = self.__find_word_span(
                self.line, "$flux_expression$"
            )

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 idx")

            idx_begin: int
            idx_end: int
            idx_begin, idx_end = idx_span["span"][0]
            rate_begin: int
            rate_end: int
            rate_begin, rate_end = flux_span

            ioff: int = idx_span["offset"][0]
            lb: str = self.line[idx_begin - 1]
            rb: str = self.line[idx_end]
            assign_op: str = self.line[idx_end + 1 : rate_begin]
            flux_var: str = self.line[: idx_begin - 1].split()[-1]
            line_end: str = self.line[rate_end:]

            self.modified += (
                self.indent
                + self.cg.get_flux_expressions(
                    idx_offset=ioff,
                    brac_format=f"{lb}{rb}",
                    flux_var=flux_var,
                    assignment_op=assign_op,
                    line_end=line_end,
                ).replace("\n", f"\n{self.indent}")
                + "\n"
            )

    def __get_ode_expressions(self, **kwargs: Any) -> None:
        """
        Generate ODE expression code.

        Creates symbolic or numerical expressions for ODE evaluation.

        Args:
            **kwargs: Additional keyword arguments
        """
        if "$idx" not in self.line:
            self.modified += self.og_line
            return

        if "$ode_expression$" in self.line:
            idx_span: IdxSpanResult = self.__find_idx_span(self.line)
            ode_span: tuple[int, int] = self.__find_word_span(
                self.line, "$ode_expression$"
            )

            if len(idx_span["span"]) != 1:
                raise ValueError(f"{self.line} must have exactly 1 idx")

            idx_begin: int
            idx_end: int
            idx_begin, idx_end = idx_span["span"][0]
            rate_begin: int
            rate_end: int
            rate_begin, rate_end = ode_span

            ioff: int = idx_span["offset"][0]
            lb: str = self.line[idx_begin - 1]
            rb: str = self.line[idx_end]
            assign_op: str = self.line[idx_end + 1 : rate_begin]
            derivative_var: str = self.line[: idx_begin - 1].split()[-1]
            line_end: str = self.line[rate_end:]

            self.modified += (
                self.indent
                + self.cg.get_ode_expressions(
                    idx_offset=ioff,
                    brac_format=f"{lb}{rb}",
                    derivative_var=derivative_var,
                    assignment_op=assign_op,
                    line_end=line_end,
                ).replace("\n", f"\n{self.indent}")
                + "\n"
            )

    @staticmethod
    def __find_idx_span(text: str) -> IdxSpanResult:
        """
        Find all index tokens ($idx$, $idx+1$, etc.) in text.

        Locates index placeholders and extracts their positions and offsets.

        Args:
            text: Text to search for index tokens

        Returns:
            Dictionary with 'offset' list (integer offsets) and 'span' list
            (start/end positions of each token)
        """
        # Match $idx$ or $idx+N$ patterns
        idx_regex: re.Pattern[str] = re.compile(r"\$idx([+]\d+)?\$")
        result: IdxSpanResult = {"offset": [], "span": []}

        # Find all matches and extract offsets and positions
        for m in idx_regex.finditer(text):
            # Parse offset value (e.g., +2 from $idx+2$), default to 0
            result["offset"].append(int(m.group(1)) if m.group(1) else 0)
            # Store the (start, end) position of this match
            result["span"].append(m.span())

        return result

    @staticmethod
    def __find_word_span(text: str, word: str) -> tuple[int, int]:
        """
        Find the start and end positions of a word in text.

        Args:
            text: Text to search
            word: Word to find

        Returns:
            Tuple of (start_position, end_position)
        """
        begin: int = text.find(word)
        end: int = begin + len(word)

        return begin, end

    @staticmethod
    def __get_stripped_tokens(tokens: str, sep: str = ",") -> list[str]:
        """
        Split a string into tokens and strip whitespace from each.

        Args:
            tokens: String to split
            sep: Separator character (default: comma)

        Returns:
            List of stripped token strings
        """
        return [token.strip() for token in tokens.strip().split(sep)]

    def __get_parser_dict(self) -> dict[str, CommandProps]:
        """
        Build the complete parser command dictionary.

        Creates a dictionary mapping command names (SUB, REPEAT, GET, HAS, END)
        to their handler functions and property definitions. This defines all
        available JAFF directives and their behaviors.

        Returns:
            Dictionary mapping command names to CommandProps structures
        """
        cg: Codegen = self.cg

        # Define all available JAFF commands and their properties
        commands: dict[str, CommandProps] = {
            # SUB command: substitute simple tokens with values
            "SUB": {
                "func": self.__sub,
                "props": {
                    "nspec": {"func": lambda: len(self.net.species)},
                    "nelem": {"func": lambda: self.elems.nelems},
                    "nreact": {"func": lambda: len(self.net.reactions)},
                    "label": {"func": lambda: self.net.label},
                    "filename": {"func": lambda: self.file.name},
                    "filepath": {"func": lambda: self.file},
                    "dedt": {"func": cg.get_dedt},
                    "e_idx": {"func": lambda: self.net.species_dict["e-"]},
                },
            },
            # REPEAT command: iterate over network components or generate expressions
            "REPEAT": {
                "func": self.__repeat,
                "props": {
                    # Non-iterable properties: generate code structures
                    "rates": {
                        "iterable": False,
                        "func": self.__get_rates,
                        "vars": ["idx", "rate", "cse"],
                    },
                    "flux_expressions": {
                        "iterable": False,
                        "func": self.__get_flux_expressions,
                        "vars": ["idx", "flux_expression"],
                    },
                    "ode_expressions": {
                        "iterable": False,
                        "func": self.__get_ode_expressions,
                        "vars": ["idx", "ode_expression"],
                    },
                    "odes": {
                        "iterable": False,
                        "func": self.__get_odes,
                        "vars": ["idx", "ode", "cse"],
                    },
                    "rhses": {
                        "iterable": False,
                        "func": self.__get_rhses,
                        "vars": ["idx", "rhs", "cse"],
                    },
                    "jacobian": {
                        "iterable": False,
                        "func": self.__get_jacobian,
                        "vars": ["idx", "expr", "cse"],
                    },
                    # Iterable properties: loop over lists
                    "reactions": {
                        "iterable": True,
                        "func": lambda: self.net.reactions,
                        "vars": ["idx", "reaction"],
                    },
                    "species": {
                        "iterable": True,
                        "func": lambda: [specie.name for specie in self.net.species],
                        "vars": ["idx", "specie"],
                    },
                    "species_with_normalized_sign": {
                        "iterable": True,
                        "func": lambda: [
                            specie.name.replace("+", "p").replace("-", "n")
                            for specie in self.net.species
                        ],
                        "vars": ["idx", "specie"],
                    },
                    "elements": {
                        "iterable": True,
                        "func": lambda: self.elems.elements,
                        "vars": ["idx", "element"],
                    },
                    "masses": {
                        "iterable": True,
                        "func": lambda: [specie.mass for specie in self.net.species],
                        "vars": ["idx", "mass"],
                    },
                    "reactants": {
                        "iterable": True,
                        "func": lambda: [
                            reaction.reactants for reaction in self.net.reactions
                        ],
                        "vars": ["idx", "reactant"],
                    },
                    "products": {
                        "iterable": True,
                        "func": lambda: [
                            reaction.products for reaction in self.net.reactions
                        ],
                        "vars": ["idx", "product"],
                    },
                    "photo_reactions": {
                        "iterable": True,
                        "func": lambda: [
                            reaction
                            for reaction in self.net.reactions
                            if reaction.guess_type() == "photo"
                        ],
                        "vars": ["idx", "photo_reaction"],
                    },
                    "photo_reaction_truth_values": {
                        "iterable": True,
                        "func": lambda: [
                            int(reaction.guess_type() == "photo")
                            for reaction in self.net.reactions
                        ],
                        "vars": ["idx", "photo_reaction_truth_value"],
                    },
                    "photo_reaction_indices": {
                        "iterable": True,
                        "func": lambda: [
                            i
                            for i, reaction in enumerate(self.net.reactions)
                            if reaction.guess_type() == "photo"
                        ],
                        "vars": ["idx", "photo_reaction_index"],
                    },
                    "charges": {
                        "iterable": True,
                        "func": lambda: [specie.charge for specie in self.net.species],
                        "vars": ["idx", "charge"],
                    },
                    "uncharged_species": {
                        "iterable": True,
                        "func": lambda: [
                            specie for specie in self.net.species if specie.charge == 0
                        ],
                        "vars": ["idx", "uncharged_specie"],
                    },
                    "charged_species": {
                        "iterable": True,
                        "func": lambda: [
                            specie for specie in self.net.species if specie.charge != 0
                        ],
                        "vars": ["idx", "charged_specie"],
                    },
                    "tmins": {
                        "iterable": True,
                        "func": lambda: [
                            reaction.tmin for reaction in self.net.reactions
                        ],
                        "vars": ["idx", "tmin"],
                    },
                    "tmaxes": {
                        "iterable": True,
                        "func": lambda: [
                            reaction.tmax for reaction in self.net.reactions
                        ],
                        "vars": ["idx", "tmax"],
                    },
                    "element_density_matrix": {
                        "iterable": True,
                        "func": self.elems.get_element_density_matrix,
                        "vars": ["idx", "element"],
                    },
                    "element_truth_matrix": {
                        "iterable": True,
                        "func": self.elems.get_element_truth_matrix,
                        "vars": ["idx", "element"],
                    },
                    "non_zero_charge_indices": {
                        "iterable": True,
                        "func": lambda: [
                            i
                            for i, specie in enumerate(self.net.species)
                            if specie.charge != 0
                        ],
                        "vars": ["idx", "non_zero_charge_index"],
                    },
                    "zero_charge_indices": {
                        "iterable": True,
                        "func": lambda: [
                            i
                            for i, specie in enumerate(self.net.species)
                            if specie.charge == 0
                        ],
                        "vars": ["idx", "zero_charge_index"],
                    },
                    "charge_truth_values": {
                        "iterable": True,
                        "func": lambda: [
                            int(bool(specie.charge)) for specie in self.net.species
                        ],
                        "vars": ["idx", "charge_truth_value"],
                    },
                },
            },
            # GET command: retrieve specific property values
            "GET": {
                "func": self.__get,
                "props": {
                    "element_idx": {"func": lambda e: self.elems.elements.index(e)},
                    "specie_idx": {"func": lambda s: self.net.species_dict[s]},
                    "reaction_idx": {"func": lambda r: self.net.reactions_dict[r]},
                    "specie_mass": {
                        "func": lambda s: self.net.species[self.net.species_dict[s]].mass
                    },
                    "specie_charge": {
                        "func": lambda s: self.net.species[
                            self.net.species_dict[s]
                        ].charge
                    },
                    "specie_latex": {
                        "func": lambda s: self.net.species[self.net.species_dict[s]].latex
                    },
                    "reaction_tmin": {
                        "func": lambda r: self.net.reactions[
                            self.net.reactions_dict[r]
                        ].tmin
                    },
                    "reaction_tmax": {
                        "func": lambda r: self.net.reactions[
                            self.net.reactions_dict[r]
                        ].tmax
                    },
                    "reaction_verbatim": {
                        "func": lambda r: self.net.reactions[
                            self.net.reactions_dict[r]
                        ].verbatim
                    },
                },
            },
            # HAS command: check entity existence (returns 1 or 0)
            "HAS": {
                "func": self.__has,
                "props": {
                    "specie": {"func": lambda s: int(s in self.net.species_dict.keys())},
                    "reaction": {
                        "func": lambda r: int(r in self.net.reactions_dict.keys())
                    },
                    "element": {"func": lambda e: int(e in self.elems.elements)},
                },
            },
            # END command: stop parsing and reset state
            "END": {"func": self.__end, "props": {}},
        }

        return commands
