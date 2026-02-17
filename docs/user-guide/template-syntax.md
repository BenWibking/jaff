# Template Syntax

Complete guide to JAFF's template language for custom code generation.

## Overview

JAFF templates allow you to embed commands in any text file to generate custom code. Templates are processed by the `Fileparser` class, which replaces JAFF commands with network-specific content.

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network
net = Network("networks/react_COthin")

# Process template
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# Save result
with open("output.cpp", "w") as f:
    f.write(output)
```

## Template Commands

JAFF templates use special commands enclosed in `$JAFF` markers:

```
$JAFF COMMAND arguments$
```

### Command Types

| Command  | Purpose                        | Example                                  |
| -------- | ------------------------------ | ---------------------------------------- |
| `SUB`    | Substitute a single value      | `$JAFF SUB nspec$`                       |
| `REPEAT` | Iterate over a collection      | `$JAFF REPEAT idx IN rates$`             |
| `GET`    | Access object properties       | `$JAFF GET species[0].name$`             |
| `HAS`    | Conditional inclusion          | `$JAFF HAS photoreactions$`              |
| `REDUCE` | Generate reduction expressions | `$JAFF REDUCE mass IN specie_masses_ne$` |
| `END`    | End a block                    | `$JAFF END$`                             |

## REPLACE Directive

All JAFF commands support optional **REPLACE** directives for regex-based text replacement in generated output.

### Syntax

**Syntax:**

```
$JAFF COMMAND arguments $[REPLACE pattern1 replacement1 REPLACE pattern2 replacement2 ...]$
```

### Key Features

- REPLACE directives must be enclosed in dollar-brackets `$[...]$`
- Replacements applied **after** code generation
- Patterns use Python regex syntax
- Supports capture groups and backreferences (`\1`, `\2`, etc.)
- Multiple REPLACE directives can be chained
- Applied sequentially in order specified
- Automatically reset at `$JAFF END$`

### Basic Example

```cpp
// Template
$JAFF SUB nspec $[REPLACE const constexpr]$
const int NUM_SPECIES = $nspec$;
$JAFF END$

// Output
constexpr int NUM_SPECIES = 14;
```

### Regex with Capture Groups

```cpp
// Template
$JAFF REPEAT idx, specie IN species $[REPLACE H_(\d+) Hydrogen_\1 REPLACE He Helium]$
species[$idx$] = "$specie$";
$JAFF END$

// Output
species[0] = "Hydrogen_1";  // H_1 -> Hydrogen_1
species[1] = "Hydrogen_2";  // H_2 -> Hydrogen_2
species[2] = "Helium";      // He -> Helium
```

### Multiple Replacements

```cpp
// Template
$JAFF REPEAT idx, specie IN species $[REPLACE \+ _plus REPLACE - _minus]$
species[$idx$] = "$specie$";
$JAFF END$

