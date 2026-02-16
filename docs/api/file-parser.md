# File Parser API Reference

The `file_parser` module provides the core template parsing functionality for JAFF code generation.

## Overview

The file parser processes template files containing JAFF directives and generates code for chemical reaction networks in multiple programming languages (C, C++, Fortran). It supports a sophisticated template syntax with commands for iteration, substitution, conditional logic, and array reductions.

**Key Features:**

- **Multi-language support**: C, C++, Fortran code generation
- **Iterative templates**: Loop over reactions, species, and network components
- **Property substitution**: Insert network properties into templates
- **Array reductions**: Generate sum/product expressions over arrays
- **CSE optimization**: Common Subexpression Elimination for efficient code
- **Conditional logic**: Check for entity existence
- **Index arithmetic**: Offset indices for different programming conventions

## Module: `jaff.file_parser`

### Main Class

#### Fileparser

The main parser class that processes template files and generates code.

**Constructor:**

```python
Fileparser(network: Network, file: Path) -> None
```

**Parameters:**

- `network` (Network): The loaded chemical reaction network
- `file` (Path): Path to the template file to parse

**Example:**

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

net = Network("networks/react_COthin")
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()
```

---

##### Methods

###### parse_file()

Parse the entire template file and generate code.

**Signature:**

```python
def parse_file(self) -> str
```

**Returns:**

- `str`: Generated code with all JAFF directives expanded

**Example:**

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

net = Network("networks/test.dat")
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# Write to file
with open("output.cpp", "w") as f:
    f.write(output)
```

---

### TypedDict Classes

The file parser uses several TypedDict classes to structure internal data and provide type safety.

#### IdxSpanResult

```python
class IdxSpanResult(TypedDict):
    """Result structure for index span detection."""
    offset: list[int]
    span: list[tuple[int, int]]
```

Result structure returned when detecting and parsing index tokens in template lines.

**Attributes:**

- `offset` (list[int]): List of integer offsets for each index token
    - Example: For `$idx+2$`, the offset would be `[2]`
    - For `$idx$`, the offset would be `[0]`
    - For `$idx-1$`, the offset would be `[-1]`
    - Supports multiple indices per line
- `span` (list[tuple[int, int]]): List of (start, end) positions of each index token in the string
    - Used for replacing index tokens with actual values
    - Each tuple contains character positions for token boundaries

**Internal Usage Example:**

```python
# When processing: "rate[$idx+1$] = $rate$;"
# Returns IdxSpanResult:
# {
#     "offset": [1],      # +1 offset
#     "span": [(5, 13)]   # Position of "$idx+1$"
# }
```

---

#### CommandProps

```python
class CommandProps(TypedDict):
    """Properties defining a JAFF command."""
    func: Callable[..., Any]
    props: dict[str, dict[str, Any]]
```

Properties structure that defines how a JAFF command is processed.

**Attributes:**

- `func` (Callable[..., Any]): Callable function that handles the command execution
    - Takes parsed command arguments and processes the template block
    - Returns modified output or None
- `props` (dict[str, dict[str, Any]]): Dictionary mapping property names to their metadata
    - Keys: Property names (e.g., "species", "reactions", "rates")
    - Values: Dict containing handler functions and configuration

---

#### CseProps

```python
class CseProps(TypedDict):
    """Common Subexpression Elimination (CSE) properties."""
    parsed: bool
    prefix: str
    var: str
```

Tracks the state and configuration for Common Subexpression Elimination during template parsing.

**Attributes:**

- `parsed` (bool): Whether the CSE declaration block has been parsed
    - `False`: CSE variables not yet declared
    - `True`: CSE block already processed, use CSE-optimized expressions
- `prefix` (str): Prefix string for CSE variable definitions
    - Example: `"const double "` for C++
    - Applied when generating CSE temporary variable declarations
- `var` (str): Variable name/prefix used for CSE storage
    - Default: `"cse"`
    - Used as array name or variable prefix: `cse[0]`, `cse[1]`, etc.

**Usage Example:**

When processing a template with CSE:

```cpp
// $JAFF REPEAT idx, cse IN rates
const double cse[$idx$] = $cse$;
// $JAFF END
```

The parser maintains CSE state to coordinate between declaration and usage blocks.

---

## JAFF Template Syntax

### Supported Commands

The file parser recognizes six main JAFF commands:

1. **SUB** - Token substitution
2. **REPEAT** - Iteration over arrays/components
3. **GET** - Retrieve specific entity properties
4. **HAS** - Check entity existence
5. **REDUCE** - Generate reduction expressions (sum, product, etc.)
6. **END** - Terminate directive block

