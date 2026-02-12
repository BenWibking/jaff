# Basic Concepts

This guide introduces the fundamental concepts you need to understand when working with JAFF.

## What is JAFF?

**JAFF** (Just Another F-word Format) is a Python library for working with chemical reaction networks. It provides tools to:

- **Load** chemical reaction networks from various formats
- **Analyze** network properties (species, reactions, elements)
- **Generate** optimized code for rate calculations, ODEs, and Jacobians
- **Export** networks to multiple programming languages (C, C++, Fortran, Python)

JAFF bridges the gap between chemical network databases and numerical simulations by automating code generation.

## Core Components

### 1. Chemical Networks

A **chemical network** describes a system of chemical species and the reactions between them.

**Key Elements:**

- **Species**: Individual chemical entities (atoms, molecules, ions)
- **Reactions**: Transformations between species
- **Rate Coefficients**: Functions that determine reaction speeds
- **Stoichiometry**: The ratios of reactants and products

**Example Network:**

```text
H + O -> OH
H2 + O -> OH + H
OH + H2 -> H2O + H
```

This network has:
- 4 species: H, O, H2, OH, H2O
- 3 reactions
- Temperature-dependent rate coefficients

### 2. Network Object

The `Network` class represents a loaded chemical network in memory.

```python
from jaff import Network

# Load a network file
net = Network("networks/react_COthin")

# Access properties
print(f"Species: {len(net.species)}")      # Number of species
print(f"Reactions: {len(net.reactions)}")  # Number of reactions
print(f"Label: {net.label}")                # Network identifier
```

**What it contains:**

- `species`: List of all chemical species
- `reactions`: List of all reactions
- `species_dict`: Fast lookup dictionary (name → index)
- `reactions_dict`: Dictionary of reactions by type
- Mass information and elemental composition

### 3. Species

A **species** represents a single chemical entity with properties.

```python
# Get a species
species = net.species[0]

print(f"Name: {species.name}")        # e.g., "CO"
print(f"Mass: {species.mass}")        # Atomic mass in amu
print(f"Charge: {species.charge}")    # Electric charge
print(f"Index: {species.index}")      # Position in array
```

**Species Properties:**

- `name`: Chemical formula or identifier
- `mass`: Molecular mass in atomic mass units
- `charge`: Electric charge (0 for neutral, +1/-1 for ions)
- `index`: Position in the species array (for indexing)

### 4. Reactions

A **reaction** describes a chemical transformation.

```python
# Get a reaction
reaction = net.reactions[0]

print(f"Reaction: {reaction.verbatim}")  # e.g., "H + O -> OH"
print(f"Type: {reaction.rtype}")         # Reaction type

# Calculate rate at a temperature
T = 100.0  # Kelvin
k = reaction.rate(T)
print(f"Rate at {T}K: {k}")
```

**Reaction Components:**

- **Reactants**: Species consumed in the reaction
- **Products**: Species created in the reaction
- **Rate Expression**: Formula for calculating reaction speed
- **Rate Type**: Classification (e.g., 2-body, photo, etc.)

**Rate Expressions:**

Most reactions use Arrhenius-type rate laws:

$$k(T) = \alpha \left(\frac{T}{300}\right)^\beta e^{-\gamma/T}$$

Where:
- α (alpha): Pre-exponential factor
- β (beta): Temperature exponent
- γ (gamma): Activation energy parameter
- T: Temperature in Kelvin

### 5. Code Generation

JAFF uses **templates** to generate code in multiple languages.

**Template Workflow:**

1. **Write a template** with JAFF commands
2. **Process the template** with the network
3. **Generate code** in your target language

**Example Template:**

```cpp
// Template: rates.cpp
const int NREACT = $JAFF SUB nreact$$nreact$$JAFF END$;

void compute_rates(double* k, double T) {
    $JAFF REPEAT idx IN rates$
    k[$idx$] = $rate$;  // $reaction$
    $JAFF END$
}
```

