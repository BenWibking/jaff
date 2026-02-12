# File Formats Reference

This page provides a comprehensive reference for all file formats supported by `codegen_class`, including network files, configuration files, and output formats.

---

## Network Input Formats

### JAFF Format (.jaff)

The **JAFF** (JSON-based Autocatalytic Format for Files) is the native format for representing chemical reaction networks in `codegen_class`.

#### Structure

```json
{
  "species": [
    {
      "id": "A",
      "name": "Species A",
      "initial_concentration": 1.0,
      "properties": {}
    }
  ],
  "reactions": [
    {
      "id": "R1",
      "reactants": {"A": 1, "B": 1},
      "products": {"C": 2},
      "rate": "k1 * A * B",
      "reversible": false,
      "properties": {}
    }
  ],
  "parameters": {
    "k1": 0.1,
    "temperature": 298.15
  },
  "metadata": {
    "name": "Example Network",
    "description": "A simple example",
    "version": "1.0"
  }
}
```

#### Field Specifications

##### Species Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the species |
| `name` | string | No | Human-readable name |
| `initial_concentration` | number | No | Initial amount (default: 0.0) |
| `constant` | boolean | No | Whether concentration is fixed (default: false) |
| `boundary` | boolean | No | Whether species is a boundary condition (default: false) |
| `properties` | object | No | Additional metadata |

##### Reactions Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the reaction |
| `reactants` | object | Yes | Map of species ID to stoichiometry |
| `products` | object | Yes | Map of species ID to stoichiometry |
| `rate` | string/number | Yes | Rate expression or constant |
| `reversible` | boolean | No | Whether reaction is reversible (default: false) |
| `reverse_rate` | string/number | No | Reverse rate (if reversible) |
| `modifiers` | array | No | Species that affect rate but aren't consumed |
| `properties` | object | No | Additional metadata |

##### Parameters Object

Key-value pairs of parameter names to numeric values.

```json
{
  "k_forward": 0.1,
  "k_reverse": 0.01,
  "temperature": 298.15,
  "volume": 1.0
}
```

##### Metadata Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Network name |
| `description` | string | Detailed description |
| `version` | string | Format version |
| `author` | string | Creator information |
| `created` | string | ISO timestamp |
| `modified` | string | ISO timestamp |
| `references` | array | Citations or links |

#### Example: Complete JAFF File

```json
{
  "species": [
    {"id": "S", "name": "Substrate", "initial_concentration": 10.0},
    {"id": "E", "name": "Enzyme", "initial_concentration": 1.0, "constant": true},
    {"id": "ES", "name": "Enzyme-Substrate Complex", "initial_concentration": 0.0},
    {"id": "P", "name": "Product", "initial_concentration": 0.0}
  ],
  "reactions": [
    {
      "id": "binding",
      "reactants": {"S": 1, "E": 1},
      "products": {"ES": 1},
      "rate": "k_on * S * E",
      "reversible": true,
      "reverse_rate": "k_off * ES"
    },
    {
      "id": "catalysis",
      "reactants": {"ES": 1},
      "products": {"E": 1, "P": 1},
      "rate": "k_cat * ES"
    }
  ],
  "parameters": {
    "k_on": 1e6,
    "k_off": 0.1,
    "k_cat": 10.0
  },
  "metadata": {
    "name": "Michaelis-Menten Enzyme Kinetics",
    "description": "Classic enzyme kinetics model",
    "version": "1.0",
    "author": "Example Author"
  }
}
```

---

### SBML Format (.xml)

**SBML** (Systems Biology Markup Language) is a widely-used XML-based format for representing biological models.

#### Support Level

- **Import**: Full support for SBML Level 2 and Level 3 Core
- **Export**: Limited (basic features only)

#### Key Features Supported

- Species with initial amounts/concentrations
- Reactions with stoichiometry
- Kinetic laws (rate expressions)
- Parameters (global and local)
- Compartments
- Function definitions
- Initial assignments
- Assignment rules
- Rate rules
- Events (basic)

#### Example: SBML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="example_model" name="Example Model">
    <listOfCompartments>
      <compartment id="cell" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    
    <listOfSpecies>
      <species id="A" compartment="cell" initialConcentration="1.0" 
               hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    
    <listOfParameters>
      <parameter id="k1" value="0.1" constant="true"/>
    </listOfParameters>
    
    <listOfReactions>
      <reaction id="R1" reversible="false">
        <listOfReactants>
          <speciesReference species="A" stoichiometry="1"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="B" stoichiometry="1"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci>k1</ci>
              <ci>A</ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>
```

#### Conversion Notes

When converting from SBML to JAFF:

- Compartment volumes are incorporated into rate expressions
- MathML expressions are converted to string expressions
- Function definitions are inlined
- Rules are converted to assignments or differential equations
- Events are converted to conditional logic (where possible)

---

### CRN Format (.crn)

A simple, human-readable text format for chemical reaction networks.

#### Syntax

```
# Comments start with #