---

### REPLACE Directive

All JAFF commands (SUB, REPEAT, REDUCE, GET, HAS) support optional **REPLACE** directives for regex-based text replacement in the generated output.

**Syntax:**

```cpp
// $JAFF COMMAND arguments [REPLACE pattern1 replacement1 [REPLACE pattern2 replacement2 ...]]
code
// $JAFF END
```

**Key Features:**

- Replacements are applied **after** primary code generation
- Patterns use Python regex syntax (compiled with `re.compile()`)
- Supports capture groups and backreferences (`\1`, `\2`, etc.)
- Multiple REPLACE directives can be chained
- Applied sequentially in the order specified
- Replacement state is automatically reset at END

**Basic Example:**

```cpp
// $JAFF SUB nspec [REPLACE const constexpr]
const int NUM_SPECIES = $nspec$;
// $JAFF END
```

**Output:**

```cpp
constexpr int NUM_SPECIES = 14;  // 'const' replaced with 'constexpr'
```

**Regex with Capture Groups:**

```cpp
// $JAFF REPEAT idx, specie IN species [REPLACE H_(\d+) Hydrogen_\1 REPLACE He Helium]
species[$idx$] = "$specie$";
// $JAFF END
```

**Output:**

```cpp
species[0] = "Hydrogen_1";  // H_1 -> Hydrogen_1 using capture group \1
species[1] = "Hydrogen_2";  // H_2 -> Hydrogen_2
species[2] = "Helium";      // He -> Helium
```

**Multiple Replacements:**

```cpp
// $JAFF REPEAT idx, specie IN species [REPLACE \+ _plus REPLACE - _minus]
species[$idx$] = "$specie$";  // H+ -> H_plus, e- -> e_minus
// $JAFF END
```

**Advanced Example - Normalizing Names:**

```cpp
// $JAFF GET specie_idx, specie_mass FOR H+ [REPLACE H\+ H_PLUS REPLACE e-24 e-24]
const int idx = $specie_idx$;
const double mass = $specie_mass$;  // 1.673773e-24 remains unchanged
// $JAFF END
```

**Important Notes:**

1. **REPLACE directives must be enclosed in square brackets**
    - ✅ Correct: `// $JAFF SUB nspec [REPLACE old new]`
    - ❌ Wrong: `// $JAFF SUB nspec REPLACE old new` (missing brackets)
    - ❌ Wrong: `// $JAFF SUB [REPLACE old new] nspec` (brackets must be after arguments)

2. **Pattern is regex, replacement is literal** (except backreferences)
    - Pattern: `H_(\d+)` matches H_1, H_2, etc.
    - Replacement: `Hydrogen_\1` becomes Hydrogen_1, Hydrogen_2, etc.

3. **Each REPLACE needs both pattern and replacement**
    - ✅ Correct: `[REPLACE pattern replacement]`
    - ❌ Wrong: `[REPLACE pattern]` (missing replacement - raises SyntaxError)

4. **Invalid regex patterns raise SyntaxError**
    - Invalid: `[REPLACE [invalid( bad_regex]`
    - Error: `SyntaxError: Invalid regex pattern '[invalid(' in line ...`

5. **Replacements are scoped to the command block**
    - Reset automatically at `// $JAFF END`
    - Don't carry over to subsequent blocks

**Use Cases:**

- Convert naming conventions (e.g., `+` to `_plus`)
- Sanitize species names for different languages
- Replace keywords (e.g., `const` to `constexpr`)
- Add prefixes/suffixes to generated identifiers
- Transform numeric formats
- Clean up special characters

**Error Handling:**

```python
# Missing replacement string
# $JAFF SUB nspec [REPLACE pattern]
# Raises: SyntaxError: Invalid replacement syntax in ...

# Invalid regex
# $JAFF SUB nspec [REPLACE [invalid regex]
# Raises: SyntaxError: Invalid regex pattern '[invalid' in ...: ...

# Missing brackets
# $JAFF SUB nspec REPLACE old new
# Raises: ValueError (or splits incorrectly)
```

---

### 1. SUB - Token Substitution

Substitute template tokens with scalar values from the network.

**Syntax:**

```cpp
// $JAFF SUB token1, token2, ... [REPLACE pattern replacement ...]
code with $token1$ and $token2$
// $JAFF END
```

**With REPLACE:**

```cpp
// $JAFF SUB nspec, label [REPLACE test production]
const int NUM_SPECIES = $nspec$;  // Network: "$label$"
// $JAFF END
```

