# Network File Formats

Comprehensive guide to all network file formats supported by JAFF.

## Overview

JAFF supports multiple file formats used in astrochemistry. Each format has its own syntax and conventions, but JAFF automatically detects and parses them correctly.

**Supported Formats:**

| Format | Extension | Origin | Auto-detect |
|--------|-----------|--------|-------------|
| JAFF | `.dat` | Native format | Arrow syntax `->` |
| KROME | `.dat` | KROME code | `@format:` line |
| KIDA | `.dat` | KIDA database | Colon separators |
| UDFA | `.dat` | UMIST database | Colon format |
| PRIZMO | `.dat` | PRIZMO code | `VARIABLES{` block |
| UCL_CHEM | `.dat` | UCL_CHEM | `,NAN,` markers |

## JAFF Format

JAFF's native format designed for readability and simplicity.

### Syntax

```text
# Comments start with #
Reactant1 + Reactant2 -> Product1 + Product2, rate_expression
```

### Features

- **Simple syntax**: Human-readable arrow notation
- **Flexible rates**: Any SymPy-compatible expression
- **Comments**: Lines starting with `#`
- **Auto-detection**: Species automatically extracted from reactions

### Example

```text
# Simple CO chemistry network
# Temperature-dependent rates using tgas variable

# Formation reactions
H + O -> OH, 1.2e-10 * (tgas/300)**0.5
H2 + O -> OH + H, 3.4e-11 * exp(-500/tgas)
C + O2 -> CO + O, 5.6e-12

# Three-body reactions
H + H + M -> H2 + M, 1.0e-32 * (tgas/300)**(-0.6)

# Photodissociation
CO + Photon -> C + O, photo(CO, 1e-10)
```

### Rate Expressions

JAFF supports SymPy expressions with these variables:

- `tgas`: Gas temperature (K)
- `tdust`: Dust temperature (K)
- `av`: Visual extinction
- `nh`: Hydrogen nuclei density
- `nh2`: H₂ density
- `nh0`: H density

**Common functions:**

```text
exp(x)      # Exponential
log(x)      # Natural logarithm
sqrt(x)     # Square root
pow(x, y)   # Power x^y
```

### Best Practices

```text
# Use descriptive comments
# H + O -> OH (neutral-neutral)
H + O -> OH, 1.2e-10 * (tgas/300)**0.5

# Group related reactions
# === Oxygen chemistry ===
O + H2 -> OH + H, 3.4e-11 * exp(-500/tgas)
OH + H2 -> H2O + H, 2.1e-11 * exp(-1000/tgas)

# === Carbon chemistry ===
C + O2 -> CO + O, 5.6e-12
CO + OH -> CO2 + H, 1.5e-13
```

## KROME Format

Format used by the KROME astrochemistry package.

### Syntax

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
idx,Reactant1,Reactant2,Reactant3,Product1,Product2,Product3,Product4,Tmin,Tmax,Rate
```

### Format Specification

The `@format:` line defines column meanings:

- `idx`: Reaction index (integer)
- `R`: Reactant (up to 3)
- `P`: Product (up to 4)
- `tmin`: Minimum temperature (K)
- `tmax`: Maximum temperature (K)
- `rate`: Rate expression

### Example

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate

# Reaction data
1,H,O,,,OH,,,10,1e4,1.2e-10*(T/300)**0.5
2,H2,O,,,OH,H,,10,1e4,3.4e-11*exp(-500/T)
3,C,O2,,,CO,O,,10,1e4,5.6e-12

# Three-body reactions (third body is last reactant)
4,H,H,H2,H2,,,,10,300,1.0e-32*(T/300)**(-0.6)
```

### Variables

KROME supports variable definitions:

```text
@var:te=tgas*8.617343e-5
@var:invtgas=1.0/tgas
@var:sqrtgas=sqrt(tgas)

1,H,O,,,OH,,,10,1e4,1.2e-10*sqrtgas
```

### Temperature Limits

Rate expressions are clamped to `[tmin, tmax]`:

```text
# This reaction only applies between 100K and 1000K
1,H,O,,,OH,,,100,1000,1.2e-10*(T/300)**0.5
```

When temperature is outside range:
- `T < Tmin`: Rate evaluated at `Tmin`
- `T > Tmax`: Rate evaluated at `Tmax`

### Special Lines

```text
@format:...        # Format specification
@var:name=expr     # Variable definition
@common:name=expr  # Common expression
# comment          # Comment line
```

## KIDA Format

