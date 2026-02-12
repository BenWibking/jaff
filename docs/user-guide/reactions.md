# Working with Reactions

This guide explains how to work with chemical reactions in the codegen_class library, including loading, manipulating, and analyzing reactions from network files.

## Overview

Reactions are the core building blocks of chemical reaction networks. Each reaction describes how species transform from reactants to products, potentially with modifiers (catalysts/inhibitors) and associated rate expressions.

## Reaction Structure

### Basic Components

A reaction in codegen_class consists of:

- **Reactants**: Species consumed by the reaction
- **Products**: Species produced by the reaction
- **Modifiers**: Species that affect the reaction rate without being consumed (catalysts, inhibitors)
- **Rate Expression**: Mathematical expression describing the reaction rate
- **Reversibility**: Whether the reaction can proceed in both directions

### Reaction Representation

```python
from codegen_class import Network

# Load a network
network = Network.from_file("network.jaff")

# Access reactions
for reaction in network.reactions:
    print(f"Reaction ID: {reaction.id}")
    print(f"Reactants: {reaction.reactants}")
    print(f"Products: {reaction.products}")
    print(f"Rate: {reaction.rate}")
    print(f"Reversible: {reaction.reversible}")
```

## Creating Reactions

### From Network Files

Most commonly, reactions are loaded from network files:

```python
# From JAFF format
network = Network.from_file("network.jaff")

# From SBML
network = Network.from_sbml("model.xml")

# From Antimony
network = Network.from_antimony("model.ant")
```

### Programmatic Creation

You can also create reactions programmatically:

```python
from codegen_class import Reaction, Species

# Create species
A = Species(id="A", name="Species A")
B = Species(id="B", name="Species B")
C = Species(id="C", name="Species C")

# Create a reaction: A + B -> C
reaction = Reaction(
    id="R1",
    name="Formation of C",
    reactants={"A": 1, "B": 1},
    products={"C": 1},
    rate="k1 * A * B"
)
```

## Reaction Properties

### Stoichiometry

Access stoichiometric coefficients for reactants and products:

```python
reaction = network.get_reaction("R1")

# Get stoichiometry
for species_id, coefficient in reaction.reactants.items():
    print(f"Reactant {species_id}: {coefficient}")

for species_id, coefficient in reaction.products.items():
    print(f"Product {species_id}: {coefficient}")

# Calculate net stoichiometry
net_stoich = reaction.net_stoichiometry()
for species_id, net_coeff in net_stoich.items():
    print(f"{species_id}: {net_coeff:+d}")
```

### Rate Expressions

Work with reaction rate expressions:

```python
# Get rate expression
rate = reaction.rate
print(f"Rate law: {rate}")

# Check if rate is mass action
if reaction.is_mass_action():
    print("This is a mass action reaction")
    print(f"Rate constant: {reaction.rate_constant}")

# Get rate parameters
params = reaction.get_parameters()
for param in params:
    print(f"Parameter: {param}")
```

### Reversibility

Handle reversible reactions:

```python
if reaction.reversible:
    print(f"Forward rate: {reaction.forward_rate}")
    print(f"Reverse rate: {reaction.reverse_rate}")
    
    # Get equilibrium constant
    K_eq = reaction.equilibrium_constant()
    print(f"K_eq = {K_eq}")
else:
    print("This is an irreversible reaction")
```

## Reaction Types

### Elementary Reactions

Elementary reactions follow mass action kinetics:

```python
# Unimolecular: A -> B
# Rate = k * A

# Bimolecular: A + B -> C
# Rate = k * A * B

# Trimolecular: A + B + C -> D
# Rate = k * A * B * C
```

### Enzymatic Reactions

Michaelis-Menten and Hill kinetics:

```python
# Michaelis-Menten
# Rate = Vmax * S / (Km + S)

# Hill equation
# Rate = Vmax * S^n / (Km^n + S^n)

# Check for enzymatic kinetics
if reaction.is_enzymatic():
    print(f"Enzyme: {reaction.enzyme}")
    print(f"Substrate: {reaction.substrate}")
    print(f"Km: {reaction.Km}")
    print(f"Vmax: {reaction.Vmax}")
```

### Custom Kinetics