**Available Tokens:**

| Token        | Type   | Description                    | Example Value    |
| ------------ | ------ | ------------------------------ | ---------------- |
| `$nspec$`    | int    | Number of species              | `14`             |
| `$nreact$`   | int    | Number of reactions            | `15`             |
| `$nelem$`    | int    | Number of elements             | `5`              |
| `$label$`    | string | Network label                  | `"test"`         |
| `$filename$` | string | Template filename              | `"template.cpp"` |
| `$filepath$` | Path   | Full template path             | `Path("...")`    |
| `$dedt$`     | string | Energy equation code           | `"dE/dt = ..."`  |
| `$e_idx$`    | int    | Index of electron species (e-) | `1`              |

**Example:**

```cpp
// $JAFF SUB nspec, nreact, label
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
const char* NETWORK_NAME = "$label$";
// $JAFF END
```

**Output** (for test.dat network):

```cpp
const int NUM_SPECIES = 14;
const int NUM_REACTIONS = 15;
const char* NETWORK_NAME = "test";
```

**Arithmetic Operations:**

You can apply arithmetic to numeric tokens:

```cpp
// $JAFF SUB nspec
int array[$nspec+1$];      // Add 1
int last_idx = $nspec-1$;  // Subtract 1
int doubled = $nspec*2$;   // Multiply
// $JAFF END
```

---

### 2. REPEAT - Iteration

Iterate over network components or generate indexed code expressions.

**Syntax:**

```cpp
// $JAFF REPEAT var1, var2 IN property [extras]
template with $var1$ and $var2$
// $JAFF END
```

Where `[extras]` can include: `SORT`, `CSE TRUE/FALSE`, `REPLACE pattern replacement ...`

**With REPLACE:**

```cpp
// $JAFF REPEAT idx, specie IN species [REPLACE \+ _plus REPLACE - _minus]
species[$idx$] = "$specie$";  // Converts H+ to H_plus, e- to e_minus
// $JAFF END
```

**Syntax:**

```cpp
// $JAFF REPEAT var1, var2, ... IN property [SORT] [CSE TRUE/FALSE]
template line with $var1$ and $var2$
// $JAFF END
```

**Modifiers:**

- `SORT`: Sort items alphabetically (for iterable properties)
- `CSE TRUE/FALSE`: Enable/disable CSE for this block

---

#### REPEAT Properties

##### Iterable Properties (Simple Lists)

These properties iterate over lists with direct value access.

| Property                    | Variables     | Description                      |
| --------------------------- | ------------- | -------------------------------- |
| `species`                   | idx, specie   | All species names                |
| `species_ne`                | idx, specie   | Species excluding electron       |
| `reactions`                 | idx, reaction | All reactions                    |
| `reactants`                 | idx, reactant | Reactants in each reaction       |
| `products`                  | idx, product  | Products in each reaction        |
| `elements`                  | idx, element  | All elements                     |
| `element_in_species_matrix` | idx, element  | Element counts per species (2D)  |
| `element_density_matrix`    | idx, element  | Element density per species (2D) |

**Example - Species:**

```cpp
// $JAFF REPEAT idx, specie IN species
species_names[$idx$] = "$specie$";
// $JAFF END
```

**Output:**

```cpp
species_names[0] = "H+";
species_names[1] = "e-";
species_names[2] = "H";
species_names[3] = "C";
// ... etc
```

**Example - Species without Electron:**

```cpp
// $JAFF REPEAT idx, specie IN species_ne
names[$idx$] = "$specie$";  // e- excluded
// $JAFF END
```

**Output:**

```cpp
names[0] = "H+";
names[1] = "H";    // e- skipped
names[2] = "C";
// ...
```

---

##### Non-Iterable Properties (Expression Generators)

These properties generate indexed code expressions (rates, ODEs, Jacobian).

| Property           | Variables      | Token               | Description               |
| ------------------ | -------------- | ------------------- | ------------------------- |
| `rates`            | idx, rate, cse | `$rate$`            | Reaction rate expressions |
| `sorted_rates`     | idx, rate, cse | `$rate$`            | Sorted reaction rates     |
| `odes`             | idx, ode, cse  | `$ode$`             | ODE right-hand sides      |
| `rhses`            | idx, rhs, cse  | `$rhs$`             | RHS expressions           |
| `jacobian`         | idx, expr, cse | `$expr$`            | Jacobian matrix elements  |
| `flux_expressions` | idx, flux_expr | `$flux_expression$` | Flux calculations         |
| `ode_expressions`  | idx, ode_expr  | `$ode_expression$`  | ODE expressions           |

