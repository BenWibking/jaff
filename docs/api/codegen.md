# Codegen API Reference

The `Codegen` class generates optimized code for chemical reaction networks in multiple programming languages.

## Overview

The `Codegen` class provides methods to generate code for:

- **Rate coefficient calculations** - Compute reaction rates
- **Flux expressions** - Calculate reaction fluxes
- **ODE systems** - Time derivatives of species concentrations
- **Jacobian matrices** - Partial derivatives for implicit solvers
- **Common constants** - Species indices and network metadata

Code generation uses SymPy for symbolic manipulation and applies optimizations like Common Subexpression Elimination (CSE) to improve performance.

```python
from jaff import Network, Codegen

# Load network
net = Network("networks/react_COthin")

# Create code generator
cg = Codegen(network=net, lang="c++")

# Generate code
rates = cg.get_rates_str(use_cse=True)
odes = cg.get_ode_str(use_cse=True)
jac = cg.get_jacobian_str(use_cse=True)
```

## Type Definitions

The `codegen` module uses TypedDict classes to provide structured, type-safe return values.

### ExtrasDict

```python
class ExtrasDict(TypedDict):
    """Container for extra data in IndexedReturn."""
    cse: IndexedList
```

Dictionary containing additional data alongside main expressions.

**Attributes**:

- `cse` (IndexedList): List of Common Subexpression Elimination (CSE) temporary variables
    - Contains `IndexedValue` objects representing CSE variable assignments
    - Example: `IndexedValue([0], "sqrt(tgas)")`

---

### IndexedReturn

```python
class IndexedReturn(TypedDict):
    """Structured return value for indexed code generation methods."""
    extras: ExtrasDict
    expressions: IndexedList
```

Return structure for methods that generate indexed expressions with optional CSE optimization.

**Attributes**:

- `extras` (ExtrasDict): Dictionary containing CSE temporaries and other auxiliary data
    - `extras["cse"]`: IndexedList of CSE temporary variable expressions
- `expressions` (IndexedList): List of main expressions
    - Contains `IndexedValue` objects for the primary output (rates, ODEs, Jacobian elements, etc.)

**Methods Returning IndexedReturn**:

- `get_indexed_rates()` - Rate coefficient expressions
- `get_indexed_odes()` - ODE right-hand side expressions
- `get_indexed_rhs()` - RHS expressions (alias for ODEs)
- `get_indexed_jacobian()` - Jacobian matrix elements

**Example**:

```python
from jaff import Network, Codegen
from jaff.codegen import IndexedReturn
from jaff.jaff_types import IndexedList

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="cxx")

# Get indexed rates with type annotation
result: IndexedReturn = cg.get_indexed_rates(use_cse=True, cse_var="cse")

# Access CSE temporaries
cse_list: IndexedList = result["extras"]["cse"]
for iv in cse_list:
    print(f"cse[{iv.indices[0]}] = {iv.value}")
# Output: cse[0] = sqrt(tgas)
#         cse[1] = exp(-100/tgas)

# Access rate expressions
rate_list: IndexedList = result["expressions"]
for iv in rate_list:
    print(f"k[{iv.indices[0]}] = {iv.value}")
# Output: k[0] = 1.2e-10 * cse[0]
#         k[1] = 3.4e-11 * cse[1]
```

---

### LangModifier

```python
class LangModifier(TypedDict):
    """Language-specific code generation configuration."""
    brac: str
    assignment_op: str
    line_end: str
    matrix_sep: str
    code_gen: Callable[..., str]
    idx_offset: int
    comment: str
    types: dict[str, str]
    extras: dict[str, Any]
```

Type definition for language-specific code generation modifiers and settings.

**Attributes**:

- `brac` (str): Bracket style for 1D arrays
    - C/C++: `"[]"`
    - Fortran: `"()"`
- `assignment_op` (str): Assignment operator (typically `"="`)
- `line_end` (str): Statement terminator
    - C/C++: `";"`
    - Python/Fortran: `""`
- `matrix_sep` (str): Separator for 2D array indexing
    - C/C++: `"]["` (for `array[i][j]`)
    - Fortran: `", "` (for `array(i, j)`)
- `code_gen` (Callable): SymPy code generation function for the target language
- `idx_offset` (int): Array indexing offset
    - C/C++/Python: `0`
    - Fortran: `1`
- `comment` (str): Comment prefix
    - C/C++: `"//"`
    - Fortran: `"!!"`
    - Python: `"#"`
- `types` (dict[str, str]): Language-specific type declarations
    - Example: `{"double": "double", "int": "int"}` for C++
