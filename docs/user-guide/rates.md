# Rate Expressions

This guide explains how to work with rate expressions in reaction networks, including rate laws, parameters, and units.

## Overview

Rate expressions define how fast reactions occur in chemical reaction networks. The `codegen_class` library supports various rate law formats and provides tools for parsing, manipulating, and generating code from rate expressions.

## Rate Law Types

### Mass Action Kinetics

The most common rate law form, where the rate is proportional to the product of reactant concentrations:

```python
from codegen_class import Network

# Example: A + B -> C with rate k*[A]*[B]
network = Network.from_jaff("""
species A, B, C;
reaction A + B -> C, k;
""")

# Access rate expression
reaction = network.reactions[0]
print(reaction.rate)  # Output: k
```

For mass action kinetics:

- **Unimolecular**: `A -> B` with rate `k` → actual rate = `k * [A]`
- **Bimolecular**: `A + B -> C` with rate `k` → actual rate = `k * [A] * [B]`
- **Trimolecular**: `A + B + C -> D` with rate `k` → actual rate = `k * [A] * [B] * [C]`

### Explicit Rate Expressions

You can specify explicit rate expressions that override mass action:

```python
network = Network.from_jaff("""
species A, B, C;
parameter k1, k2, Km;

# Michaelis-Menten kinetics
reaction A -> B, k1*A/(Km + A);

# Hill equation
reaction B -> C, k2*B^2/(1 + B^2);
""")
```

### Common Rate Laws

#### Michaelis-Menten

Enzyme kinetics:

```python
# V_max * [S] / (K_m + [S])
reaction S -> P, Vmax*S/(Km + S);
```

#### Hill Equation

Cooperative binding:

```python
# V_max * [S]^n / (K_d^n + [S]^n)
reaction S -> P, Vmax*S^n/(Kd^n + S^n);
```

#### Competitive Inhibition

```python
# V_max * [S] / (K_m * (1 + [I]/K_i) + [S])
reaction S -> P, Vmax*S/(Km*(1 + I/Ki) + S);
```

#### Reversible Mass Action

```python
# Forward and reverse reactions
reaction A <-> B, kf*A - kr*B;
# Or as separate reactions:
reaction A -> B, kf;
reaction B -> A, kr;
```

## Parameters

### Defining Parameters

Parameters are rate constants and other constants used in rate expressions:

```python
network = Network.from_jaff("""
parameter k1 = 0.1;
parameter k2 = 1.0;
parameter Km = 0.5;

species A, B, C;

reaction A -> B, k1;
reaction B -> C, k2*B/(Km + B);
""")

# Access parameters
for param_name, param_value in network.parameters.items():
    print(f"{param_name} = {param_value}")
```

### Parameter Values

Parameters can be:

- **Constant**: Fixed numerical values
- **Variable**: Symbols to be defined later
- **Derived**: Computed from other parameters

```python
network = Network.from_jaff("""
# Constant parameters
parameter k1 = 0.1;
parameter k2 = 1.0;

# Variable parameter (no value)
parameter Km;

# Derived parameter (computed from others)
parameter kcat = k2/Km;

species E, S, ES, P;
reaction E + S -> ES, k1;
reaction ES -> E + P, k2;
""")
```

### Accessing Parameters

```python
# Get parameter value
k1_value = network.get_parameter('k1')

# Set parameter value
network.set_parameter('k1', 0.2)

# List all parameters
params = network.parameters
print(params)  # {'k1': 0.2, 'k2': 1.0, ...}
```

## Units

### Unit Specification

While the parser doesn't enforce units, it's good practice to document them:

```python
network = Network.from_jaff("""
# Rate constants with units (as comments)
parameter k1 = 0.1;  # s^-1 (first-order)
parameter k2 = 1e6;  # M^-1 s^-1 (second-order)
parameter k3 = 1e9;  # M^-2 s^-1 (third-order)

species A, B, C, D;  # All in M (molar)

reaction A -> B, k1;         # rate in M/s
reaction B + C -> D, k2;     # rate in M/s
reaction A + B + C -> D, k3; # rate in M/s
""")
```