// Output
species[0] = "H_plus";   // H+ -> H_plus
species[1] = "e_minus";  // e- -> e_minus
```

### Common Use Cases

- **Sanitize names**: Convert special characters (`+`, `-`) to valid identifiers
- **Replace keywords**: Change language keywords (e.g., `const` to `constexpr`)
- **Add prefixes/suffixes**: Transform identifiers with patterns
- **Normalize formats**: Convert naming conventions

### Important Notes

1. **REPLACE directives must be enclosed in dollar-brackets**
    - ✅ Correct: `$JAFF SUB nspec $[REPLACE old new]$`
    - ❌ Wrong: `$JAFF SUB nspec REPLACE old new$` (missing dollar-brackets)
    - ❌ Wrong: `$JAFF SUB $[REPLACE old new]$ nspec$` (dollar-brackets must be after arguments)

2. **Each REPLACE needs both pattern and replacement**
    - ✅ Correct: `$[REPLACE pattern replacement]$`
    - ❌ Wrong: `$[REPLACE pattern]$` (raises SyntaxError)

3. **Invalid regex raises error**
    - Invalid: `$[REPLACE [invalid( bad]$`
    - Error: `SyntaxError: Invalid regex pattern...`

4. **Replacements are block-scoped**
    - Reset at `$JAFF END$`
    - Don't carry over to next block

## SUB Command

Substitute a single value from the network.

### Syntax

```
$JAFF SUB variable$
value_here
$JAFF END$
```

### Available Variables

**Network Metadata:**

- `nspec` - Number of species
- `nreact` - Number of reactions
- `label` - Network label/name

**Example:**

```cpp
// Template
const int NUM_SPECIES = $JAFF SUB nspec$
$nspec$
$JAFF END$;

// Output
const int NUM_SPECIES = 35;
```

### Multiple Substitutions

```cpp
// Template
$JAFF SUB nspec$
const int NSPEC = $nspec$;
const int NREACT = $nreact$;
const int TOTAL = $nspec$ + $nreact$;
$JAFF END$

// Output
const int NSPEC = 35;
const int NREACT = 127;
const int TOTAL = 35 + 127;
```

## REPEAT Command

Iterate over collections in the network.

### Syntax

```
$JAFF REPEAT variable IN collection$
template using $variable$
$JAFF END$
```

### Collections

**Species Collections:**

- `species` - All species (iterate with index, species object)
- `species_names` - Species names only

**Reaction Collections:**

- `reactions` - All reactions (iterate with index, reaction object)
- `rates` - Rate expressions
- `odes` - ODE expressions
- `fluxes` - Flux expressions

**Other:**

- `elements` - Chemical elements in network

### Simple Iteration

```cpp
// Template
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;
$JAFF END$

// Output
k[0] = 1.2e-10 * pow(tgas/300, 0.5);
k[1] = 3.4e-11 * exp(-500/tgas);
k[2] = 5.6e-12;
```

### Multiple Variables

```cpp
// Template
$JAFF REPEAT idx, species IN species$
// Species $idx$: $species$
$JAFF END$

// Output
// Species 0: H
// Species 1: H2
// Species 2: O
```

### Nested Loops

```cpp
// Template
$JAFF REPEAT i, sp1 IN species$
$JAFF REPEAT j, sp2 IN species$
matrix[$i$][$j$] = compute($sp1$, $sp2$);
$JAFF END$
$JAFF END$

// Output
matrix[0][0] = compute(H, H);
matrix[0][1] = compute(H, H2);
matrix[1][0] = compute(H2, H);
matrix[1][1] = compute(H2, H2);
```

## Token Substitution

Within REPEAT blocks, use tokens to access data:

### Rate Tokens

```cpp
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;  // $reaction$
$JAFF END$
```

**Available tokens:**

- `$idx$` - Reaction index
- `$rate$` - Rate expression
- `$reaction$` - Reaction verbatim string

### ODE Tokens

```cpp
$JAFF REPEAT idx IN odes$
dydt[$idx$] = $ode$;
$JAFF END$
```

**Available tokens:**

- `$idx$` - Species index
- `$ode$` - ODE expression for species

### Species Tokens

```cpp
$JAFF REPEAT idx, species IN species$
names[$idx$] = "$species$";
mass[$idx$] = $mass$;
charge[$idx$] = $charge$;
$JAFF END$
```

**Available tokens:**

- `$idx$` - Species index
- `$species$` - Species name
- `$mass$` - Species mass
- `$charge$` - Species charge

## GET Command

Access specific object properties.

### Syntax

```
$JAFF GET object.property$
```

### Examples

```cpp
// Get first species name
$JAFF GET species[0].name$

// Get third reaction verbatim
$JAFF GET reactions[2].verbatim$

// Get network label
$JAFF GET net.label$
```

## HAS Command

Conditional inclusion based on network features.

### Syntax

```
$JAFF HAS feature$
content if feature exists
$JAFF END$
```

### Features

```cpp
// Include if network has photoreactions
$JAFF HAS photoreactions$
void compute_photo_rates(double* k_photo) {
    // Photo-reaction code
}
$JAFF END$

// Include if network has dust chemistry
$JAFF HAS dust$
void compute_grain_chemistry(double* rates) {
    // Dust chemistry code
}
$JAFF END$
```

## Index Offsets

Control array indexing with offset specifiers.

### Syntax

Add offset to indices using `+N` or `-N`:

```cpp
// Start at 0 (default)
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;
$JAFF END$

// Start at 1 (Fortran-style)
$JAFF REPEAT idx+1 IN rates$
k($idx$) = $rate$
$JAFF END$

// Custom offset
$JAFF REPEAT idx+5 IN rates$
k[$idx$] = $rate$;
$JAFF END$
```

### Example

```fortran
! Template (Fortran)
$JAFF REPEAT idx+1 IN rates$
k($idx$) = $rate$
$JAFF END$

! Output (1-based)
k(1) = 1.2d-10 * (tgas/300.d0)**0.5d0
k(2) = 3.4d-11 * dexp(-500.d0/tgas)
```

## Arithmetic Operations

Perform arithmetic on indices:

```cpp
// Addition
$JAFF REPEAT idx IN rates$
k[$idx+1$] = $rate$;  // Offset each index by 1
$JAFF END$

// Subtraction
$JAFF REPEAT idx IN rates$
k[$idx-1$] = $rate$;  // Offset each index by -1
$JAFF END$

// Multiplication
$JAFF REPEAT idx IN rates$
k[$idx*2$] = $rate$;  // Double each index
$JAFF END$
```

## CSE (Common Subexpression Elimination)

Enable CSE optimization in templates.

### Syntax

```
$JAFF REPEAT idx IN rates CSE$
template
$JAFF END$
```

### Example

```cpp
// Template with CSE
void compute_rates(double* k, double tgas) {
$JAFF REPEAT idx IN rates CSE$
    k[$idx$] = $rate$;
$JAFF END$
}

// Output
void compute_rates(double* k, double tgas) {
    // Common subexpressions
    const double x0 = sqrt(tgas);
    const double x1 = pow(tgas/300, 0.5);

    // Rate calculations
    k[0] = 1.2e-10 * x1;
    k[1] = 3.4e-11 * x0 * exp(-500/tgas);
    k[2] = 5.6e-12 * x0 * x1;
}
```

## Layout Modes

Control how content is generated.

### Horizontal Mode (Default)

Each iteration on same line:

```cpp
$JAFF REPEAT idx, sp IN species$
$idx$,
$JAFF END$

// Output
0, 1, 2, 3, 4,
```

### Vertical Mode

Each iteration on new line:

```cpp
$JAFF REPEAT idx, sp IN species VERTICAL$
species[$idx$] = "$sp$";
$JAFF END$

// Output
species[0] = "H";
species[1] = "H2";
species[2] = "O";
```

## Complete Examples

### Example 1: C++ Header File

```cpp
// Template: chemistry.h
#ifndef CHEMISTRY_H
#define CHEMISTRY_H

namespace chemistry {

// Species indices
$JAFF REPEAT idx, species IN species$
constexpr int idx_$species$ = $idx$;
$JAFF END$

// Counts
$JAFF SUB nspec$
constexpr int NUM_SPECIES = $nspec$;
constexpr int NUM_REACTIONS = $nreact$;
$JAFF END$

// Rate calculations
void compute_rates(double* k, double tgas) {
$JAFF REPEAT idx IN rates CSE$
    k[$idx$] = $rate$;  // $reaction$
$JAFF END$
}

} // namespace chemistry

#endif
```

### Example 2: Fortran Module

```fortran
! Template: chemistry.f90
module chemistry
  implicit none

  ! Species indices
$JAFF REPEAT idx+1, species IN species$
  integer, parameter :: idx_$species$ = $idx$
$JAFF END$

  ! Counts
$JAFF SUB nspec$
  integer, parameter :: nspec = $nspec$
  integer, parameter :: nreact = $nreact$
$JAFF END$

contains

  subroutine compute_rates(k, tgas)
    real(8), intent(out) :: k(nreact)
    real(8), intent(in) :: tgas

$JAFF REPEAT idx+1 IN rates$
    k($idx$) = $rate$
$JAFF END$
  end subroutine compute_rates

end module chemistry
```

### Example 3: Python Module

```python
# Template: chemistry.py
import numpy as np
from math import sqrt, exp, log

# Species indices
$JAFF REPEAT idx, species IN species$
idx_$species$ = $idx$
$JAFF END$

# Counts
$JAFF SUB nspec$
NUM_SPECIES = $nspec$
NUM_REACTIONS = $nreact$
$JAFF END$

def compute_rates(tgas):
    """Compute reaction rate coefficients."""
    k = np.zeros(NUM_REACTIONS)
$JAFF REPEAT idx IN rates CSE$
    k[$idx$] = $rate$  # $reaction$
$JAFF END$
    return k

def compute_odes(y, k):
    """Compute ODE right-hand side."""
    dydt = np.zeros(NUM_SPECIES)
$JAFF REPEAT idx IN odes$
    dydt[$idx$] = $ode$
$JAFF END$
    return dydt
```

### Example 4: Species Information Table

```cpp
// Template: species_data.cpp
struct SpeciesData {
    const char* name;
    double mass;
    int charge;
};

SpeciesData species_table[] = {
$JAFF REPEAT idx, species IN species$
    {"$species$", $mass$, $charge$},  // [$idx$]
$JAFF END$
};
```

### Example 5: Reaction Names

```cpp
// Template: reaction_names.h
const char* reaction_names[] = {
$JAFF REPEAT idx, reaction IN reactions$
    "$reaction$",  // [$idx$]
$JAFF END$
};
```

## Best Practices

### 1. Use Descriptive Comments

```cpp
// Good
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;  // $reaction$
$JAFF END$

// Better - more context
$JAFF REPEAT idx IN rates$
// Reaction $idx$: $reaction$
k[$idx$] = $rate$;
$JAFF END$
```

### 2. Enable CSE for Performance

```cpp
// Always use CSE for rate calculations
$JAFF REPEAT idx IN rates CSE$
k[$idx$] = $rate$;
$JAFF END$
```

### 3. Match Language Conventions

```fortran
! Fortran: 1-based indexing
$JAFF REPEAT idx+1 IN rates$
k($idx$) = $rate$
$JAFF END$
```

```cpp
// C++: 0-based indexing
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;
$JAFF END$
```

### 4. Organize Templates

```
templates/
├── cpp/
│   ├── header.h
│   ├── rates.cpp
│   └── odes.cpp
├── fortran/
│   ├── module.f90
│   └── subroutines.f90
└── python/
    └── chemistry.py
```

### 5. Test Templates on Small Networks

```python
# Test on small network first
net = Network("networks/test_small.dat")
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()
print(output)  # Check output before using on large network
```

## Advanced Techniques

### Conditional Code Generation

```cpp
$JAFF HAS photoreactions$
// Photoreaction handling
void compute_photo_rates(double* k_photo, double av) {
$JAFF REPEAT idx IN photo_rates$
    k_photo[$idx$] = photo_rate($idx$, av);
$JAFF END$
}
$JAFF END$
```

### Multi-Dimensional Arrays

```cpp
// 2D array initialization
double jac[NSPEC][NSPEC] = {
$JAFF REPEAT i IN species$
    {
$JAFF REPEAT j IN species$
        0.0,
$JAFF END$
    },
$JAFF END$
};
```

### Custom Formatting

```python
# Pretty-print species table
$JAFF REPEAT idx, species IN species$
print(f"{$idx$:3d}: {$species$:10s}  mass={$mass$:8.2f}  charge={$charge$:+2d}")
$JAFF END$
```

## Troubleshooting

### Issue: "Command not recognized"

**Cause:** Typo in command name

```cpp
// Wrong
$JAFF REPEATE idx IN rates$

// Correct
$JAFF REPEAT idx IN rates$
```

### Issue: "Unmatched END"

**Cause:** Missing or extra `$JAFF END$`

```cpp
// Wrong - missing END
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;

// Correct
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;
$JAFF END$
```

### Issue: "Token not found"

**Cause:** Using wrong token for collection

```cpp
// Wrong - $ode$ not available in rates
$JAFF REPEAT idx IN rates$
k[$idx$] = $ode$;
$JAFF END$

// Correct
$JAFF REPEAT idx IN rates$
k[$idx$] = $rate$;
$JAFF END$
```

## See Also

- [File Parser API](../api/file-parser.md) - Complete API reference
- [Code Generation](code-generation.md) - Codegen class usage
- [Tutorial: Custom Templates](../tutorials/custom-templates.md) - Hands-on guide
- [Template Variables Reference](../reference/template-variables.md) - All available variables

---

**Next:** Explore [Tutorial: Custom Templates](../tutorials/custom-templates.md).