- `extras` (dict[str, Any]): Additional language-specific attributes
    - Qualifiers, specifiers, and other language features

**Usage**:

This structure is used internally by `Codegen` to maintain language-specific settings.

---

## Class Reference

<!-- ::: jaff.codegen.Codegen
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get_commons
        - get_rates_str
        - get_flux_expressions_str
        - get_ode_expressions_str
        - get_ode_str
        - get_jacobian_str
        - get_dedt
-->

```python
class Codegen:
    """
    Code generator for chemical reaction networks.

    Attributes:
        net (Network): Chemical reaction network
        lang (str): Target programming language
        code_gen: SymPy code generation function
        lb, rb (str): Array brackets
        mlb, mrb (str): Matrix brackets
        matrix_sep (str): Matrix index separator
        assignment_op (str): Assignment operator
        line_end (str): Statement terminator
    """
```

## Constructor

### `Codegen(network, lang="c++", brac_format="", matrix_format="")`

Create a code generator for a specific language and network.

**Parameters:**

- `network` (Network): Chemical reaction network object
- `lang` (str): Target programming language. Default: "c++"
    - `"c++"`, `"cpp"`, `"cxx"` → C++
    - `"c"` → C
    - `"fortran"`, `"f90"` → Fortran 90
    - `"python"`, `"py"` → Python
    - `"rust"`, `"rs"` → Rust
    - `"julia"`, `"jl"` → Julia
    - `"r"` → R
- `brac_format` (str): Override 1D array bracket style. Default: "" (use language default)
    - Options: `"()"`, `"[]"`, `"{}"`, `"<>"`
- `matrix_format` (str): Override 2D array format. Default: "" (use language default)
    - Options: `"()"`, `"(,)"`, `"[]"`, `"[,]"`, `"{}"`, `"{,}"`, `"<>"`, `"<,>"`

**Returns:**

- `Codegen`: Initialized code generator

**Raises:**

- `ValueError`: If language, bracket format, or matrix format is not supported

**Example:**

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")

# C++ (default)
cg_cpp = Codegen(network=net, lang="c++")

# Fortran
cg_f90 = Codegen(network=net, lang="f90")

# Python with custom brackets
cg_py = Codegen(network=net, lang="python", brac_format="[]")

# C with 2D comma-separated indexing
cg_c = Codegen(network=net, lang="c", matrix_format="[,]")
```

## Attributes

| Attribute       | Type             | Description                                                                  |
| --------------- | ---------------- | ---------------------------------------------------------------------------- |
| `net`           | `Network`        | Chemical reaction network object                                             |
| `lang`          | `str`            | Internal language identifier ('cxx', 'c', 'f90', 'py', 'rust', 'julia', 'r') |
| `lb`            | `str`            | Left bracket for 1D arrays (e.g., '[', '(')                                  |
| `rb`            | `str`            | Right bracket for 1D arrays (e.g., ']', ')')                                 |
| `mlb`           | `str`            | Left bracket for 2D arrays                                                   |
| `mrb`           | `str`            | Right bracket for 2D arrays                                                  |
| `matrix_sep`    | `str`            | Separator for 2D indices (e.g., '][', ', ')                                  |
| `assignment_op` | `str`            | Assignment operator (typically '=')                                          |
| `line_end`      | `str`            | Statement terminator (';' for C/C++, '' for Python/Fortran)                  |
| `code_gen`      | `Callable`       | SymPy code generation function                                               |
| `ioff`          | `int`            | Default array indexing offset (0 or 1)                                       |
| `comment`       | `str`            | Comment prefix ('//', '!!', '#')                                             |
| `types`         | `dict[str, str]` | Type declarations for the language                                           |
| `extras`        | `dict[str, Any]` | Additional language-specific attributes                                      |

## Methods

The `Codegen` class provides two types of methods:

1. **String Methods** - Return formatted code strings ready to use (e.g., `get_rates_str()`, `get_ode_str()`)
2. **Indexed Methods** - Return structured `IndexedReturn` dictionaries with `IndexedList` objects (e.g., `get_indexed_rates()`, `get_indexed_odes()`)

### Common Constants

#### `get_commons(idx_offset=-1, idx_prefix="", definition_prefix="", assignment_op="", line_end="")`

Generate code for common constants (species indices, counts).

**Parameters:**

- `idx_offset` (int): Starting index for species. Default: -1 (use language default)
- `idx_prefix` (str): Prefix for species index names (e.g., "idx\_"). Default: ""
- `definition_prefix` (str): Prefix for definitions (e.g., "const int "). Default: ""
- `assignment_op` (str): Override assignment operator. Default: "" (use language default)
- `line_end` (str): Override line terminator. Default: "" (use language default)

**Returns:**

- `str`: Generated code with species indices and counts

**Example:**

```python
# C++ style
commons = cg.get_commons(
    idx_offset=0,
    idx_prefix="idx_",
    definition_prefix="const int "
)
```

**Output (C++):**

```cpp
const int idx_h = 0;
const int idx_h2 = 1;
const int idx_o = 2;
const int nspecs = 35;
const int nreactions = 127;
```

### Rate Calculations

#### `get_indexed_rates(use_cse=True, cse_var="x")`

Generate indexed rate expressions with optional CSE optimization.

**Parameters:**

- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "x"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of rate expressions

**Example:**

```python
result = cg.get_indexed_rates(use_cse=True, cse_var="cse")