**Example - Rates:**

```cpp
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output:**

```cpp
rate[0] = 3.61e-12 * pow(Tgas/300, -0.75) * n[0] * n[1];
rate[1] = 4.60e-01 * crate * n[2];
rate[2] = 3.39e-10 * exp(-3.761 * av) * n[3];
// ...
```

---

##### Scalar Property Arrays

These properties return arrays of scalar values for each species/reaction.

**Species Properties:**

| Property                    | Variables             | Token                       | Description                     |
| --------------------------- | --------------------- | --------------------------- | ------------------------------- |
| `specie_masses`             | idx, specie_mass      | `$specie_mass$`             | Mass of each species (g)        |
| `specie_masses_ne`          | idx, specie_mass_ne   | `$specie_mass_ne$`          | Masses excluding electron       |
| `specie_charges`            | idx, specie_charge    | `$specie_charge$`           | Charge of each species          |
| `specie_charges_ne`         | idx, specie_charge_ne | `$specie_charge_ne$`        | Charges excluding electron      |
| `charge_truths`             | idx, charge_truth     | `$charge_truth$`            | 1 if charged, 0 if neutral      |
| `charge_truths_ne`          | idx, charge_truth     | `$charge_truth$`            | Charge truth excluding electron |
| `specie_indices`            | idx, specie_index     | `$specie_index$`            | Index of each species           |
| `neutral_specie_indices`    | idx, neutral_idx      | `$neutral_specie_index$`    | Indices of neutral species      |
| `neutral_specie_indices_ne` | idx, neutral_idx_ne   | `$neutral_specie_index_ne$` | Neutral indices (no e-)         |
| `charged_specie_indices`    | idx, charged_idx      | `$charged_specie_index$`    | Indices of charged species      |
| `charged_specie_indices_ne` | idx, charged_idx_ne   | `$charged_specie_index_ne$` | Charged indices (no e-)         |
| `neutral_specie_masses`     | idx, neutral_mass     | `$neutral_specie_mass$`     | Masses of neutral species       |
| `neutral_specie_masses_ne`  | idx, neutral_mass_ne  | `$neutral_specie_mass_ne$`  | Neutral masses (no e-)          |
| `charged_specie_masses`     | idx, charged_mass     | `$charged_specie_mass$`     | Masses of charged species       |
| `charged_specie_masses_ne`  | idx, charged_mass_ne  | `$charged_specie_mass_ne$`  | Charged masses (no e-)          |

**Reaction Properties:**

| Property          | Variables     | Token        | Description              |
| ----------------- | ------------- | ------------ | ------------------------ |
| `photo_reactions` | idx, reaction | `$reaction$` | Photoreactions only      |
| `tmins`           | idx, tmin     | `$tmin$`     | Minimum temperatures (K) |
| `tmaxes`          | idx, tmax     | `$tmax$`     | Maximum temperatures (K) |

**Example - Species Masses (excluding electron):**

```cpp
// $JAFF REPEAT idx IN specie_masses_ne
const double mass_$idx$ = $specie_mass_ne$;
// $JAFF END
```

**Output** (quantitatively verified):

```cpp
const double mass_0 = 1.673773e-24;   // H+
const double mass_1 = 1.673773e-24;   // H
const double mass_2 = 1.994473e-23;   // C
const double mass_3 = 1.994473e-23;   // C+
const double mass_4 = 4.651236e-23;   // CO+
// ... (13 total, electron excluded)
```

**Example - Charged Species Only:**

```cpp
// $JAFF REPEAT idx IN charged_specie_indices_ne
int charged_idx_$idx$ = $charged_specie_index_ne$;
// $JAFF END
```

---

#### Index Offsets

For languages with 1-based indexing (Fortran), use index arithmetic:

```cpp
// $JAFF REPEAT idx IN species
species_names($idx+1$) = "$specie$"  ! Fortran 1-based
// $JAFF END
```

**Output:**

```fortran
species_names(1) = "H+"
species_names(2) = "e-"
species_names(3) = "H"
```

---

#### Sorting

Sort items alphabetically:

```cpp
// $JAFF REPEAT idx, specie IN species SORT
sorted_species[$idx$] = "$specie$";
// $JAFF END
```

---

#### Horizontal Mode (Inline Arrays)

Omit `idx` to generate inline comma-separated lists:

```cpp
// $JAFF REPEAT specie IN species
const char* names[] = {"$specie$"};
// $JAFF END
```

**Output:**

```cpp
const char* names[] = {"H+", "e-", "H", "C", "C+", "CO+", "CO"};
```

---

### 3. GET - Retrieve Properties

Retrieve specific properties for named entities (species, reactions, elements).

**Syntax:**

```cpp
// $JAFF GET property1, property2 FOR entity_name [REPLACE pattern replacement ...]
code with $property1$ and $property2$
// $JAFF END
```

**With REPLACE:**

```cpp
// $JAFF GET specie_idx FOR H+ [REPLACE 0 ZERO]
const int idx = $specie_idx$;  // 0 becomes ZERO
// $JAFF END
```

**Note:** GET requires the `FOR` keyword to specify the entity.

---

#### Available GET Properties

**Element Properties:**

| Property      | Type | Description   |
| ------------- | ---- | ------------- |
| `element_idx` | int  | Element index |

**Species Properties:**

| Property        | Type   | Description          |
| --------------- | ------ | -------------------- |
| `specie_idx`    | int    | Species index        |
| `specie_mass`   | float  | Species mass (g)     |
| `specie_charge` | int    | Species charge       |
| `specie_latex`  | string | LaTeX representation |

**Reaction Properties:**

| Property            | Type   | Description              |
| ------------------- | ------ | ------------------------ |
| `reaction_idx`      | int    | Reaction index           |
| `reaction_tmin`     | float  | Minimum temperature (K)  |
| `reaction_tmax`     | float  | Maximum temperature (K)  |
| `reaction_verbatim` | string | Original reaction string |

---

#### GET Examples

**Example 1: Single Species Properties**

```cpp
// $JAFF GET specie_idx, specie_mass, specie_charge FOR H+
const int h_plus_idx = $specie_idx$;
const double h_plus_mass = $specie_mass$;
const int h_plus_charge = $specie_charge$;
// $JAFF END
```

**Output** (quantitatively verified against test.dat):

```cpp
const int h_plus_idx = 0;
const double h_plus_mass = 1.673773e-24;
const int h_plus_charge = 1;
```

**Example 2: Multiple Species**

```cpp
// $JAFF GET specie_idx FOR CO
const int co_idx = $specie_idx$;
// $JAFF END

