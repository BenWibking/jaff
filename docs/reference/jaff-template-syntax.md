# JAFF Template Syntax Quick Reference

This page provides a quick reference for JAFF template syntax used in the file parser.

---

## Quick Start

JAFF templates use special directives embedded in code comments to generate repetitive code structures.

**Basic Pattern:**

```cpp
// $JAFF COMMAND arguments
code with $tokens$
// $JAFF END
```

---

## Commands Overview

| Command | Purpose                        | Example                                    |
| ------- | ------------------------------ | ------------------------------------------ |
| SUB     | Substitute scalar values       | `// $JAFF SUB nspec`                       |
| REPEAT  | Iterate over arrays/lists      | `// $JAFF REPEAT idx IN species`           |
| GET     | Retrieve entity properties     | `// $JAFF GET specie_idx FOR H+`           |
| HAS     | Check entity existence         | `// $JAFF HAS specie e-`                   |
| REDUCE  | Generate reduction expressions | `// $JAFF REDUCE mass IN specie_masses_ne` |
| END     | Terminate directive block      | `// $JAFF END`                             |

---

## REPLACE Directive

All commands (SUB, REPEAT, REDUCE, GET, HAS) support optional **REPLACE** directives for regex-based text replacement in the generated output.

**Syntax:**

```cpp
// $JAFF COMMAND args $[REPLACE pattern1 replacement1 REPLACE pattern2 replacement2 ...]$
code
// $JAFF END
```

**Key Features:**

- Replacements are applied **after** code generation
- Patterns use Python regex syntax (compiled with `re.compile()`)
- Multiple REPLACE directives can be chained
- Applied sequentially in order specified
- Supports capture groups and backreferences

**Example - Simple Replacement:**

```cpp
// $JAFF SUB nspec $[REPLACE const constexpr]$
const int NUM_SPECIES = $nspec$;
// $JAFF END
```

**Output:**

```cpp
constexpr int NUM_SPECIES = 14;  // 'const' replaced with 'constexpr'
```

**Example - Regex with Capture Groups:**

```cpp
// $JAFF REPEAT idx, specie IN species $[REPLACE H_(\d+) Hydrogen_\1 REPLACE He Helium]$
species[$idx$] = "$specie$";
// $JAFF END
```

**Output:**

```cpp
species[0] = "Hydrogen_1";  // H_1 -> Hydrogen_1 using capture group
species[1] = "Hydrogen_2";  // H_2 -> Hydrogen_2
species[2] = "Helium";      // He -> Helium
```

**Example - Multiple Replacements:**

```cpp
// $JAFF REPEAT idx IN specie_masses_ne $[REPLACE e- electron REPLACE \+ _plus]$
mass[$idx$] = $specie_mass_ne$;  // H+ becomes H_plus
// $JAFF END
```

**Notes:**

- REPLACE directives must be enclosed in dollar-brackets `$[...]$`
- Brackets must appear **after** all command arguments
- Pattern is a regex, replacement is a literal string (can use `\1`, `\2` for backreferences)
- Invalid regex patterns will raise `SyntaxError`
- Replacements persist only within the current command block (reset at END)

---

## SUB - Simple Substitution

Replace tokens with scalar values from the network.

**Syntax:**

```cpp
// $JAFF SUB token1, token2, ... $[REPLACE pattern replacement ...]$
code with $token1$ and $token2$
// $JAFF END
```

**With REPLACE:**

```cpp
// $JAFF SUB nspec, label $[REPLACE test production]$
const int NUM_SPECIES = $nspec$;  // "$label$" network
// $JAFF END
```

**Available Tokens:**

| Token        | Type   | Description            | Example      |
| ------------ | ------ | ---------------------- | ------------ |
| `$nspec$`    | int    | Number of species      | `14`         |
| `$nreact$`   | int    | Number of reactions    | `15`         |
| `$nelem$`    | int    | Number of elements     | `5`          |
| `$label$`    | string | Network label          | `"test"`     |
| `$filename$` | string | Template filename      | `"temp.cpp"` |
| `$e_idx$`    | int    | Electron species index | `1`          |

**Example:**

```cpp
// $JAFF SUB nspec, nreact
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
// $JAFF END
```

**Arithmetic:**

```cpp
// $JAFF SUB nspec
int array[$nspec+1$];     // Add
int last = $nspec-1$;     // Subtract
int double = $nspec*2$;   // Multiply
// $JAFF END
```

---

## REPEAT - Iteration

Iterate over network components or generate indexed expressions.

**Syntax:**

```cpp
// $JAFF REPEAT var1, var2 IN property [extras]
template with $var1$ and $var2$
// $JAFF END
```

Where `[extras]` can include: `SORT`, `CSE TRUE/FALSE`, `REPLACE pattern replacement ...`

**With REPLACE:**