Format from the Kinetic Database for Astrochemistry.

### Syntax

```text
Reactants -> Products : α : β : γ
```

**Rate formula:** k(T) = α × (T/300)^β × exp(-γ/T)

### Example

```text
H + O -> OH : 1.2e-10 : 0.5 : 0.0
H2 + O -> OH + H : 3.4e-11 : 0.0 : 500.0
C + O2 -> CO + O : 5.6e-12 : 0.0 : 0.0
```

### Parameters

- **α (alpha)**: Pre-exponential factor (cm³/s for 2-body)
- **β (beta)**: Temperature exponent
- **γ (gamma)**: Activation energy parameter (K)

### Temperature Dependence

```text
# No temperature dependence (β=0, γ=0)
C + O -> CO : 5.0e-11 : 0 : 0

# Power law only (γ=0)
H + O -> OH : 1.2e-10 : 0.5 : 0

# Exponential only (β=0)
H2 + O -> OH + H : 3.4e-11 : 0 : 500

# Both power law and exponential
OH + H2 -> H2O + H : 2.1e-11 : 0.5 : 1000
```

### Multiple Products/Reactants

```text
# Three reactants
H + H + M -> H2 + M : 1.0e-32 : -0.6 : 0

# Multiple products
H2O + hν -> OH + H : 1.0e-10 : 0 : 0
```

## UDFA Format

Format from the UMIST Database for Astrochemistry.

### Syntax

```text
R1:R2:R3:P1:P2:P3:P4:α:β:γ:Tmin:Tmax
```

Colon-separated format with all fields.

### Example

```text
H:O:::OH::::1.2e-10:0.5:0.0:10:1e4
H2:O:::OH:H:::3.4e-11:0.0:500.0:10:1e4
C:O2:::CO:O:::5.6e-12:0.0:0.0:10:1e4
```

### Field Order

1-3: Reactants (empty if fewer than 3)
4-7: Products (empty if fewer than 4)
8: α (pre-exponential factor)
9: β (temperature exponent)
10: γ (activation energy)
11: Tmin (minimum temperature)
12: Tmax (maximum temperature)

### Empty Fields

Use empty strings for missing reactants/products:

```text
# Single reactant, single product
CO::::C:O:::1.0e-10:0:0:10:1e4

# Two reactants, two products
H:O2:::OH:O:::2.0e-11:0:100:10:1e4
```

## PRIZMO Format

Format used by the PRIZMO code.

### Syntax

```text
VARIABLES{
    variable1 = expression1
    variable2 = expression2
}

Reactants -> Products, rate_expression
```

### Example

```text
VARIABLES{
    k1 = 1.2e-10
    k2 = 3.4e-11
    sqrtt = sqrt(tgas)
    expt = exp(-500/tgas)
}

H + O -> OH, k1 * sqrtt
H2 + O -> OH + H, k2 * expt
C + O2 -> CO + O, 5.6e-12
```

### Variable Block

Variables defined in `VARIABLES{}` block:

```text
VARIABLES{
    # Temperature variables
    t32 = tgas / 300
    invt = 1.0 / tgas
    
    # Common rate factors
    k_neutral = 1.0e-10 * sqrt(tgas)
    k_ion = 1.0e-9
}
```

Variables can reference each other:

```text
VARIABLES{
    t32 = tgas / 300
    sqrtt32 = sqrt(t32)
    rate_base = 1.0e-10 * sqrtt32
}
```

### Fortran Expressions

PRIZMO uses Fortran syntax:

```text
VARIABLES{
    # Fortran-style exponentiation
    t32 = tgas / 3.0e2
    
    # Double precision literals
    k1 = 1.0d-10
    k2 = 3.4d-11
}
```

JAFF automatically converts to Python syntax.

## UCL_CHEM Format

Format from the UCL_CHEM code.

### Syntax

```text
R1,R2,R3,P1,P2,P3,P4,α,β,γ
```

Comma-separated with `NAN` placeholders.

### Example

```text
H,O,NAN,OH,NAN,NAN,NAN,1.2e-10,0.5,0.0
H2,O,NAN,OH,H,NAN,NAN,3.4e-11,0.0,500.0
C,O2,NAN,CO,O,NAN,NAN,5.6e-12,0.0,0.0
```

### NAN Placeholders

Use `NAN` for empty slots:

```text
# Single reactant
CO,NAN,NAN,C,O,NAN,NAN,1.0e-10,0,0

# Two reactants, single product
H,H,NAN,H2,NAN,NAN,NAN,1.0e-32,-0.6,0
```