# Access CSE temporaries
for iv in result["extras"]["cse"]:
    print(f"const double cse[{iv.indices[0]}] = {iv.value};")

# Access rate expressions
for iv in result["expressions"]:
    print(f"k[{iv.indices[0]}] = {iv.value};")
```

**See Also**: [JAFF Types API](jaff-types.md) for details on `IndexedValue` and `IndexedList`.

---

#### `get_rates_str(idx_offset=-1, rate_variable="k", brac_format="", use_cse=True, cse_var="x", var_prefix="", assignment_op="", line_end="")`

Generate code for reaction rate coefficient calculations.

**Parameters:**

- `idx_offset` (int): Starting index for rate array. Default: -1 (use language default)
- `rate_variable` (str): Name of rate array variable. Default: "k"
- `brac_format` (str): Override bracket format. Default: ""
- `use_cse` (bool): Apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variables. Default: "x"
- `var_prefix` (str): Prefix for variable declarations. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated rate calculation code

**Example:**

```python
rates = cg.get_rates_str(
    idx_offset=0,
    rate_variable="k",
    use_cse=True
)
```

**Output (C++ with CSE):**

```cpp
//Common subexpressions
const double x0 = sqrt(tgas);
const double x1 = pow(tgas/300, 0.5);
const double x2 = exp(-500/tgas);

//Rate calculations using common subexpressions
k[0] = 1.2e-10 * x1;
k[1] = 3.4e-11 * x2;
k[2] = 5.6e-12 * x0 * x1;
```

### Flux Calculations

#### `get_indexed_flux_expressions()`

Generate indexed flux expressions for all reactions.

This method creates IndexedValue objects representing flux calculations for each reaction. Fluxes are the products of rate coefficients and reactant concentrations.

**Parameters:**

None

**Returns:**

- `IndexedList`: List of IndexedValue([reaction_idx], flux_expression) objects
    - Each flux expression contains the template placeholder `$IDX$` for the reaction index
    - Uses language-specific bracket formats

**Note:**

- Flux expressions use template placeholders replaced during code generation
- Use `get_flux_expressions_str()` for formatted code strings
- Generated expressions are language-independent templates

**Example:**

```python
fluxes = cg.get_indexed_flux_expressions()
for iv in fluxes:
    print(f"Reaction {iv.indices[0]}: {iv.value}")
# Output:
# Reaction 0: k[$IDX$] * y[h] * y[o]
# Reaction 1: k[$IDX$] * y[co]
```

**See Also:**

- `get_flux_expressions_str()` - Generate formatted string output with variable names

---

#### `get_flux_expressions_str(rate_var="k", species_var="y", idx_prefix="", idx_offset=-1, brac_format="", flux_var="flux", assignment_op="", line_end="")`

Generate code for reaction flux calculations (rate × reactant concentrations).

Generate code for reaction flux calculations (rate × reactant concentrations).

**Parameters:**

- `rate_var` (str): Name of rate coefficient array. Default: "k"
- `species_var` (str): Name of species concentration array. Default: "y"
- `idx_prefix` (str): Prefix for species index names. Default: ""
- `idx_offset` (int): Starting index. Default: -1 (use language default)
- `brac_format` (str): Override bracket format. Default: ""
- `flux_var` (str): Name of flux array variable. Default: "flux"
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated flux calculation code

**Example:**

```python
fluxes = cg.get_flux_expressions_str(
    rate_var="k",
    species_var="n",
    idx_prefix="idx_",
    flux_var="flux"
)
```

**Output:**

```cpp
flux[0] = k[0] * n[idx_h] * n[idx_o];
flux[1] = k[1] * n[idx_h2] * n[idx_o];
flux[2] = k[2] * n[idx_c] * n[idx_o2];
```

### ODE Expressions

#### `get_indexed_ode_expressions()`

Generate indexed ODE expressions from flux contributions.

This method creates IndexedValue objects representing the time derivatives of species concentrations based on their participation in reactions (via fluxes).

**Parameters:**

None

**Returns:**

- `IndexedList`: List of IndexedValue([species_idx], ode_expression) objects
    - Each ODE expression is the sum of flux contributions for that species
    - Uses language-specific bracket formats

**Note:**

- Does NOT apply CSE optimization (use `get_indexed_odes()` for CSE)
- Flux expressions must be generated separately
- Use `get_ode_expressions_str()` for formatted code strings

**Example:**

```python
ode_exprs = cg.get_indexed_ode_expressions()
for iv in ode_exprs:
    print(f"Species {iv.indices[0]}: dy/dt = {iv.value}")