```cpp
// $JAFF REPEAT idx, specie IN species $[REPLACE \+ _plus REPLACE - _minus]$
species[$idx$] = "$specie$";  // H+ becomes H_plus, e- becomes e_minus
// $JAFF END
```

---

### Simple List Properties

**Species Properties:**

| Property     | Variables   | Description           |
| ------------ | ----------- | --------------------- |
| `species`    | idx, specie | All species           |
| `species_ne` | idx, specie | Species (no electron) |

**Example:**

```cpp
// $JAFF REPEAT idx, specie IN species
names[$idx$] = "$specie$";
// $JAFF END
```

**Reaction Properties:**

| Property          | Variables     | Description            |
| ----------------- | ------------- | ---------------------- |
| `reactions`       | idx, reaction | All reactions          |
| `photo_reactions` | idx, reaction | Photoreactions only    |
| `reactants`       | idx, reactant | Reactants per reaction |
| `products`        | idx, product  | Products per reaction  |

**Other Properties:**

| Property   | Variables    | Description  |
| ---------- | ------------ | ------------ |
| `elements` | idx, element | All elements |

---

### Scalar Array Properties

**Species Masses:**

| Property                   | Variable          | Description            |
| -------------------------- | ----------------- | ---------------------- |
| `specie_masses`            | `specie_mass`     | All species masses     |
| `specie_masses_ne`         | `specie_mass_ne`  | Masses (no electron)   |
| `neutral_specie_masses`    | `neutral_mass`    | Neutral species masses |
| `neutral_specie_masses_ne` | `neutral_mass_ne` | Neutral masses (no e-) |
| `charged_specie_masses`    | `charged_mass`    | Charged species masses |
| `charged_specie_masses_ne` | `charged_mass_ne` | Charged masses (no e-) |

**Example:**

```cpp
// $JAFF REPEAT idx IN specie_masses_ne
const double mass_$idx$ = $specie_mass_ne$;
// $JAFF END
```

**Species Charges:**

| Property            | Variable           | Description            |
| ------------------- | ------------------ | ---------------------- |
| `specie_charges`    | `specie_charge`    | All charges            |
| `specie_charges_ne` | `specie_charge_ne` | Charges (no electron)  |
| `charge_truths`     | `charge_truth`     | 1 if charged, 0 if not |
| `charge_truths_ne`  | `charge_truth`     | Charge truths (no e-)  |

**Species Indices:**

| Property                    | Variable                  | Description             |
| --------------------------- | ------------------------- | ----------------------- |
| `specie_indices`            | `specie_index`            | All species indices     |
| `neutral_specie_indices`    | `neutral_specie_index`    | Neutral species indices |
| `neutral_specie_indices_ne` | `neutral_specie_index_ne` | Neutral indices (no e-) |
| `charged_specie_indices`    | `charged_specie_index`    | Charged species indices |
| `charged_specie_indices_ne` | `charged_specie_index_ne` | Charged indices (no e-) |

**Reaction Temperature Limits:**

| Property | Variable | Description       |
| -------- | -------- | ----------------- |
| `tmins`  | `tmin`   | Minimum temps (K) |
| `tmaxes` | `tmax`   | Maximum temps (K) |

---

### Expression Generators

These generate indexed code expressions (rates, ODEs, Jacobian).

| Property           | Variables      | Token               | Description          |
| ------------------ | -------------- | ------------------- | -------------------- |
| `rates`            | idx, rate, cse | `$rate$`            | Reaction rates       |
| `sorted_rates`     | idx, rate, cse | `$rate$`            | Sorted rates         |
| `odes`             | idx, ode, cse  | `$ode$`             | ODE right-hand sides |
| `rhses`            | idx, rhs, cse  | `$rhs$`             | RHS expressions      |
| `jacobian`         | idx, expr, cse | `$expr$`            | Jacobian elements    |
| `flux_expressions` | idx, flux_expr | `$flux_expression$` | Flux calculations    |
| `ode_expressions`  | idx, ode_expr  | `$ode_expression$`  | ODE expressions      |

**Example:**