// $JAFF GET specie_mass FOR N2+
const double n2_plus_mass = $specie_mass$;
// $JAFF END
```

**Output** (verified):

```cpp
const int co_idx = 6;

const double n2_plus_mass = 4.651734e-23;
```

**Example 3: Reaction Properties**

```cpp
// $JAFF GET reaction_tmin, reaction_tmax FOR reaction_name
double tmin = $reaction_tmin$;
double tmax = $reaction_tmax$;
// $JAFF END
```

---

### 4. HAS - Check Existence

Check if a species, reaction, or element exists in the network.

**Syntax:**

```cpp
// $JAFF HAS entity_type entity_name [REPLACE pattern replacement ...]
int result = $entity_type$;
// $JAFF END
```

**With REPLACE:**

```cpp
// $JAFF HAS specie e- [REPLACE 1 true REPLACE 0 false]
const bool has_electron = $specie$;  // 1 becomes true, 0 becomes false
// $JAFF END
```

**Entity Types:**

- `specie` - Check if a species exists
- `reaction` - Check if a reaction exists
- `element` - Check if an element exists

**Example:**

```cpp
// $JAFF HAS specie e-
const int has_electrons = $specie$;
// $JAFF END

// $JAFF HAS specie Ar
const int has_argon = $specie$;
// $JAFF END
```

**Output:**

```cpp
const int has_electrons = 1;  // e- exists

const int has_argon = 0;      // Ar not in network
```

**Use Case - Conditional Compilation:**

```cpp
// $JAFF HAS specie e-
#if $specie$
    // Code that requires electrons
    compute_ionization_rates();
#endif
// $JAFF END
```

---

### 5. REDUCE - Array Reduction Expressions

Generate expressions that combine array elements (sum, product, etc.).

**Syntax:**

```cpp
// $JAFF REDUCE variable_name IN property_name [REPLACE pattern replacement ...]
result = $($variable_name$ OPERATION $variable_name$)$;
// $JAFF END
```

**With REPLACE:**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne [REPLACE \+ plus]
const double total = $($specie_mass_ne$ + $specie_mass_ne$)$;  // + becomes plus
// $JAFF END
```

**Important:** The formula pattern inside `$(...$)` must include the variable name(s) being reduced.

---

#### REDUCE Properties