# Species declarations (optional)
species A, B, C

# Parameters (optional)
param k1 = 0.1
param k2 = 0.05

# Reactions
A + B -> C @ k1
C -> A + B @ k2 * C
2A + B <-> C @ (k_forward, k_reverse)
```

#### Rules

1. **Species**: Comma-separated list after `species` keyword
2. **Parameters**: `param name = value`
3. **Reactions**: 
   - Format: `reactants -> products @ rate`
   - Reversible: `reactants <-> products @ (forward_rate, reverse_rate)`
   - Stoichiometry: Use coefficient before species (e.g., `2A`)
   - Catalysts: Use `|` separator (e.g., `A + B |E-> C`)

#### Example: Complete CRN File

```
# Glycolysis Simplified Model

species Glucose, G6P, F6P, FBP, GAP, DHAP, PEP, Pyruvate
species ATP, ADP, NAD, NADH, Pi

param k_hexokinase = 0.1
param k_pgi = 0.05
param k_pfk = 0.2
param k_aldolase = 0.15

# Glucose phosphorylation
Glucose + ATP -> G6P + ADP @ k_hexokinase * Glucose * ATP

# Isomerization
G6P <-> F6P @ (k_pgi, k_pgi * 0.5)

# Phosphofructokinase (committed step)
F6P + ATP -> FBP + ADP @ k_pfk * F6P * ATP

# Aldolase
FBP <-> GAP + DHAP @ (k_aldolase, k_aldolase * 0.3)
```

---

## Configuration Files

### Template Configuration (.toml)

Templates can include a configuration file specifying template metadata and requirements.

#### Structure

```toml
[template]
name = "Python ODE Solver"
description = "Generates Python code with SciPy ODE solver"
version = "1.0.0"
author = "Your Name"

[requirements]
codegen_version = ">=0.1.0"
network_features = ["species", "reactions", "parameters"]

[output]
extension = ".py"
language = "python"

[variables]
# Custom variables with defaults
solver_method = "LSODA"
relative_tolerance = 1e-6
absolute_tolerance = 1e-8

[options]
# Boolean flags
include_plotting = true
include_analysis = false
verbose_output = false
```

---

### Code Generation Config (.yaml)

Configuration file for batch code generation jobs.

#### Structure

```yaml
# Input network files
networks:
  - path: networks/example1.jaff
    name: Example1
  - path: networks/example2.xml
    format: sbml

# Output configuration
output:
  directory: generated/
  format: python
  template: templates/ode_solver.py.jinja

# Code generation options
options:
  solver: scipy
  include_tests: true
  optimization_level: 2
  
# Parameter overrides
parameters:
  relative_tolerance: 1e-6
  absolute_tolerance: 1e-8
  max_time: 100.0

# Species of interest (for selective code generation)
species_filter:
  include: ["A", "B", "C"]
  exclude: ["intermediate_*"]

# Reaction filters
reaction_filter:
  types: ["mass_action", "enzymatic"]
```

---

## Output Formats

### Generated Code

#### Python (.py)

Generated Python code typically includes:

```python
"""
Generated by codegen_class
Network: Example Network
Date: 2024-01-15
"""

import numpy as np
from scipy.integrate import solve_ivp

# Parameters
params = {
    'k1': 0.1,
    'k2': 0.05
}

# Initial conditions
y0 = {
    'A': 1.0,
    'B': 0.5,
    'C': 0.0
}

def derivatives(t, y, params):
    """Compute time derivatives of species concentrations."""
    # Unpack state variables
    A, B, C = y
    
    # Unpack parameters
    k1 = params['k1']
    k2 = params['k2']
    
    # Compute reaction rates
    r1 = k1 * A * B
    r2 = k2 * C
    
    # Compute derivatives
    dA_dt = -r1 + r2
    dB_dt = -r1 + r2
    dC_dt = r1 - r2
    
    return [dA_dt, dB_dt, dC_dt]

# ... additional functions ...
```

#### C++ (.cpp)

```cpp
/**
 * Generated by codegen_class
 * Network: Example Network
 */

#include <vector>
#include <array>
#include <cmath>

class ReactionNetwork {
private:
    // Parameters
    double k1 = 0.1;
    double k2 = 0.05;
    
public:
    static const size_t NUM_SPECIES = 3;
    
    // Species indices
    enum Species { A = 0, B = 1, C = 2 };
    
    void derivatives(double t, const std::array<double, NUM_SPECIES>& y,
                    std::array<double, NUM_SPECIES>& dydt) {
        // Compute reaction rates
        double r1 = k1 * y[A] * y[B];
        double r2 = k2 * y[C];
        
        // Compute derivatives
        dydt[A] = -r1 + r2;
        dydt[B] = -r1 + r2;
        dydt[C] = r1 - r2;
    }
};
```

#### Julia (.jl)

```julia
# Generated by codegen_class
# Network: Example Network