```cpp
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

---

### Index Arithmetic

Use offsets for different indexing conventions:

```cpp
// $JAFF REPEAT idx IN species
! Fortran 1-based indexing
species($idx+1$) = "$specie$"
// $JAFF END
```

---

### Sorting

Sort items alphabetically:

```cpp
// $JAFF REPEAT idx, specie IN species SORT
sorted[$idx$] = "$specie$";
// $JAFF END
```

---

### Horizontal Mode (Inline Arrays)

Omit `idx` for comma-separated lists:

```cpp
// $JAFF REPEAT specie IN species
const char* names[] = {"$specie$"};
// $JAFF END
```

**Output:**

```cpp
const char* names[] = {"H+", "e-", "H", "C"};
```

---

## GET - Retrieve Properties

Get properties for a specific named entity.

**Syntax:**

```cpp
// $JAFF GET property1, property2 FOR entity_name $[REPLACE pattern replacement ...]$
code with $property1$ and $property2$
// $JAFF END
```

**Note:** The `FOR` keyword is **required**.

**With REPLACE:**

```cpp
// $JAFF GET specie_idx FOR H+ $[REPLACE 0 zero]$
const int idx = $specie_idx$;  // 0 becomes zero
// $JAFF END
```

**Species Properties:**

| Property        | Type   | Description  |
| --------------- | ------ | ------------ |
| `specie_idx`    | int    | Index        |
| `specie_mass`   | float  | Mass (g)     |
| `specie_charge` | int    | Charge       |
| `specie_latex`  | string | LaTeX format |

**Example:**

```cpp
// $JAFF GET specie_idx, specie_mass, specie_charge FOR H+
const int h_idx = $specie_idx$;        // 0
const double h_mass = $specie_mass$;   // 1.673773e-24
const int h_charge = $specie_charge$;  // 1
// $JAFF END
```

**Reaction Properties:**

| Property            | Type   | Description     |
| ------------------- | ------ | --------------- |
| `reaction_idx`      | int    | Index           |
| `reaction_tmin`     | float  | Min temp (K)    |
| `reaction_tmax`     | float  | Max temp (K)    |
| `reaction_verbatim` | string | Original string |

**Element Properties:**

| Property      | Type | Description |
| ------------- | ---- | ----------- |
| `element_idx` | int  | Index       |

---

## HAS - Check Existence

Check if an entity exists (returns 1 or 0).

**Syntax:**

```cpp
// $JAFF HAS entity_type entity_name $[REPLACE pattern replacement ...]$
int result = $entity_type$;
// $JAFF END
```

**Entity Types:** `specie`, `reaction`, `element`

**With REPLACE:**

```cpp
// $JAFF HAS specie e- $[REPLACE 1 true REPLACE 0 false]$
const bool has_electron = $specie$;  // 1 becomes true
// $JAFF END
```

**Example:**

```cpp
// $JAFF HAS specie e-
const int has_electron = $specie$;  // 1 if exists, 0 otherwise
// $JAFF END

// Use in conditional compilation
#if has_electron
    compute_ionization();
#endif
```

---

## REDUCE - Array Reduction

Generate expressions that combine array elements.

**Syntax:**

```cpp
// $JAFF REDUCE variable_name IN property_name $[REPLACE pattern replacement ...]$
result = $($variable_name$ OPERATION $variable_name$)$;
// $JAFF END
```

**Important:** The formula `$(...$)` **must** include the variable name.

**With REPLACE:**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne $[REPLACE \+ plus]$
const double total = $($specie_mass_ne$ + $specie_mass_ne$)$;  // + becomes plus
// $JAFF END
```

**Available Properties:**

| Property                   | Variable                 | Description      |
| -------------------------- | ------------------------ | ---------------- |
| `specie_masses_ne`         | `specie_mass_ne`         | Masses (no e-)   |
| `specie_charges_ne`        | `specie_charge_ne`       | Charges (no e-)  |
| `neutral_specie_masses_ne` | `neutral_specie_mass_ne` | Neutral masses   |
| `charged_specie_masses_ne` | `charged_specie_mass_ne` | Charged masses   |
| `tmins`                    | `tmin`                   | Min temperatures |
| `tmaxes`                   | `tmax`                   | Max temperatures |

**Example - Sum:**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
const double total = $($specie_mass_ne$ + $specie_mass_ne$)$;
// $JAFF END
```

**Output:**

```cpp
const double total = 1.673773e-24 + 1.673773e-24 + 1.994473e-23 + ...;
```

**Example - Product:**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
const double product = $($specie_mass_ne$ * $specie_mass_ne$)$;
// $JAFF END
```

**Example - Array:**

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
double masses[] = {$($specie_mass_ne$, $specie_mass_ne$)$};
// $JAFF END
```

---

## CSE - Common Subexpression Elimination

Extract common subexpressions to temporary variables for efficiency.

**Without CSE:**

```cpp
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output:**

```cpp
rate[0] = k[0] * exp(-100/T) * n[0] * n[1];
rate[1] = k[1] * exp(-100/T) * n[2] * n[3];  // exp() repeated!
```

**With CSE:**

```cpp
// CSE declaration
// $JAFF REPEAT idx, cse IN rates
double cse[$idx$] = $cse$;
// $JAFF END

// Use CSE in rates
// $JAFF REPEAT idx IN rates
rate[$idx$] = $rate$;
// $JAFF END
```

**Output:**