```

**See Also:**

- `get_ode_expressions_str()` - Generate formatted string output
- `get_indexed_odes()` - Generate ODE system with CSE optimization

---

#### `get_indexed_odes(use_cse=True, cse_var="cse")`

Generate indexed ODE expressions with optional CSE optimization.

**Parameters:**

- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of ODE right-hand side expressions

**Example:**

```python
result = cg.get_indexed_odes(use_cse=True)

# Generate CSE declarations
for iv in result["extras"]["cse"]:
    print(f"const double cse[{iv.indices[0]}] = {iv.value};")

# Generate ODE assignments
for iv in result["expressions"]:
    print(f"dydt[{iv.indices[0]}] = {iv.value};")
```

---

#### `get_ode_expressions_str(idx_offset=-1, flux_var="flux", species_var="y", idx_prefix="", derivative_prefix="d", derivative_var=None, brac_format="", assignment_op="", line_end="")`

Generate code for ODE right-hand side (dy/dt) from fluxes.

**Parameters:**

- `idx_offset` (int): Starting index. Default: -1 (use language default)
- `flux_var` (str): Name of flux array. Default: "flux"
- `species_var` (str): Name of species array. Default: "y"
- `idx_prefix` (str): Prefix for species indices. Default: ""
- `derivative_prefix` (str): Prefix for derivative variable. Default: "d"
- `derivative_var` (str): Override derivative array name. Default: None
- `brac_format` (str): Override bracket format. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated ODE code

**Example:**

```python
odes = cg.get_ode_expressions_str(
    flux_var="flux",
    species_var="y",
    idx_prefix="idx_",
    derivative_prefix="d"
)
```

**Output:**

```cpp
dy[idx_h] = 0.0 - flux[0] + flux[1];
dy[idx_o] = 0.0 - flux[0] - flux[1] + flux[2];
dy[idx_oh] = 0.0 + flux[0] + flux[1];
```

### Optimized ODE System

#### `get_indexed_rhs(use_cse=True, cse_var="cse")`

Generate indexed right-hand side expressions (ODE + energy equation).

This method combines the ODE system with the specific internal energy derivative (dedt). The energy equation is appended as the last element in the expressions list.

**Parameters:**

- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of RHS expressions (n_species + 1 elements, last is dedt)

**Note:**

- The energy equation is appended as the last element: `expressions[n_species]`
- CSE temporaries are shared from the ODE system
- Use `get_rhs_str()` for formatted code ready to write to file

**Example:**

```python
result = cg.get_indexed_rhs(use_cse=True)

# Last expression is the energy derivative
n_species = len(cg.net.species)
dedt_expr = result["expressions"][-1]
print(f"Energy equation at index {dedt_expr.indices[0]}: {dedt_expr.value}")
```

**See Also:**

- `get_rhs_str()` - Generate formatted string output
- `get_indexed_odes()` - Generate only ODE system without energy equation
- `get_dedt()` - Generate only the energy derivative expression

---

#### `get_rhs_str(idx_offset=0, use_cse=True, cse_var="cse", ode_var="f", brac_format="", def_prefix="", assignment_op="", line_end="")`

Generate formatted code string for complete RHS (ODE + energy equation).

This method combines the ODE system with the specific internal energy derivative. The energy equation is appended as the last element in the output array.

**Parameters:**

- `idx_offset` (int): Starting index for arrays. Default: 0
- `use_cse` (bool): Apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"
- `ode_var` (str): Name of output array. Default: "f"
- `brac_format` (str): Override bracket format. Default: ""
- `def_prefix` (str): Prefix for variable declarations. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated code with ODE system followed by energy equation assignment

**Note:**

- Energy equation is assigned to `ode_var[n_species]`
- CSE optimizations from ODE system are included

**Example:**

```python
rhs = cg.get_rhs_str(
    idx_offset=0,
    use_cse=True,
    ode_var="f"
)
```

**Output:**

```cpp
const double cse0 = k[0] * n[0];
const double cse1 = k[1] * n[1];