**Generated Code:**

```cpp
const int NREACT = 127;

void compute_rates(double* k, double T) {
    k[0] = 1.2e-10 * pow(T/300, 0.5);  // H + O -> OH
    k[1] = 3.4e-11 * exp(-500/T);      // H2 + O -> OH + H
    // ... more rates
}
```

## Key Concepts

### Network Files

JAFF supports multiple network file formats:

- **JAFF format** (.dat): Native format with simple syntax
- **KIDA format**: From the KInetic Database for Astrochemistry
- **UMIST format**: From the UMIST Database for Astrochemistry
- **Custom formats**: Via auxiliary function files

### Array Indexing

Different languages use different indexing conventions:

| Language | Starting Index | Example |
|----------|---------------|---------|
| C/C++    | 0             | `arr[0]` |
| Python   | 0             | `arr[0]` |
| Fortran  | 1             | `arr(1)` |

JAFF handles these differences automatically when generating code.

### Index Offsets

You can customize array indexing:

```python
from jaff import Codegen

cg = Codegen(network=net, lang="c++")

# Use default offset (0 for C++)
code1 = cg.get_rates(idx_offset=0)  # arr[0], arr[1], ...

# Use custom offset (e.g., start at 1)
code2 = cg.get_rates(idx_offset=1)  # arr[1], arr[2], ...
```

### Common Subexpression Elimination (CSE)

CSE is an optimization that reduces redundant calculations:

**Without CSE:**
```cpp
rate[0] = k0 * sqrt(T) * n[0];
rate[1] = k1 * sqrt(T) * n[1];
rate[2] = k2 * sqrt(T) * n[2];
```

**With CSE:**
```cpp
double x0 = sqrt(T);
rate[0] = k0 * x0 * n[0];
rate[1] = k1 * x0 * n[1];
rate[2] = k2 * x0 * n[2];
```

Enable CSE with `use_cse=True`:

```python
code = cg.get_rates(use_cse=True)  # More efficient
```

### ODEs (Ordinary Differential Equations)

Chemical networks produce systems of ODEs describing concentration changes:

$$\frac{dn_i}{dt} = \sum_j \nu_{ij} R_j$$

Where:
- $n_i$: Concentration of species i
- $R_j$: Rate of reaction j
- $\nu_{ij}$: Stoichiometric coefficient (net change of species i in reaction j)

JAFF generates these ODEs automatically:

```python
ode_code = cg.get_ode(ode_var="dydt", use_cse=True)
```

### Jacobian Matrix

The **Jacobian** is the matrix of partial derivatives:

$$J_{ij} = \frac{\partial f_i}{\partial y_j}$$

Where $f_i = dn_i/dt$ is the ODE for species i.

Jacobians are essential for implicit ODE solvers:

```python
jac_code = cg.get_jacobian(jac_var="J", use_cse=True)
```

### Element Conservation

Chemical reactions conserve elements. JAFF can check conservation:

```python
from jaff.elements import Elements

elem = Elements(net)

# Get element truth matrix (which species contain which elements)
truth_matrix = elem.get_element_truth_matrix()

# Get element density matrix (how many of each element per species)
density_matrix = elem.get_element_density_matrix()
```

## Workflow Examples

### Basic Analysis Workflow

```python
from jaff import Network

# 1. Load network
net = Network("networks/react_COthin")

# 2. Explore species
for species in net.species:
    print(f"{species.name}: {species.mass} amu")

# 3. Explore reactions
for reaction in net.reactions:
    print(f"{reaction.verbatim}: {reaction.rtype}")

# 4. Calculate rates at a temperature
T = 100.0
for reaction in net.reactions[:5]:
    k = reaction.rate(T)
    print(f"{reaction.verbatim}: k = {k:.2e}")
```

### Code Generation Workflow