```cpp
// CSE temporaries
double cse[0] = exp(-100/T);
double cse[1] = exp(-200/T);

// Rates using CSE
rate[0] = k[0] * cse[0] * n[0] * n[1];
rate[1] = k[1] * cse[0] * n[2] * n[3];  // Reuses cse[0]!
```

**Control CSE per block:**

```cpp
// $JAFF REPEAT idx IN rates CSE FALSE
rate[$idx$] = $rate$;  // CSE disabled
// $JAFF END
```

---

## Complete Examples

### C++ Example

```cpp
#include <vector>

// $JAFF SUB nspec, nreact, label
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
const char* NETWORK = "$label$";
// $JAFF END

// $JAFF REPEAT idx, specie IN species
const char* SPECIES[] = {"$specie$"};
// $JAFF END

// $JAFF REPEAT idx IN specie_masses_ne
const double MASSES[] = {$specie_mass_ne$};
// $JAFF END

// $JAFF GET specie_idx FOR H+
const int H_PLUS = $specie_idx$;
// $JAFF END

void compute_rates(double* rate, const double* n, double T) {
    // $JAFF REPEAT idx IN rates
    rate[$idx$] = $rate$;
    // $JAFF END
}

void compute_odes(double* dy, const double* y, const double* rate) {
    // $JAFF REPEAT idx IN odes
    dy[$idx$] = $ode$;
    // $JAFF END
}
```

### Fortran Example

```fortran
module network
    implicit none

    ! $JAFF SUB nspec, nreact
    integer, parameter :: NUM_SPECIES = $nspec$
    integer, parameter :: NUM_REACTIONS = $nreact$
    ! $JAFF END

    ! $JAFF REPEAT idx IN specie_masses_ne
    real(8), parameter :: MASSES($nspec$) = (/ $specie_mass_ne$ /)
    ! $JAFF END

contains

    subroutine compute_rates(rate, n, T)
        real(8), intent(out) :: rate(NUM_REACTIONS)
        real(8), intent(in) :: n(NUM_SPECIES)
        real(8), intent(in) :: T

        ! $JAFF REPEAT idx IN rates
        rate($idx+1$) = $rate$
        ! $JAFF END
    end subroutine

end module
```

---

## Common Patterns

### Species Loop

```cpp
// $JAFF REPEAT idx, specie IN species
// Process: $specie$ at index $idx$
// $JAFF END
```

### Reaction Loop

```cpp
// $JAFF REPEAT idx, reaction IN reactions
// Reaction $idx$: $reaction$
// $JAFF END
```

### Masses Array

```cpp
// $JAFF REPEAT idx IN specie_masses_ne
double masses[$idx$] = $specie_mass_ne$;
// $JAFF END
```

### Conditional Code

```cpp
// $JAFF HAS specie e-
#if $specie$
    // Electron-dependent code
#endif
// $JAFF END
```

### Total Mass

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
double total = $($specie_mass_ne$ + $specie_mass_ne$)$;
// $JAFF END
```

---

## Common Errors

### ❌ Missing FOR in GET

```cpp
// $JAFF GET specie_idx H+  // WRONG!
// $JAFF GET specie_idx FOR H+  // CORRECT
```

### ❌ REDUCE without variable

```cpp
// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
total = $($ + $)$;  // WRONG - no variable name!
// $JAFF END

// $JAFF REDUCE specie_mass_ne IN specie_masses_ne
total = $($specie_mass_ne$ + $specie_mass_ne$)$;  // CORRECT
// $JAFF END
```

### ❌ Missing END

```cpp
// $JAFF SUB nspec
const int n = $nspec$;
// Missing END causes errors!
```

### ❌ Invalid REPLACE Syntax

```cpp
// $JAFF SUB nspec $[REPLACE pattern]$  // WRONG - missing replacement string
// $JAFF SUB nspec $[REPLACE [invalid( regex]$  // WRONG - invalid regex pattern
// $JAFF SUB nspec REPLACE old new  // WRONG - missing brackets
```

### ❌ REPLACE in Wrong Position

```cpp
// $JAFF SUB $[REPLACE old new]$ nspec  // WRONG - dollar-brackets must be after arguments
// $JAFF SUB nspec $[REPLACE old new]$  // CORRECT
```

### ❌ Multiple idx in single line (for some properties)

```cpp
// $JAFF REPEAT idx IN specie_masses_ne
mass[$idx$] = $specie_mass_ne$; comment[$idx$]  // May fail
// $JAFF END
```

---

## Property Naming Convention

Properties ending in `_ne` exclude the electron species:

- `species` → all species (including e-)
- `species_ne` → all species except e-
- `specie_masses` → all masses
- `specie_masses_ne` → masses without electron

---

## See Also

- [File Parser API](../api/file-parser.md) - Complete API reference
- [Codegen API](../api/codegen.md) - Code generation functions
- [Network API](../api/network.md) - Network object reference