f[0] = -cse0 + cse1;
f[1] = cse0 - cse1;
f[2] = (some energy equation expression);
```

---

#### `get_ode_str(idx_offset=0, use_cse=True, cse_var="cse", ode_var="f", brac_format="", def_prefix="", assignment_op="", line_end="")`

Generate optimized ODE system with CSE applied to the entire system (without energy equation).

**Parameters:**

- `idx_offset` (int): Starting index. Default: 0
- `use_cse` (bool): Apply CSE optimization. Default: True
- `cse_var` (str): Prefix for CSE variables. Default: "cse"
- `ode_var` (str): Name of ODE output array. Default: "f"
- `brac_format` (str): Override bracket format. Default: ""
- `def_prefix` (str): Prefix for variable definitions. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated ODE code with CSE optimizations

**Note:** Results are cached after the first call.

**Example:**

```python
ode = cg.get_ode_str(
    idx_offset=0,
    use_cse=True,
    ode_var="dydt"
)
```

**Output:**

```cpp
const double cse0 = k[0] * n[0];
const double cse1 = k[1] * n[1];
const double cse2 = cse0 * n[2];

dydt[0] = -cse2 + cse1;
dydt[1] = -cse1 + cse0;
dydt[2] = cse2 - cse0;
```

### Jacobian Matrix

#### `get_indexed_jacobian(use_dedt=False, use_cse=True, cse_var="cse")`

Generate indexed Jacobian matrix elements with optional CSE optimization.

**Parameters:**

- `use_dedt` (bool): Include energy equation derivatives. Default: False
- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of Jacobian elements with 2D indices

**Note**: Jacobian elements use 2D indexing (flattened representation).

**Example:**

```python
result = cg.get_indexed_jacobian(use_cse=True)

# CSE temporaries (1D indices)
for iv in result["extras"]["cse"]:
    print(f"const double cse[{iv.indices[0]}] = {iv.value};")

# Jacobian elements (2D indices)
for iv in result["expressions"]:
    i, j = iv.indices
    print(f"jac[{i}][{j}] = {iv.value};")

# Convert to nested representation
nested_jac = result["expressions"].nested()
for iv in nested_jac:
    row_idx = iv.indices[0]
    print(f"Row {row_idx}: {len(iv.value)} elements")
```

---

#### `get_jacobian_str(use_dedt=False, idx_offset=0, use_cse=True, cse_var="cse", jac_var="J", matrix_format="", var_prefix="", assignment_op="", line_end="")`

Generate analytical Jacobian matrix (∂f_i/∂y_j).

**Parameters:**

- `use_dedt` (bool): Include energy equation derivatives. Default: False
- `idx_offset` (int): Starting index. Default: 0
- `use_cse` (bool): Apply CSE optimization. Default: True
- `cse_var` (str): Prefix for CSE variables. Default: "cse"
- `jac_var` (str): Name of Jacobian matrix variable. Default: "J"
- `matrix_format` (str): Override 2D array format. Default: ""
- `var_prefix` (str): Prefix for CSE variable declarations. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated Jacobian code with CSE optimizations

**Note:** Results are cached after the first call.

**Example:**

```python
jac = cg.get_jacobian_str(
    idx_offset=0,
    use_cse=True,
    jac_var="J"
)
```

**Output:**

```cpp
const double cse0 = k[0] * n[1];
const double cse1 = k[1] * n[0];

J[0][0] = -cse1;
J[0][1] = -cse0;
J[1][0] = cse1;
J[1][1] = cse0;
```

### Energy Derivative

#### `get_dedt()`

Generate code for specific internal energy time derivative.

**Returns:**

- `str`: Generated code for d(e)/dt calculation

**Note:** Results are cached after the first call.

**Example:**

```python
dedt = cg.get_dedt()
```

## Language-Specific Defaults

### C/C++

```python
cg = Codegen(network=net, lang="c++")
```

- **Brackets**: `[]`
- **Matrix**: `[][]`
- **Index offset**: 0
- **Line end**: `;`
- **Comment**: `//`
- **Assignment**: `=`

### Fortran

```python
cg = Codegen(network=net, lang="f90")
```