Reactions with arbitrary rate laws:

```python
# Custom rate expression
reaction = Reaction(
    id="R_custom",
    rate="k * A^2 * B / (1 + K * C)"
)

# Extract variables from rate
variables = reaction.get_rate_variables()
print(f"Variables in rate: {variables}")
```

## Modifiers and Catalysis

### Working with Modifiers

Modifiers affect reaction rates without being consumed:

```python
# Create reaction with modifier
reaction = Reaction(
    id="R_catalyzed",
    reactants={"A": 1},
    products={"B": 1},
    modifiers={"E": "catalyst"},
    rate="k * E * A / (Km + A)"
)

# Access modifiers
for modifier_id, role in reaction.modifiers.items():
    print(f"Modifier {modifier_id}: {role}")
```

### Catalytic Cycles

Model enzyme catalysis:

```python
# Enzyme catalysis: E + S <-> ES -> E + P
reactions = [
    Reaction(
        id="R1",
        reactants={"E": 1, "S": 1},
        products={"ES": 1},
        rate="k1 * E * S",
        reversible=True
    ),
    Reaction(
        id="R2",
        reactants={"ES": 1},
        products={"E": 1, "P": 1},
        rate="k2 * ES"
    )
]
```

## Reaction Filtering and Selection

### Query Reactions

Find reactions matching specific criteria:

```python
# Get all reactions involving a species
reactions_with_A = network.get_reactions_with_species("A")

# Get reactions by type
unimolecular = network.get_reactions_by_order(1)
bimolecular = network.get_reactions_by_order(2)

# Get reversible reactions
reversible = network.get_reversible_reactions()

# Get reactions with modifiers
catalyzed = network.get_reactions_with_modifiers()
```

### Filter by Properties

```python
# Filter by rate constant range
fast_reactions = [
    r for r in network.reactions
    if r.has_rate_constant() and r.rate_constant > 100
]

# Filter by stoichiometry
synthesis_reactions = [
    r for r in network.reactions
    if len(r.products) == 1 and len(r.reactants) > 1
]

# Filter by complexity
simple_reactions = [
    r for r in network.reactions
    if len(r.reactants) + len(r.products) <= 3
]
```

## Reaction Analysis

### Stoichiometric Analysis

Analyze reaction stoichiometry:

```python
# Build stoichiometric matrix
S = network.stoichiometric_matrix()
print(f"Stoichiometric matrix shape: {S.shape}")

# Get conservation laws
conservation = network.conservation_laws()
for law in conservation:
    print(f"Conservation: {law}")

# Check for conservation
if network.is_conservative():
    print("Network conserves total mass")
```

### Rate Analysis

Analyze reaction rates:

```python
# Get maximum possible rate
max_rate = reaction.max_rate(species_concentrations)

# Calculate sensitivity
sensitivity = reaction.rate_sensitivity("A", concentrations)

# Compare rates
rates = {r.id: r.evaluate_rate(concentrations) for r in network.reactions}
sorted_rates = sorted(rates.items(), key=lambda x: x[1], reverse=True)
print("Fastest reactions:")
for rxn_id, rate in sorted_rates[:5]:
    print(f"  {rxn_id}: {rate}")
```

### Thermodynamic Analysis

Check thermodynamic consistency:

```python
# Check for detailed balance
if reaction.satisfies_detailed_balance(concentrations):
    print("Reaction satisfies detailed balance")

# Calculate Gibbs free energy
delta_G = reaction.gibbs_free_energy(concentrations)
print(f"ΔG = {delta_G} kJ/mol")

# Check reversibility from thermodynamics
if delta_G < 0:
    print("Forward reaction is thermodynamically favorable")
```

## Reaction Modification

### Updating Reactions

Modify existing reactions:

```python
# Update rate
reaction.rate = "k_new * A * B"

# Add modifier
reaction.add_modifier("E", role="catalyst")

# Change stoichiometry
reaction.set_product("C", coefficient=2)

# Toggle reversibility
reaction.reversible = True
reaction.reverse_rate = "k_rev * C"
```

### Reaction Transformations

Transform reactions systematically:

```python
# Scale all rate constants
for reaction in network.reactions:
    if reaction.is_mass_action():
        reaction.rate_constant *= 1.5

# Convert to reversible
for reaction in network.reactions:
    if not reaction.reversible:
        reaction.make_reversible(K_eq=1.0)

# Normalize stoichiometry
for reaction in network.reactions:
    reaction.normalize_stoichiometry()
```

## Common Patterns

### Reaction Enumeration

Iterate through all reactions:

```python
for i, reaction in enumerate(network.reactions):
    print(f"{i+1}. {reaction}")
    print(f"   Rate: {reaction.rate}")
    print()
```

### Reaction Comparison

Compare two reactions:

```python
def reactions_equivalent(r1, r2):
    """Check if two reactions are equivalent."""
    return (
        r1.reactants == r2.reactants and
        r1.products == r2.products and
        r1.modifiers == r2.modifiers
    )

# Find duplicate reactions
duplicates = []
for i, r1 in enumerate(network.reactions):
    for r2 in network.reactions[i+1:]:
        if reactions_equivalent(r1, r2):
            duplicates.append((r1.id, r2.id))
```

### Reaction Pathways

Trace reaction pathways:

```python
def find_pathway(network, start_species, end_species, max_steps=5):
    """Find reaction pathway from start to end species."""
    pathways = []
    
    def search(current, target, path, steps):
        if steps > max_steps:
            return
        if current == target:
            pathways.append(path.copy())
            return
            
        for reaction in network.get_reactions_producing(current):
            if reaction.id not in path:
                path.append(reaction.id)
                for reactant in reaction.reactants:
                    search(reactant, target, path, steps + 1)
                path.pop()
    
    search(end_species, start_species, [], 0)
    return pathways
```

## Best Practices

### Naming Conventions

```python
# Use descriptive reaction IDs
reaction.id = "glucose_phosphorylation"  # Good
reaction.id = "R1"  # Less descriptive

# Include direction for reversible reactions
forward = Reaction(id="ATP_hydrolysis_forward", ...)
reverse = Reaction(id="ATP_hydrolysis_reverse", ...)
```

### Rate Expression Clarity

```python
# Use clear parameter names
rate = "k_cat * E * S / (K_m + S)"  # Good
rate = "a * b * c / (d + c)"  # Unclear

# Document units in comments
reaction.rate = "k * A * B"  # k in M^-1 s^-1
```

### Validation

Always validate reactions:

```python
# Check for mass balance
if not reaction.is_balanced():
    print(f"Warning: Reaction {reaction.id} is not balanced")

# Check for valid rate
try:
    reaction.validate_rate()
except ValueError as e:
    print(f"Invalid rate: {e}")

# Check for negative stoichiometry
if any(c < 0 for c in reaction.reactants.values()):
    print("Error: Negative reactant coefficient")
```

## Troubleshooting

### Common Issues

**Issue**: Rate expression contains undefined variables

```python
# Check for undefined parameters
undefined = reaction.get_undefined_parameters(network.parameters)
if undefined:
    print(f"Undefined parameters: {undefined}")
```

**Issue**: Stoichiometry doesn't balance

```python
# Check element balance
if not reaction.check_element_balance():
    print("Elements don't balance")
    print(f"Reactant elements: {reaction.get_reactant_elements()}")
    print(f"Product elements: {reaction.get_product_elements()}")
```

**Issue**: Rate evaluation fails

```python
# Safely evaluate rate
try:
    rate_value = reaction.evaluate_rate(concentrations)
except Exception as e:
    print(f"Rate evaluation failed: {e}")
    print(f"Rate expression: {reaction.rate}")
    print(f"Available concentrations: {concentrations.keys()}")
```

## See Also

- [Species](species.md) - Working with chemical species
- [Rates](rates.md) - Rate law expressions and kinetics
- [Network Formats](network-formats.md) - File format specifications
- [Code Generation](code-generation.md) - Generating code from reactions
- [API Reference: Reaction](../api/reaction.md) - Complete API documentation

## Examples

For complete examples of working with reactions, see:

- [Basic Usage Tutorial](../tutorials/basic-usage.md)
- [Network Analysis Tutorial](../tutorials/network-analysis.md)
- Example networks in the `examples/` directory