### Common Unit Systems

#### Concentration Units
- **M** (Molar): mol/L
- **mM** (Millimolar): mmol/L
- **μM** (Micromolar): μmol/L
- **nM** (Nanomolar): nmol/L
- **molecules/cell**: Number density

#### Time Units
- **s** (seconds)
- **min** (minutes)
- **h** (hours)

#### Rate Constant Units

| Order | Reaction Type | Rate Constant Units | Example |
|-------|--------------|---------------------|---------|
| 0 | `-> A` | M/s | Production |
| 1 | `A ->` | s⁻¹ | Degradation |
| 2 | `A + B ->` | M⁻¹ s⁻¹ | Binding |
| 3 | `A + B + C ->` | M⁻² s⁻¹ | Trimolecular |

### Unit Conversion

When working with different unit systems, convert parameters accordingly:

```python
# Convert from seconds to minutes
k_per_sec = 0.1  # s^-1
k_per_min = k_per_sec * 60  # min^-1

# Convert from M to mM
k_M = 1e6  # M^-1 s^-1
k_mM = k_M / 1000  # mM^-1 s^-1

network = Network.from_jaff(f"""
parameter k1 = {k_per_min};  # min^-1
parameter k2 = {k_mM};       # mM^-1 s^-1

species A, B, C;
reaction A -> B, k1;
reaction B + C -> A, k2;
""")
```

## Rate Expression Manipulation

### Extracting Rate Information

```python
network = Network.from_jaff("""
species A, B, C;
parameter k1, k2;

reaction A + B -> C, k1*A*B;
reaction C -> A + B, k2;
""")

for i, reaction in enumerate(network.reactions):
    print(f"Reaction {i}:")
    print(f"  Rate expression: {reaction.rate}")
    print(f"  Reactants: {reaction.reactants}")
    print(f"  Products: {reaction.products}")
```

### Parsing Rate Expressions

Rate expressions are parsed into symbolic form:

```python
from codegen_class import parse_jaff

network = parse_jaff("""
species A, B;
parameter k, Km;

reaction A -> B, k*A/(Km + A);
""")

reaction = network.reactions[0]
print(reaction.rate)  # Symbolic representation
```

### Modifying Rates

You can modify rate expressions programmatically:

```python
# Create network
network = Network.from_jaff("""
species A, B;
parameter k = 0.1;
reaction A -> B, k;
""")

# Modify rate expression
reaction = network.reactions[0]
# (Note: Exact API depends on implementation)
# reaction.rate = "k*A"  # Example modification
```

## Code Generation with Rates

### ODE Systems

Generate ODE code with rate expressions:

```python
network = Network.from_jaff("""
species A, B, C;
parameter k1 = 0.1, k2 = 0.05;

reaction A -> B, k1;
reaction B -> C, k2;
""")

# Generate Python ODE function
code = network.generate_code('python', 'ode')
print(code)
```

Output example:

```python
def ode_system(t, y, params):
    A, B, C = y
    k1, k2 = params['k1'], params['k2']
    
    dA_dt = -k1 * A
    dB_dt = k1 * A - k2 * B
    dC_dt = k2 * B
    
    return [dA_dt, dB_dt, dC_dt]
```

### Stochastic Simulations

Generate code for stochastic simulation algorithms:

```python
# Generate Gillespie algorithm code
code = network.generate_code('python', 'gillespie')
print(code)
```

### Custom Templates

Create custom templates with rate expressions:

```jinja2
{# custom_rates.jinja #}
{% for reaction in reactions %}
Reaction {{ loop.index }}: {{ reaction.rate }}
  - Type: {% if reaction.is_mass_action %}Mass Action{% else %}Custom{% endif %}
  - Order: {{ reaction.order }}
{% endfor %}
```

## Best Practices

### 1. Parameter Organization

Group related parameters:

```python
network = Network.from_jaff("""
# Transcription rates
parameter k_tx_A = 1.0;
parameter k_tx_B = 0.5;

# Translation rates
parameter k_tl_A = 10.0;
parameter k_tl_B = 5.0;

# Degradation rates
parameter gamma_A = 0.1;
parameter gamma_B = 0.2;

species mRNA_A, mRNA_B, Protein_A, Protein_B;

reaction -> mRNA_A, k_tx_A;
reaction mRNA_A -> Protein_A, k_tl_A;
reaction Protein_A ->, gamma_A;
""")
```

### 2. Use Descriptive Names

```python
# Good: descriptive parameter names
parameter binding_rate = 1e6;
parameter unbinding_rate = 0.1;
parameter catalytic_rate = 100;

# Avoid: cryptic names
parameter k1 = 1e6;
parameter k2 = 0.1;
parameter k3 = 100;
```

### 3. Document Assumptions

```python
network = Network.from_jaff("""
# Assumes:
# - Well-mixed system
# - Constant temperature (37°C)
# - Constant volume
# - Dilute solution (activity coefficients = 1)

parameter k_on = 1e6;   # M^-1 s^-1, diffusion-limited
parameter k_off = 0.1;  # s^-1
parameter K_d = 0.1e-6; # M, k_off/k_on

species L, R, LR;
reaction L + R -> LR, k_on;
reaction LR -> L + R, k_off;
""")
```

### 4. Validate Rate Constants

Ensure rate constants are physically reasonable:

```python
def validate_rate_constants(network):
    """Check that rate constants are in reasonable ranges."""
    for param_name, param_value in network.parameters.items():
        if param_value is not None:
            # Check for negative rates
            if param_value < 0:
                print(f"Warning: {param_name} is negative: {param_value}")
            
            # Check for extremely large/small values
            if abs(param_value) > 1e10:
                print(f"Warning: {param_name} is very large: {param_value}")
            if 0 < abs(param_value) < 1e-10:
                print(f"Warning: {param_name} is very small: {param_value}")

validate_rate_constants(network)
```

## Advanced Topics

### Time-Dependent Rates

Some systems require time-dependent rate expressions:

```python
# Note: Support depends on implementation
network = Network.from_jaff("""
species A, B;
parameter k0, omega;

# Periodic forcing
reaction A -> B, k0*(1 + sin(omega*t));
""")
```

### Conditional Rates

Use piecewise or conditional expressions:

```python
# Example: Switch-like behavior
network = Network.from_jaff("""
species A, B;
parameter k, threshold;

# Rate depends on concentration threshold
reaction A -> B, k*heaviside(A - threshold);
""")
```

### Composite Rates

Build complex rates from simpler components:

```python
network = Network.from_jaff("""
parameter k1, k2, K1, K2;
species S, E1, E2, P;

# Multiple enzyme activities
reaction S -> P, (k1*E1/(K1 + S)) + (k2*E2/(K2 + S));
""")
```

## Troubleshooting

### Common Issues

1. **Undefined Parameters**
   ```python
   # Error: parameter 'k' not defined
   reaction A -> B, k;  # k must be declared first
   
   # Fix:
   parameter k;
   reaction A -> B, k;
   ```

2. **Unit Mismatches**
   ```python
   # Be careful with unit consistency
   parameter k1 = 0.1;  # s^-1
   parameter k2 = 100;  # Different order reaction!
   ```

3. **Syntax Errors in Expressions**
   ```python
   # Error: invalid syntax
   reaction A -> B, k*A^;  # Missing exponent
   
   # Fix:
   reaction A -> B, k*A^2;
   ```

## See Also

- [Reactions](reactions.md) - Working with reactions
- [Species](species.md) - Defining species
- [Code Generation](code-generation.md) - Generating simulation code
- [Template Syntax](template-syntax.md) - Custom code templates
- [API Reference: Reaction](../api/reaction.md) - Reaction class API

## Examples

Complete examples can be found in the [Tutorials](../tutorials/basic-usage.md) section.