- **Brackets**: `()`
- **Matrix**: `(,)`
- **Index offset**: 1
- **Line end**: ``
- **Comment**: `!!`
- **Assignment**: `=`

### Python

```python
cg = Codegen(network=net, lang="py")
```

- **Brackets**: `[]`
- **Matrix**: `[][]`
- **Index offset**: 0
- **Line end**: ``
- **Comment**: `#`
- **Assignment**: `=`

## Usage Examples

### Example 1: Complete C++ Code Generation

```python
from jaff import Network, Codegen

# Load network
net = Network("networks/react_COthin")

# Create C++ code generator
cg = Codegen(network=net, lang="c++")

# Generate all components
commons = cg.get_commons(
    idx_offset=0,
    idx_prefix="idx_",
    definition_prefix="const int "
)

rates = cg.get_rates_str(
    idx_offset=0,
    rate_variable="k",
    use_cse=True
)

odes = cg.get_ode_str(
    idx_offset=0,
    use_cse=True,
    ode_var="dydt"
)

jac = cg.get_jacobian_str(
    idx_offset=0,
    use_cse=True,
    jac_var="J"
)

# Combine into single file
code = f"""
// Chemical network constants
{commons}

// Rate coefficient calculations
void compute_rates(double* k, double tgas) {{
{rates}
}}

// ODE right-hand side
void compute_odes(double* dydt, const double* y, const double* k) {{
{odes}
}}

// Jacobian matrix
void compute_jacobian(double** J, const double* y, const double* k) {{
{jac}
}}
"""

# Save to file
with open("chemistry.cpp", "w") as f:
    f.write(code)
```

### Example 2: Fortran Code Generation

```python
# Create Fortran code generator
cg = Codegen(network=net, lang="f90")

# Generate with Fortran conventions
commons = cg.get_commons(
    idx_offset=1,  # Fortran is 1-indexed
    idx_prefix="idx_",
    definition_prefix="integer, parameter :: "
)

rates = cg.get_rates_str(
    idx_offset=1,
    rate_variable="k",
    use_cse=True
)

# Write Fortran module
fortran_code = f"""
module chemistry
  implicit none

  {commons}

contains

  subroutine compute_rates(k, tgas)
    real(8), intent(out) :: k(nreactions)
    real(8), intent(in) :: tgas

{rates}
  end subroutine compute_rates

end module chemistry
"""
```

### Example 3: Python Code Generation

```python
# Create Python code generator
cg = Codegen(network=net, lang="python")

rates = cg.get_rates_str(
    idx_offset=0,
    rate_variable="k",
    use_cse=True
)

odes = cg.get_ode_str(
    idx_offset=0,
    use_cse=True,
    ode_var="dydt"
)

# Generate Python module
python_code = f"""
import numpy as np
from math import sqrt, exp, log

def compute_rates(tgas):
    k = np.zeros({len(net.reactions)})
{rates}
    return k

def compute_odes(y, k):
    dydt = np.zeros({len(net.species)})
{odes}
    return dydt
"""
```

### Example 4: Working with IndexedReturn and IndexedList

```python
from jaff import Network, Codegen
from jaff.codegen import IndexedReturn
from jaff.jaff_types import IndexedList, IndexedValue

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="cxx")

# Get indexed rates (returns IndexedReturn)
result: IndexedReturn = cg.get_indexed_rates(use_cse=True, cse_var="cse")

# Access CSE temporaries (IndexedList)
cse_temps: IndexedList = result["extras"]["cse"]
print(f"Number of CSE temporaries: {len(cse_temps)}")

# Iterate over CSE temporaries
for iv in cse_temps:
    idx = iv.indices[0]
    expr = iv.value
    print(f"const double cse[{idx}] = {expr};")

# Access rate expressions (IndexedList)
rate_exprs: IndexedList = result["expressions"]
for iv in rate_exprs:
    idx = iv.indices[0]
    rate = iv.value
    print(f"k[{idx}] = {rate};")

# Get Jacobian with 2D indices
jac_result = cg.get_indexed_jacobian(use_cse=True)
jac_elements: IndexedList = jac_result["expressions"]

# Jacobian is flattened by default
print(f"List type: {jac_elements.type()}")  # "flattened"

# Access individual elements (2D indices)
for iv in jac_elements:
    i, j = iv.indices  # Unpack 2D indices
    print(f"J[{i}][{j}] = {iv.value};")

# Convert to nested representation
nested_jac = jac_elements.nested()
print(f"List type: {nested_jac.type()}")  # "nested"

for iv in nested_jac:
    row_idx = iv.indices[0]
    row_elements: IndexedList = iv.value  # Each row is an IndexedList
    print(f"Row {row_idx} has {len(row_elements)} non-zero elements")

    for col_iv in row_elements:
        col_idx = col_iv.indices[0]
        print(f"  J[{row_idx}][{col_idx}] = {col_iv.value}")
```