using DifferentialEquations

# Parameters
params = (
    k1 = 0.1,
    k2 = 0.05
)

# Initial conditions
u0 = [
    1.0,  # A
    0.5,  # B
    0.0   # C
]

function derivatives!(du, u, p, t)
    # Unpack state
    A, B, C = u
    
    # Unpack parameters
    k1, k2 = p.k1, p.k2
    
    # Reaction rates
    r1 = k1 * A * B
    r2 = k2 * C
    
    # Derivatives
    du[1] = -r1 + r2  # dA/dt
    du[2] = -r1 + r2  # dB/dt
    du[3] = r1 - r2   # dC/dt
end
```

---

### Analysis Output

#### JSON Results

```json
{
  "network": "example_network",
  "timestamp": "2024-01-15T10:30:00Z",
  "statistics": {
    "num_species": 10,
    "num_reactions": 15,
    "num_parameters": 20
  },
  "species": [
    {
      "id": "A",
      "name": "Species A",
      "initial_concentration": 1.0,
      "appears_in_reactions": ["R1", "R2", "R5"]
    }
  ],
  "reactions": [
    {
      "id": "R1",
      "type": "mass_action",
      "order": 2,
      "reversible": false
    }
  ],
  "analysis": {
    "conserved_moieties": [
      {"species": ["A", "B", "C"], "total": "A + B + C"}
    ],
    "steady_states": [],
    "bifurcations": []
  }
}
```

---

## File Format Conversion

### Using the CLI

```bash
# Convert SBML to JAFF
jaff convert input.xml output.jaff

# Convert JAFF to CRN
jaff convert input.jaff output.crn

# Auto-detect format
jaff convert input.xml output.json --format auto

# Specify input/output formats explicitly
jaff convert network.txt network.xml --input-format crn --output-format sbml
```

### Using Python API

```python
from codegen_class import Network

# Load from any format
network = Network.from_file("input.xml")  # Auto-detects SBML

# Export to different format
network.to_jaff("output.jaff")
network.to_sbml("output.xml")
network.to_crn("output.crn")

# Convert directly
Network.convert("input.xml", "output.jaff")
```

---

## Format Validation

### JAFF Validation

```bash
# Validate JAFF file
jaff validate network.jaff

# Strict validation
jaff validate network.jaff --strict

# Output errors to file
jaff validate network.jaff --output errors.txt
```

### Common Validation Errors

| Error | Description | Fix |
|-------|-------------|-----|
| `INVALID_SPECIES_ID` | Species ID contains invalid characters | Use alphanumeric + underscore only |
| `DUPLICATE_ID` | Multiple items with same ID | Ensure all IDs are unique |
| `MISSING_SPECIES` | Reaction references undefined species | Add species definition |
| `INVALID_RATE` | Rate expression has syntax error | Check expression syntax |
| `NEGATIVE_CONCENTRATION` | Initial concentration < 0 | Use non-negative values |
| `CIRCULAR_DEPENDENCY` | Parameters reference each other circularly | Remove circular references |

---

## Best Practices

### File Organization

```
project/
├── networks/           # Input network files
│   ├── raw/           # Original files (SBML, etc.)
│   └── processed/     # Converted JAFF files
├── templates/         # Code generation templates
├── generated/         # Generated code output
├── config/           # Configuration files
└── results/          # Analysis results
```

### Naming Conventions

- **Species IDs**: Use descriptive names (e.g., `glucose_6_phosphate`, not `g6p`)
- **Reaction IDs**: Use systematic naming (e.g., `r_glycolysis_01`)
- **Parameters**: Use standard conventions (e.g., `k_forward_01`, `K_m_substrate`)
- **Files**: Use lowercase with underscores (e.g., `glycolysis_model.jaff`)

### Version Control

- Always include `version` in metadata
- Track changes in `modified` timestamp
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Document changes in metadata comments

---

## Troubleshooting

### Common Issues

**Problem**: SBML import fails with MathML error

**Solution**: Ensure SBML file uses supported MathML operators. Convert complex functions to simpler expressions.

---

**Problem**: CRN parser doesn't recognize reaction

**Solution**: Check syntax. Ensure spaces around operators (`->`, `@`). Use parentheses for complex expressions.

---

**Problem**: Generated code has syntax errors

**Solution**: Validate network file first. Check template syntax. Ensure all species/parameters are defined.

---

## See Also

- [Network Formats Guide](../user-guide/network-formats.md)
- [Code Generation Guide](../user-guide/code-generation.md)
- [Template Variables Reference](template-variables.md)
- [JAFF Commands Reference](jaff-commands.md)