### Field Order

Fields: R1, R2, R3, P1, P2, P3, P4, α, β, γ

Always 10 comma-separated values per line.

## Format Comparison

### Rate Expression Styles

| Format | Expression Style | Example |
|--------|-----------------|---------|
| JAFF | SymPy | `1.2e-10 * (tgas/300)**0.5` |
| KROME | Fortran | `1.2e-10*(T/300)**0.5` |
| KIDA | Parameters | `1.2e-10 : 0.5 : 0` |
| UDFA | Parameters | `1.2e-10:0.5:0` |
| PRIZMO | Fortran | `k1 * sqrtt` |
| UCL_CHEM | Parameters | `1.2e-10,0.5,0` |

### Variable Names

| JAFF/PRIZMO | KROME | Meaning |
|-------------|-------|---------|
| `tgas` | `T` | Gas temperature |
| `tdust` | `Tdust` | Dust temperature |
| `av` | `Av` | Visual extinction |
| `nh` | `nH` | H nuclei density |

### Loading Any Format

```python
from jaff import Network

# JAFF auto-detects all formats
net = Network("network.dat")  # Works for any format
```

## Photoreactions

Different formats handle photoreactions differently.

### JAFF Format

```text
CO + Photon -> C + O, photo(CO, 1e-10)
H2O + hν -> OH + H, photo(H2O, 2e-10)
```

### KROME Format

```text
@format:idx,R,R,P,P,rate
1,CO,Photon,C,O,photo(1e-10,1e99)
```

### KIDA Format

```text
CO + Photon -> C + O : photo : 1e-10 : 0
```

## Best Practices

### Choosing a Format

**Use JAFF format when:**
- Creating new networks
- Need readable, editable files
- Want flexibility in rate expressions

**Use KROME format when:**
- Interfacing with KROME code
- Need temperature limits
- Want structured, indexed reactions

**Use KIDA format when:**
- Importing from KIDA database
- Simple Arrhenius-type rates
- Need compact representation

### Converting Formats

```python
# Load any format
net = Network("network_kida.dat")

# Examine reactions
for r in net.reactions[:5]:
    print(f"{r.verbatim}: {r.rate}")

# Reactions are now in JAFF internal format
# Can generate code in any target language
```

### Validation

Always validate when loading new networks:

```python
net = Network("new_network.dat", errors=True)
```

This catches format-specific issues.

## Format Detection

JAFF detects formats by examining file content:

```python
def detect_format(filename):
    with open(filename) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    
    content = '\n'.join(lines)
    
    if '@format:' in content:
        return "KROME"
    elif 'VARIABLES{' in content:
        return "PRIZMO"
    elif ',NAN,' in content:
        return "UCL_CHEM"
    elif content.count(':') > content.count(','):
        return "KIDA/UDFA"
    elif '->' in content:
        return "JAFF/PRIZMO"
    
    return "Unknown"
```

## Examples by Format

### Complete JAFF Network

```text
# CO chemistry network
# Author: Example
# Date: 2024

# === Formation ===
H + O -> OH, 1.2e-10 * (tgas/300)**0.5
H2 + O -> OH + H, 3.4e-11 * exp(-500/tgas)

# === CO formation ===
C + O2 -> CO + O, 5.6e-12
C + OH -> CO + H, 7.8e-11

# === Photochemistry ===
CO + Photon -> C + O, photo(CO, 1e-10)
```

### Complete KROME Network

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate

@var:sqrtgas=sqrt(tgas)
@var:invtgas=1.0/tgas

1,H,O,,,OH,,,10,1e4,1.2e-10*sqrtgas
2,H2,O,,,OH,H,,10,1e4,3.4e-11*exp(-500*invtgas)
3,C,O2,,,CO,O,,10,1e4,5.6e-12
```

### Complete KIDA Network

```text
H + O -> OH : 1.2e-10 : 0.5 : 0.0
H2 + O -> OH + H : 3.4e-11 : 0.0 : 500.0
C + O2 -> CO + O : 5.6e-12 : 0.0 : 0.0
C + OH -> CO + H : 7.8e-11 : 0.0 : 0.0
```

## See Also

- [Loading Networks](loading-networks.md) - How to load networks
- [Network API](../api/network.md) - Network class reference
- [Reference: Supported Formats](../reference/formats.md) - Format specifications
- [Basic Concepts](../getting-started/concepts.md) - Network fundamentals

---

**Next:** Learn about [Working with Species](species.md).