### Example 5: Custom Bracket Formats

```python
# C with parentheses instead of brackets
cg = Codegen(network=net, lang="c", brac_format="()")

rates = cg.get_rates_str()
# Output: k(0) = ..., k(1) = ...

# Python with comma-separated 2D indexing
cg = Codegen(network=net, lang="py", matrix_format="[,]")

jac = cg.get_jacobian_str(jac_var="J")
# Output: J[0,0] = ..., J[0,1] = ...
```

### Example 6: Comparing CSE vs Non-CSE

```python
# Without CSE
rates_no_cse = cg.get_rates_str(use_cse=False)
print(f"Without CSE: {len(rates_no_cse)} characters")

# With CSE
rates_with_cse = cg.get_rates_str(use_cse=True)
print(f"With CSE: {len(rates_cse)} characters")

# CSE typically reduces code size by 20-50%
```

### Example 6: Multiple Languages from Same Network

```python
# Generate for all supported languages
languages = ["c++", "c", "f90", "python", "rust", "julia", "r"]

for lang in languages:
    cg = Codegen(network=net, lang=lang)

    rates = cg.get_rates_str(use_cse=True)
    odes = cg.get_ode_str(use_cse=True)

    # Save language-specific file
    ext = {"c++": "cpp", "c": "c", "f90": "f90", "python": "py",
           "rust": "rs", "julia": "jl", "r": "r"}[lang]
    with open(f"chemistry.{ext}", "w") as f:
        f.write(rates)
        f.write("\n\n")
        f.write(odes)
```

## Best Practices

### 1. Always Use CSE for Production Code

```python
# CSE reduces redundant calculations significantly
rates = cg.get_rates_str(use_cse=True)
odes = cg.get_ode_str(use_cse=True)
jac = cg.get_jacobian_str(use_cse=True)
```

### 2. Match Index Offsets to Your Framework

```python
# For C/C++/Python arrays starting at 0
cg = Codegen(network=net, lang="c++")
code = cg.get_rates_str(idx_offset=0)

# For Fortran arrays starting at 1
cg = Codegen(network=net, lang="f90")
code = cg.get_rates_str(idx_offset=1)
```

### 3. Use Consistent Variable Names

```python
# Consistent naming across components
commons = cg.get_commons(idx_prefix="idx_")
rates = cg.get_rates_str(rate_variable="k")
fluxes = cg.get_flux_expressions_str(rate_var="k", species_var="n")
odes = cg.get_ode_expressions_str(flux_var="flux", species_var="n")
```

### 4. Cache Code Generator Objects

```python
# Create once, use many times
cg = Codegen(network=net, lang="c++")

# Multiple calls reuse the same configuration
rates = cg.get_rates_str(use_cse=True)
odes = cg.get_ode_str(use_cse=True)
jac = cg.get_jacobian_str(use_cse=True)
```

### 5. Review Generated Code

```python
# Always inspect generated code
code = cg.get_rates_str(use_cse=True)
print(code)  # Check for correctness

# Or save to file and review
with open("temp.cpp", "w") as f:
    f.write(code)
```

## Performance Considerations

### CSE Optimization

Common Subexpression Elimination can significantly improve runtime:

- **Without CSE**: Each expression computed independently
- **With CSE**: Shared subexpressions computed once and reused
- **Typical savings**: 20-50% reduction in operations for complex networks

### Caching

Methods like `get_ode()` and `get_jacobian()` cache results:

```python
# First call: computes and caches
ode1 = cg.get_ode_str(use_cse=True)  # Slow

# Subsequent calls: returns cached result
ode2 = cg.get_ode_str(use_cse=True)  # Fast (instant)
```

### Large Networks

For networks with 1000+ reactions:

- Use CSE to reduce code complexity
- Consider generating code in chunks
- Test compilation of generated code

## Common Patterns

### Pattern 1: Complete Integration Code

```python
def generate_full_chemistry(net, lang="c++"):
    cg = Codegen(network=net, lang=lang)

    code = f"""
// Species indices and counts
{cg.get_commons(idx_prefix='idx_', definition_prefix='const int ')}

// Rate coefficients
{cg.get_rates_str(use_cse=True)}

// ODE system
{cg.get_ode_str(use_cse=True)}

// Jacobian
{cg.get_jacobian_str(use_cse=True)}
"""
    return code
```