| Property                   | Variable Name            | Description                 |
| -------------------------- | ------------------------ | --------------------------- |
| `specie_masses`            | `specie_mass`            | All species masses          |
| `specie_masses_ne`         | `specie_mass_ne`         | Masses excluding electron   |
| `specie_charges`           | `specie_charge`          | All species charges         |
| `specie_charges_ne`        | `specie_charge_ne`       | Charges excluding electron  |
| `charge_truths`            | `charge_truth`           | Charge truth values (0/1)   |
| `charge_truths_ne`         | `charge_truth`           | Charge truths (no electron) |
| `neutral_specie_masses_ne` | `neutral_specie_mass_ne` | Neutral species masses      |
| `charged_specie_masses_ne` | `charged_specie_mass_ne` | Charged species masses      |
| `tmins`                    | `tmin`                   | Minimum temperatures        |
| `tmaxes`                   | `tmax`                   | Maximum temperatures        |

---

#### REDUCE Examples

**Example 1: Sum of All Species Masses (No Electron)**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
const double total_mass = $($specie_mass_ne$ + $specie_mass_ne$)$;
// $JAFF END
```

**Output** (quantitatively verified):

```cpp
const double total_mass = 1.673773e-24 + 1.673773e-24 + 1.994473e-23 +
    1.994473e-23 + 4.651236e-23 + 4.651236e-23 + 2.656763e-23 +
    2.329228e-23 + 2.161850e-23 + 4.651734e-23 + 2.325867e-23 +
    4.651734e-23 + 3.347546e-24;
```

This evaluates to: **3.273810e-22 g** (total mass of 13 species excluding electron)

**Example 2: Product of Values**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
const double mass_product = $($specie_mass_ne$ * $specie_mass_ne$)$;
// $JAFF END
```

**Output:**

```cpp
const double mass_product = 1.673773e-24 * 1.673773e-24 * 1.994473e-23 * ...;
```

**Example 3: Custom Formula**

```cpp
// $JAFF REDUCE specie_charge_ne IN specie_charges_ne
const int total_charge = $($specie_charge_ne$ + $specie_charge_ne$)$;
// $JAFF END
```

**Output:**

```cpp
const int total_charge = 1 + 0 + 0 + 1 + 1 + 0 + 0 + 0 + 0 + 0 + 0 + 1 + 0;
```

**Example 4: Array Initialization**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
double masses[] = {$($specie_mass_ne$, $specie_mass_ne$)$};
// $JAFF END
```

**Output:**

```cpp
double masses[] = {1.673773e-24, 1.673773e-24, 1.994473e-23, ...};
```

---

### 6. END - Terminate Block

Mark the end of a JAFF directive block.

**Syntax:**

```cpp
// $JAFF END
```

All JAFF commands except inline substitutions must be terminated with `END`.

---

## Common Subexpression Elimination (CSE)

CSE optimization reduces redundant calculations in generated expressions by extracting common subexpressions into temporary variables.

### Without CSE

```cpp
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output:**

```cpp
rate[0] = k[0] * exp(-100.0/Tgas) * n[0] * n[1];
rate[1] = k[1] * exp(-100.0/Tgas) * n[2] * n[3];
rate[2] = k[2] * exp(-200.0/Tgas) * n[4] * n[5];
rate[3] = k[3] * exp(-100.0/Tgas) * n[6] * n[7];
```

The expression `exp(-100.0/Tgas)` is repeated unnecessarily.

### With CSE

```cpp
// CSE declaration block
// $JAFF REPEAT idx, cse IN rates
double cse[$idx$] = $cse$;
// $JAFF END

// Rate expressions using CSE
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output:**

```cpp
// CSE temporaries
double cse[0] = exp(-100.0/Tgas);
double cse[1] = exp(-200.0/Tgas);

