# File Parser API Reference

The `file_parser` module provides the core template parsing functionality for JAFF code generation.

## Overview

The file parser processes template files containing JAFF directives and generates code for chemical reaction networks in multiple programming languages (C, C++, Fortran). It supports a sophisticated template syntax with commands for iteration, substitution, and conditional logic.

## Module: `jaff.file_parser`

::: jaff.file_parser
    options:
      show_root_heading: true
      show_source: true
      heading_level: 2

## Classes

### Fileparser

::: jaff.file_parser.Fileparser
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - parse_file
      heading_level: 3

#### Methods

##### parse_file()

Parse the entire template file and generate code.

**Returns**: `str` - Generated code with all JAFF directives expanded

**Example**:
```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

net = Network("networks/react_COthin")
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()
print(output)
```

### TypedDict Classes

#### IdxSpanResult

::: jaff.file_parser.IdxSpanResult
    options:
      show_root_heading: true
      heading_level: 4

Result structure for index span detection.

**Attributes**:

- `offset` (list[int]): List of integer offsets for each index (e.g., from `$idx+2$`)
- `span` (list[tuple[int, int]]): List of tuples containing (start, end) positions of each index token

#### CommandProps

::: jaff.file_parser.CommandProps
    options:
      show_root_heading: true
      heading_level: 4

Properties defining a JAFF command.

**Attributes**:

- `func` (Callable[..., Any]): Callable function that handles the command
- `props` (dict[str, dict[str, Any]]): Dictionary mapping property names to their function handlers

#### CseProps

::: jaff.file_parser.CseProps
    options:
      show_root_heading: true
      heading_level: 4

Common Subexpression Elimination (CSE) properties.

**Attributes**:

- `parsed` (bool): Whether CSE declaration has been parsed
- `prefix` (str): Prefix string for CSE variable definitions
- `var` (str): Variable name used for CSE storage

## JAFF Template Syntax

### Supported Commands

The file parser recognizes five main JAFF commands:

#### SUB - Token Substitution

Substitute template tokens with values from the network.

**Syntax**:
```cpp
// $JAFF SUB token1, token2, ...
code with $token1$ and $token2$
// $JAFF END
```

**Available Tokens**:

- `$nspec$` - Number of species
- `$nreact$` - Number of reactions
- `$nelem$` - Number of elements
- `$label$` - Network label
- `$filename$` - Template filename
- `$filepath$` - Full template path
- `$dedt$` - Time derivative variable name
- `$e_idx$` - Index of electron species

**Example**:
```cpp
// $JAFF SUB nspec, nreact
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
// $JAFF END
```

**Output** (for a network with 50 species and 200 reactions):
```cpp
const int NUM_SPECIES = 50;
const int NUM_REACTIONS = 200;
```

#### REPEAT - Iteration

Iterate over network components or generate code expressions.

**Syntax for Iterable Properties**:
```cpp
// $JAFF REPEAT var1, var2 IN property [SORT]
template line with $var1$ and $var2$
// $JAFF END
```

**Syntax for Non-Iterable Properties**:
```cpp
// $JAFF REPEAT idx [, cse] IN property
template line with $idx$ and $property_token$
// $JAFF END
```

**Iterable Properties**:

| Property | Variables | Description |
|----------|-----------|-------------|
| `species` | idx, specie | All species names |
| `reactions` | idx, reaction | All reactions |
| `elements` | idx, element | All elements |
| `masses` | idx, mass | Species masses |
| `charges` | idx, charge | Species charges |
| `reactants` | idx, reactant | Reaction reactants |
| `products` | idx, product | Reaction products |
| `tmins` | idx, tmin | Minimum temperatures |
| `tmaxes` | idx, tmax | Maximum temperatures |

**Non-Iterable Properties**:

| Property | Variables | Token | Description |
|----------|-----------|-------|-------------|
| `rates` | idx, rate, cse | `$rate$` | Reaction rate expressions |
| `odes` | idx, ode, cse | `$ode$` | ODE right-hand sides |
| `rhses` | idx, rhs, cse | `$rhs$` | RHS expressions |
| `jacobian` | idx, expr, cse | `$expr$` | Jacobian matrix elements |
| `flux_expressions` | idx, flux_expression | `$flux_expression$` | Flux calculations |
| `ode_expressions` | idx, ode_expression | `$ode_expression$` | ODE expressions |

**Example - Iterable**:
```cpp
// $JAFF REPEAT idx, specie IN species
species_names[$idx$] = "$specie$";
// $JAFF END
```

**Output**:
```cpp
species_names[0] = "H";
species_names[1] = "H2";
species_names[2] = "CO";
```