### Pattern 2: Separate Components

```python
def generate_modular_code(net):
    cg = Codegen(network=net, lang="c++")

    # Separate files for different components
    with open("constants.h", "w") as f:
        f.write(cg.get_commons())

    with open("rates.cpp", "w") as f:
        f.write(cg.get_rates_str(use_cse=True))

    with open("odes.cpp", "w") as f:
        f.write(cg.get_ode_str(use_cse=True))
```

### Pattern 3: Custom Formatting

```python
def generate_with_headers(net):
    cg = Codegen(network=net, lang="c++")

    code = f"""
// Generated by JAFF
// Network: {net.label}
// Species: {len(net.species)}
// Reactions: {len(net.reactions)}

#include <cmath>

{cg.get_commons(definition_prefix='const int ')}

void chemistry(double* dydt, const double* y, double tgas) {{
    // Allocate arrays
    double k[{len(net.reactions)}];

    // Compute rates
{cg.get_rates_str(rate_variable='k', use_cse=True)}

    // Compute ODEs
{cg.get_ode_str(ode_var='dydt', use_cse=True)}
}}
"""
    return code
```

## Language-Specific Differences

### Indexing Conventions

Different languages use different array indexing conventions:

| Language | Index Offset | Default Bracket | Example    |
| -------- | ------------ | --------------- | ---------- |
| C        | 0-based      | `[]`            | `array[0]` |
| C++      | 0-based      | `[]`            | `array[0]` |
| Python   | 0-based      | `[]`            | `array[0]` |
| Rust     | 0-based      | `[]`            | `array[0]` |
| Fortran  | 1-based      | `()`            | `array(1)` |
| Julia    | 1-based      | `[]`            | `array[1]` |
| R        | 1-based      | `[]`            | `array[1]` |

### Statement Terminators

| Language | Terminator | Example  |
| -------- | ---------- | -------- |
| C        | `;`        | `x = 1;` |
| C++      | `;`        | `x = 1;` |
| Rust     | `;`        | `x = 1;` |
| Python   | (none)     | `x = 1`  |
| Fortran  | (none)     | `x = 1`  |
| Julia    | (none)     | `x = 1`  |
| R        | (none)     | `x <- 1` |

### Assignment Operators

| Language | Operator | Example  |
| -------- | -------- | -------- |
| C/C++    | `=`      | `x = 5;` |
| Python   | `=`      | `x = 5`  |
| Rust     | `=`      | `x = 5;` |
| Fortran  | `=`      | `x = 5`  |
| Julia    | `=`      | `x = 5`  |
| R        | `<-`     | `x <- 5` |

### Comment Styles

| Language | Prefix | Example                |
| -------- | ------ | ---------------------- |
| C/C++    | `//`   | `// This is a comment` |
| Rust     | `//`   | `// This is a comment` |
| Python   | `#`    | `# This is a comment`  |
| Julia    | `#`    | `# This is a comment`  |
| R        | `#`    | `# This is a comment`  |
| Fortran  | `!!`   | `!! This is a comment` |

### Type Declarations

**C/C++:**

```cpp
const double x = 1.0;
const int i = 42;
const bool flag = true;
```

**Rust:**

```rust
const x: f64 = 1.0;
const i: i32 = 42;
const flag: bool = true;
```

**Julia:**

```julia
const x::Float64 = 1.0
const i::Int64 = 42
const flag::Bool = true
```

**Python, R, Fortran:**
No explicit type declarations in generated code.

### Requirements

**Note:** Rust, Julia, and R support require **SymPy >= 1.7** which includes:

- `sympy.rust_code()` - Rust code generation
- `sympy.julia_code()` - Julia code generation
- `sympy.rcode()` - R code generation

## Error Handling

```python
# Handle unsupported languages
try:
    cg = Codegen(network=net, lang="ruby")
except ValueError as e:
    print(f"Error: {e}")

# Handle invalid bracket formats
try:
    cg = Codegen(network=net, brac_format="<<")
except ValueError as e:
    print(f"Error: {e}")
```

## See Also

- [JAFF Types API](jaff-types.md) - IndexedValue and IndexedList type definitions
- [Network API](network.md) - Loading and analyzing networks
- [File Parser API](file-parser.md) - Template-based code generation
- [CLI API](cli.md) - Command-line interface
- [User Guide: Code Generation](../user-guide/code-generation.md) - Detailed guide

---

**Next**: Learn about [Template-Based Generation](file-parser.md) with the Fileparser class.