// Rates using CSE variables
rate[0] = k[0] * cse[0] * n[0] * n[1];
rate[1] = k[1] * cse[0] * n[2] * n[3];
rate[2] = k[2] * cse[1] * n[4] * n[5];
rate[3] = k[3] * cse[0] * n[6] * n[7];
```

**Benefits:**

- Fewer computations (exp called 2 times instead of 4)
- Better compiler optimization opportunities
- Improved numerical precision (consistent value reuse)

### CSE Control

Enable/disable CSE per block:

```cpp
// $JAFF REPEAT idx IN rates CSE FALSE
rate[$idx$] = $rate$;  // CSE disabled for this block
// $JAFF END
```

---

## Advanced Features

### 2D Lists and Nested Structures

For nested structures like element composition matrices:

```cpp
// $JAFF REPEAT idx, element IN element_in_species_matrix
int matrix[$idx$][] = {$element$};
// $JAFF END
```

**Output:**

```cpp
int matrix[0][] = {1, 0, 1, 2};  // C count in each species
int matrix[1][] = {0, 2, 0, 4};  // H count in each species
int matrix[2][] = {1, 0, 1, 1};  // O count in each species
```

### Multi-Token Templates

Use multiple variables in one line:

```cpp
// $JAFF REPEAT idx, specie, mass, charge IN species
printf("Species %d: %s (mass=%.3e, q=%d)\n", $idx$, "$specie$", $mass$, $charge$);
// $JAFF END
```

---

## Complete Example Templates

### Example 1: C++ Reaction Network

```cpp
// network.cpp - Generated from template
#include <cmath>
#include <vector>

// $JAFF SUB nspec, nreact
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
// $JAFF END

// Species names
// $JAFF REPEAT idx, specie IN species
const char* SPECIES_NAMES[] = {"$specie$"};
// $JAFF END

// Species masses (g)
// $JAFF REPEAT idx IN specie_masses_ne
const double SPECIES_MASSES[] = {$specie_mass_ne$};
// $JAFF END

// Species charges
// $JAFF REPEAT idx IN specie_charges
const int SPECIES_CHARGES[] = {$specie_charge$};
// $JAFF END

// Compute reaction rates
void compute_rates(double* rate, const double* n, const double* k,
                   double Tgas, double crate, double av) {
    // $JAFF REPEAT idx IN rates
    rate[$idx$] = $rate$;
    // $JAFF END
}

// Compute ODEs
void compute_odes(double* dydt, const double* y, const double* rate) {
    // $JAFF REPEAT idx IN odes
    dydt[$idx$] = $ode$;
    // $JAFF END
}

// Compute Jacobian
void compute_jacobian(double* jac, const double* y, const double* rate) {
    // $JAFF REPEAT idx IN jacobian
    jac[$idx$] = $expr$;
    // $JAFF END
}
```

### Example 2: Fortran Module

```fortran
! network.f90
module network_module
    implicit none

    ! $JAFF SUB nspec, nreact
    integer, parameter :: NUM_SPECIES = $nspec$
    integer, parameter :: NUM_REACTIONS = $nreact$
    ! $JAFF END

    ! Species names
    ! $JAFF REPEAT idx, specie IN species
    character(len=20), dimension($nspec$) :: species_names = (/ "$specie$" /)
    ! $JAFF END

contains

    subroutine compute_rates(rate, n, k, Tgas)
        real(8), intent(out) :: rate(NUM_REACTIONS)
        real(8), intent(in) :: n(NUM_SPECIES)
        real(8), intent(in) :: k(NUM_REACTIONS)
        real(8), intent(in) :: Tgas

        ! $JAFF REPEAT idx IN rates
        rate($idx+1$) = $rate$
        ! $JAFF END
    end subroutine

end module
```

### Example 3: Conditional Code Generation

```cpp
// conditionals.cpp
#include <iostream>

// Check for electron species
// $JAFF HAS specie e-
#define HAS_ELECTRONS $specie$
// $JAFF END

#if HAS_ELECTRONS
void compute_ionization_rates() {
    // $JAFF GET specie_idx FOR e-
    const int e_idx = $specie_idx$;
    // $JAFF END

    std::cout << "Electron species at index: " << e_idx << std::endl;
}
#endif

// Get properties for specific species
// $JAFF GET specie_idx, specie_mass FOR H+
const int H_PLUS_IDX = $specie_idx$;
const double H_PLUS_MASS = $specie_mass$;  // Exact: 1.673773e-24
// $JAFF END

// $JAFF GET specie_idx, specie_mass FOR CO
const int CO_IDX = $specie_idx$;
const double CO_MASS = $specie_mass$;      // Exact: 4.651236e-23
// $JAFF END
```

---

## Python Usage

### Basic Usage

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network
net = Network("networks/test.dat")

# Parse template
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# Write output
with open("generated.cpp", "w") as f:
    f.write(output)

print(f"Generated {len(output)} characters of code")
```

### Batch Processing

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network once
net = Network("networks/react_COthin")

# Process multiple templates
templates = [
    "rates.cpp",
    "odes.cpp",
    "jacobian.cpp",
    "species.h"
]

for template_file in templates:
    parser = Fileparser(net, Path(template_file))
    output = parser.parse_file()

    output_file = template_file.replace(".cpp", "_generated.cpp")
    with open(output_file, "w") as f:
        f.write(output)

    print(f"✓ Generated {output_file}")