**Example - Non-Iterable**:
```cpp
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output**:
```cpp
rate[0] = k[0] * n[0] * n[1];
rate[1] = k[1] * n[2] * n[3];
```

**Index Offsets**:
```cpp
// $JAFF REPEAT idx, specie IN species
// Index with offset: $idx+1$ starts from 1 instead of 0
fortran_index[$idx+1$] = "$specie$";
// $JAFF END
```

**Sorting**:
```cpp
// $JAFF REPEAT idx, specie IN species SORT
// Species will be alphabetically sorted
species_names[$idx$] = "$specie$";
// $JAFF END
```

**Horizontal Mode** (inline arrays):
```cpp
// $JAFF REPEAT specie IN species
const char* names[] = {"$specie$"};
// $JAFF END
```

**Output**:
```cpp
const char* names[] = {"H", "H2", "CO", "OH"};
```

#### GET - Retrieve Properties

Get specific properties for named entities.

**Syntax**:
```cpp
// $JAFF GET property1, property2 FOR entity_name
code with $property1$ and $property2$
// $JAFF END
```

**Available Properties**:

- `element_idx` - Index of an element
- `specie_idx` - Index of a species
- `reaction_idx` - Index of a reaction
- `specie_mass` - Mass of a species (amu)
- `specie_charge` - Charge of a species
- `specie_latex` - LaTeX representation of a species
- `reaction_tmin` - Minimum temperature for a reaction
- `reaction_tmax` - Maximum temperature for a reaction
- `reaction_verbatim` - Original reaction string

**Example**:
```cpp
// $JAFF GET specie_idx, specie_mass FOR CO
const int co_index = $specie_idx$;
const double co_mass = $specie_mass$;
// $JAFF END
```

**Output**:
```cpp
const int co_index = 15;
const double co_mass = 28.01;
```

#### HAS - Check Existence

Check if an entity exists in the network (returns 1 or 0).

**Syntax**:
```cpp
// $JAFF HAS entity_type entity_name
int result = $entity_type$;
// $JAFF END
```

**Entity Types**:

- `specie` - Check if a species exists
- `reaction` - Check if a reaction exists
- `element` - Check if an element exists

**Example**:
```cpp
// $JAFF HAS specie e-
const int has_electrons = $specie$;
// $JAFF END
```

**Output**:
```cpp
const int has_electrons = 1;  // 1 if exists, 0 otherwise
```

#### END - Terminate Block

Mark the end of a JAFF directive block.

**Syntax**:
```cpp
// $JAFF END
```

## Common Subexpression Elimination (CSE)

CSE optimization reduces redundant calculations in generated expressions.

**Example without CSE**:
```cpp
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output**:
```cpp
rate[0] = k[0] * exp(-100.0/T) * n[0] * n[1];
rate[1] = k[1] * exp(-100.0/T) * n[2] * n[3];
rate[2] = k[2] * exp(-100.0/T) * n[4] * n[5];
```

**Example with CSE**:
```cpp
// $JAFF REPEAT idx, cse IN rates
double cse[$idx$] = $cse$;
// $JAFF END

// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output**:
```cpp
double cse[0] = exp(-100.0/T);
double cse[1] = exp(-200.0/T);

rate[0] = k[0] * cse[0] * n[0] * n[1];
rate[1] = k[1] * cse[0] * n[2] * n[3];
rate[2] = k[2] * cse[1] * n[4] * n[5];
```

## Advanced Features

### 2D Lists

For nested structures like element density matrices:

```cpp
// $JAFF REPEAT idx, element IN element_density_matrix
int matrix[$idx$][] = {$element$};
// $JAFF END
```

**Output**:
```cpp
int matrix[0][] = {1, 0, 1, 2};  // C in each species
int matrix[1][] = {0, 2, 0, 4};  // H in each species
int matrix[2][] = {1, 0, 1, 1};  // O in each species
```

### Arithmetic Operations

Apply arithmetic to token values:

```cpp
// $JAFF SUB nspec
int array[$nspec+1$];  // Add 1 to nspec
int offset = $nspec-1$;  // Subtract 1
int doubled = $nspec*2$;  // Multiply by 2
// $JAFF END
```

## Usage Examples

### Complete Template Example

```cpp
// template.cpp
#include <vector>

// $JAFF SUB nspec, nreact
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
// $JAFF END

// Species names
// $JAFF REPEAT idx, specie IN species
const char* species_names[$idx$] = "$specie$";
// $JAFF END

// Calculate reaction rates
void compute_rates(double* rate, const double* n, const double* k, double T) {
    // $JAFF REPEAT idx IN rates
    rate[$idx$] = $rate$;
    // $JAFF END
}

// Calculate ODEs
void compute_odes(double* dydt, const double* y, const double* rate) {
    // $JAFF REPEAT idx IN odes
    dydt[$idx$] = $ode$;
    // $JAFF END
}
```

### Python Usage

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network
net = Network("networks/react_COthin")

# Parse template
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# Write output
with open("generated.cpp", "w") as f:
    f.write(output)
```

## See Also

- [Code Generation Guide](../user-guide/code-generation.md) - Detailed guide on generating code
- [Template Syntax Reference](../reference/jaff-commands.md) - Complete JAFF command reference
- [Codegen API](codegen.md) - Low-level code generation API
- [Elements API](elements.md) - Element extraction and matrices
