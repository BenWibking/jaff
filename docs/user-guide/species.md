# Working with Species

Guide to working with chemical species in JAFF.

## Overview

Species represent individual chemical entities (atoms, molecules, ions) in a chemical reaction network.

```python
from jaff import Network

net = Network("networks/react_COthin")

# Access species
for species in net.species:
    print(f"{species.name}: mass={species.mass:.2f} amu, charge={species.charge}")
```

## Species Attributes

Each species object has the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Species identifier (e.g., "H2", "CO", "H+") |
| `mass` | float | Molecular mass in atomic mass units (amu) |
| `charge` | int | Electric charge (0 for neutral, ±1, ±2 for ions) |
| `index` | int | Position in the species array |
| `fidx` | str | Formatted index name for code generation |

## Accessing Species

### By Index

```python
# Get first species
species = net.species[0]
print(f"First species: {species.name}")

# Iterate over all species
for i, species in enumerate(net.species):
    print(f"{i}: {species.name}")
```

### By Name

```python
# Fast lookup using dictionary
if "CO" in net.species_dict:
    idx = net.species_dict["CO"]
    co = net.species[idx]
    print(f"CO at index {idx}, mass={co.mass}")
else:
    print("CO not in network")
```

### Using Helper Methods

```python
# Get species object by name
co = net.get_species_object("CO")
print(f"CO: {co.mass} amu, charge={co.charge}")

# Get species index by name
idx = net.get_species_index("CO")
print(f"CO is at index {idx}")

# Get number of species
nspec = net.get_number_of_species()
print(f"Network has {nspec} species")
```

## Species Properties

### Mass

Molecular mass in atomic mass units:

```python
for species in net.species[:5]:
    print(f"{species.name}: {species.mass:.4f} amu")

# Output:
# H: 1.0079 amu
# H2: 2.0159 amu
# O: 15.9994 amu
# OH: 17.0073 amu
# CO: 28.0101 amu
```

### Charge

Electric charge state:

```python
# Find all ions
ions = [s for s in net.species if s.charge != 0]
print(f"Found {len(ions)} ions:")
for ion in ions[:5]:
    print(f"  {ion.name}: charge={ion.charge:+d}")

# Find neutral species
neutral = [s for s in net.species if s.charge == 0]
print(f"Found {len(neutral)} neutral species")
```

### Index

Array position for code generation:

```python
for species in net.species[:3]:
    print(f"{species.name} at index {species.index}")

# Use in generated code
from jaff import Codegen
cg = Codegen(network=net, lang="c++")
# Indices will be: 0, 1, 2, ... for C++
# Indices will be: 1, 2, 3, ... for Fortran
```

## Filtering Species

### By Mass Range

```python
# Find species between 10 and 50 amu
mid_mass = [s for s in net.species if 10 <= s.mass <= 50]
print(f"Species with mass 10-50 amu: {len(mid_mass)}")
for s in mid_mass[:5]:
    print(f"  {s.name}: {s.mass:.2f} amu")
```

### By Charge

```python
# Positive ions
cations = [s for s in net.species if s.charge > 0]

# Negative ions
anions = [s for s in net.species if s.charge < 0]

# Neutral
neutral = [s for s in net.species if s.charge == 0]

print(f"Cations: {len(cations)}")
print(f"Anions: {len(anions)}")
print(f"Neutral: {len(neutral)}")
```

### By Element

```python
from jaff.elements import Elements

elem = Elements(net)

# Get element truth matrix
truth_matrix = elem.get_element_truth_matrix()

# Find species containing carbon
if "C" in elem.elements:
    carbon_idx = elem.elements.index("C")
    carbon_species = [
        net.species[i] for i in range(len(net.species))
        if truth_matrix[i][carbon_idx]
    ]
    print(f"Species containing carbon: {len(carbon_species)}")
    for s in carbon_species[:5]:
        print(f"  {s.name}")
```

### By Name Pattern

```python
import re

# Find all H2X species
h2_species = [s for s in net.species if s.name.startswith("H2")]
print(f"H2X species: {[s.name for s in h2_species]}")

# Find species matching pattern
pattern = re.compile(r"C.*O")  # C followed by O
co_species = [s for s in net.species if pattern.match(s.name)]
print(f"C*O species: {[s.name for s in co_species]}")
```

## Species Statistics

### Mass Distribution

```python
import numpy as np

masses = [s.mass for s in net.species]

print(f"Average mass: {np.mean(masses):.2f} amu")
print(f"Mass range: {np.min(masses):.2f} - {np.max(masses):.2f} amu")
print(f"Median mass: {np.median(masses):.2f} amu")
```

### Charge Distribution

```python
from collections import Counter

charges = [s.charge for s in net.species]
charge_dist = Counter(charges)

for charge, count in sorted(charge_dist.items()):
    print(f"Charge {charge:+d}: {count} species")
```

## Common Patterns

### Pattern 1: Species Lookup Table

```python
# Create lookup table
species_data = {
    s.name: {
        'index': s.index,
        'mass': s.mass,
        'charge': s.charge
    }
    for s in net.species
}

# Use lookup
if "CO" in species_data:
    print(f"CO data: {species_data['CO']}")
```

### Pattern 2: Species Groups

```python
# Group by charge state
by_charge = {}
for species in net.species:
    charge = species.charge
    if charge not in by_charge:
        by_charge[charge] = []
    by_charge[charge].append(species)

# Print groups
for charge, species_list in sorted(by_charge.items()):
    print(f"Charge {charge:+d}: {len(species_list)} species")
```

### Pattern 3: Mass-Ordered List

```python
# Sort by mass
sorted_species = sorted(net.species, key=lambda s: s.mass)

print("Lightest species:")
for s in sorted_species[:5]:
    print(f"  {s.name}: {s.mass:.4f} amu")

print("\nHeaviest species:")
for s in sorted_species[-5:]:
    print(f"  {s.name}: {s.mass:.4f} amu")
```

## Best Practices

### 1. Use Dictionary Lookup

```python
# Fast O(1) lookup
idx = net.species_dict["CO"]

# Avoid O(n) search
for s in net.species:
    if s.name == "CO":
        idx = s.index
```

### 2. Check Existence

```python
# Check before accessing
if "UnknownSpecies" in net.species_dict:
    species = net.get_species_object("UnknownSpecies")
else:
    print("Species not found")
```

### 3. Cache Frequently Used Data

```python
# Cache species for repeated access
h2_idx = net.species_dict["H2"]
co_idx = net.species_dict["CO"]

# Use cached indices
for reaction in net.reactions:
    # Fast access using cached indices
    pass
```

## See Also

- [Working with Reactions](reactions.md)
- [Network API](../api/network.md)
- [Elements API](../api/elements.md)
- [Loading Networks](loading-networks.md)

---

**Next:** Learn about [Working with Reactions](reactions.md).