```python
from jaff import Network, Codegen

# 1. Load network
net = Network("networks/react_COthin")

# 2. Create code generator
cg = Codegen(network=net, lang="c++")

# 3. Generate rate calculations
rates = cg.get_rates(idx_offset=0, use_cse=True)

# 4. Generate ODE system
odes = cg.get_ode(idx_offset=0, use_cse=True)

# 5. Generate Jacobian
jac = cg.get_jacobian(idx_offset=0, use_cse=True)

# 6. Save to file
with open("chemistry.cpp", "w") as f:
    f.write(rates)
    f.write("\n\n")
    f.write(odes)
    f.write("\n\n")
    f.write(jac)
```

### Template-Based Workflow

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# 1. Load network
net = Network("networks/react_COthin")

# 2. Process template file
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# 3. Save generated code
with open("output.cpp", "w") as f:
    f.write(output)
```

## Understanding Network Properties

### Species Count

```python
nspec = len(net.species)
print(f"Network has {nspec} species")
```

### Reaction Count

```python
nreact = len(net.reactions)
print(f"Network has {nreact} reactions")
```

### Species Lookup

```python
# By index
species = net.species[0]

# By name
idx = net.species_dict["CO"]
species = net.species[idx]
```

### Network Label

```python
label = net.label  # Identifier for this network
```

## Best Practices

### 1. Validate Networks

Always check for errors when loading:

```python
net = Network("mynetwork.dat", errors=True)
```

This enables warnings for:
- Missing sink/source species
- Duplicate reactions
- Isomer issues
- Element conservation violations

### 2. Use CSE for Performance

Enable CSE for production code:

```python
cg.get_rates(use_cse=True)  # Faster execution
```

### 3. Check Generated Code

Always review generated code before using:

```python
code = cg.get_rates()
print(code)  # Inspect output
```

### 4. Choose Appropriate Index Offsets

Match your target framework:

```python
# For C/C++/Python: start at 0
code = cg.get_rates(idx_offset=0)

# For Fortran: start at 1
code = cg.get_rates(idx_offset=1)

# For custom arrays: use any offset
code = cg.get_rates(idx_offset=5)
```

### 5. Organize Generated Code

Structure your output logically:

```python
# Generate all components
commons = cg.get_commons()
rates = cg.get_rates(use_cse=True)
odes = cg.get_ode(use_cse=True)
jac = cg.get_jacobian(use_cse=True)

# Combine in logical order
full_code = f"""
// Common definitions
{commons}

// Rate calculations
{rates}

// ODE system
{odes}

// Jacobian matrix
{jac}
"""
```

## Next Steps

Now that you understand the basic concepts:

1. **[Quick Start Guide](quickstart.md)**: Get hands-on experience
2. **[Loading Networks](../user-guide/loading-networks.md)**: Learn about network file formats
3. **[Code Generation](../user-guide/code-generation.md)**: Master code generation
4. **[Template Syntax](../user-guide/template-syntax.md)**: Create custom templates
5. **[API Reference](../api/index.md)**: Explore the complete API

## Common Terms

| Term | Definition |
|------|------------|
| **Species** | A chemical entity (atom, molecule, ion) |
| **Reaction** | A chemical transformation between species |
| **Rate Coefficient** | Function determining reaction speed |
| **Stoichiometry** | Ratio of reactants to products |
| **ODE** | Ordinary Differential Equation describing concentration changes |
| **Jacobian** | Matrix of partial derivatives of ODEs |
| **CSE** | Common Subexpression Elimination (optimization) |
| **Template** | File with JAFF commands for code generation |
| **Network** | Collection of species and reactions |
| **Index Offset** | Starting index for arrays (0 or 1) |

## Further Reading

- **Chemistry Background**: Understanding chemical kinetics helps interpret results
- **ODE Solvers**: Learn about numerical integration methods
- **Programming Languages**: Familiarity with target languages (C++, Fortran, etc.)
- **SymPy**: JAFF uses SymPy for symbolic mathematics

Happy learning! 🚀