```

---

## Validation and Testing

The file parser has been **quantitatively validated** against the `test.dat` network with 100% accuracy.

### Validation Results

**Test Network:** `networks/test.dat`

- 14 species (including electron)
- 15 reactions
- 2 photoreactions

**Validation Tests Performed:**

| Test                   | Values Checked | Exact Matches | Result      |
| ---------------------- | -------------- | ------------- | ----------- |
| Species masses (no e-) | 13             | 13            | ✅ 100%     |
| Species charges (all)  | 14             | 14            | ✅ 100%     |
| GET commands           | 18             | 18            | ✅ 100%     |
| SUB tokens             | 2              | 2             | ✅ 100%     |
| REDUCE expressions     | 13             | 13            | ✅ 100%     |
| **TOTAL**              | **60**         | **60**        | **✅ 100%** |

**Key Findings:**

- ✅ All numeric values match to **full double precision** (16 significant digits)
- ✅ Electron correctly excluded from `*_ne` properties
- ✅ Index mapping correct (e.g., loop idx 1 → species H, skipping e- at network idx 1)
- ✅ GET lookups accurate for all species tested (H+, H, e-, CO, N2+, CH2)
- ✅ REDUCE generates correct sum expressions with all values present

**Example Verified Values:**

- H+ mass: `1.6737729999999998e-24` g ✅ EXACT
- H+ index: `0` ✅
- H+ charge: `+1` ✅
- Total mass (13 species, no e-): `3.273810e-22` g ✅

See `QUANTITATIVE_VALIDATION.md` for complete validation report.

---

## Language Support

The parser supports code generation for:

- **C**: Standard C syntax
- **C++**: Modern C++ (C++11/14/17/20)
- **Fortran**: Fortran 90/95/2003/2008

The parser automatically detects language from file extension or you can specify it explicitly.

---

## Performance Considerations

### Template Complexity

- Simple templates (< 1000 lines): < 1 second
- Complex templates with CSE: 1-5 seconds
- Large networks (1000+ reactions): 5-30 seconds

### Optimization Tips

1. **Use CSE for complex expressions** - Reduces both parsing time and runtime
2. **Minimize nested REPEAT blocks** - Each nesting level multiplies iterations
3. **Use `*_ne` variants** when electron not needed - Smaller arrays
4. **Cache parsed output** - Parse once, use many times

---

## Error Handling

### Common Errors

**1. Missing FOR in GET:**

```cpp
// $JAFF GET specie_idx H+  ❌ WRONG
// $JAFF GET specie_idx FOR H+  ✅ CORRECT
```

**2. REDUCE without variable in formula:**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
// total = $($ + $)$;  ❌ WRONG - no variable name
// total = $($specie_mass_ne$ + $specie_mass_ne$)$;  ✅ CORRECT
```

**3. Multiple $idx$ in single line (for some properties):**

```cpp
// $JAFF REPEAT idx IN specie_masses_ne
// mass[$idx$] = $specie_mass_ne$; comment[$idx$]  ❌ MAY FAIL
// mass[$idx$] = $specie_mass_ne$;  ✅ CORRECT
```

**4. Missing END:**

```cpp
// $JAFF SUB nspec
const int n = $nspec$;
// Missing END here causes errors
```

---

## Troubleshooting

### Template Not Expanding

**Check:**

1. Is `// $JAFF END` present?
2. Are tokens wrapped in `$...$`?
3. Is property name spelled correctly?

### Wrong Values Generated

**Check:**

1. Is network loaded correctly?
2. Are you using correct property name (`specie_mass` vs `specie_mass_ne`)?
3. Does entity exist in network (use HAS to check)?

### CSE Not Working

**Check:**

1. Did you declare CSE block first?
2. Is `cse` included in variable list: `REPEAT idx, cse IN rates`?
3. Is CSE enabled? (default: enabled)

---

## See Also

- [JAFF Types API](jaff-types.md) - IndexedValue and IndexedList type definitions
- [Codegen API](codegen.md) - Low-level code generation functions
- [Network API](network.md) - Chemical reaction network loading and processing
- [Elements API](elements.md) - Element extraction and matrices
- [Species API](species.md) - Species object properties
- [Reaction API](reaction.md) - Reaction object properties
- [User Guide: Code Generation](../user-guide/code-generation.md) - Step-by-step guide
- [Tutorial: Template Syntax](../tutorials/template-syntax.md) - Interactive tutorial
