# Elements API Reference

The `elements` module provides utilities for extracting chemical elements from species and generating element-related matrices for conservation laws and stoichiometric analysis.

## Overview

The Elements class analyzes all species in a chemical reaction network to extract unique chemical elements and provides methods to generate matrices that describe element composition and presence across all species. These matrices are essential for:

- Checking element conservation in reactions
- Computing mass balance equations
- Analyzing stoichiometry
- Validating network consistency

## Module: `jaff.elements`

::: jaff.elements
    options:
      show_root_heading: true
      show_source: true
      heading_level: 2

## Classes

### Elements

::: jaff.elements.Elements
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get_element_truth_matrix
        - get_element_density_matrix
      heading_level: 3

The main class for extracting and managing chemical elements from a reaction network.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `net` | Network | The chemical reaction network to analyze |
| `elements` | list[str] | Sorted list of unique element symbols |
| `nelems` | int | Total number of unique elements |

#### Constructor

##### `__init__(network: Network) -> None`

Initialize the Elements analyzer for a given reaction network.

**Parameters**:

- `network` (Network): Chemical reaction network containing species to analyze

**Example**:
```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)
print(f"Found {elem.nelems} elements: {elem.elements}")
```

**Output**:
```
Found 3 elements: ['C', 'H', 'O']
```

#### Methods

##### `get_element_truth_matrix() -> list[list[int]]`

Generate a binary matrix indicating element presence in each species.

Creates a matrix where entry `[i][j]` is `1` if element `i` is present in species `j`, and `0` otherwise. This is useful for checking element conservation laws and identifying species composition.

**Returns**: 

- `list[list[int]]`: 2D matrix (nelems × nspecies) with binary values
  - `1` if the element is present in the species
  - `0` if the element is absent from the species

**Example**:
```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)
truth_matrix = elem.get_element_truth_matrix()

# Print which elements are in each species
for i, element in enumerate(elem.elements):
    print(f"{element}: {truth_matrix[i]}")
```

**Example Output**:
```
C: [1, 0, 1, 1, 0]  # C present in species 0, 2, 3
H: [0, 1, 0, 1, 1]  # H present in species 1, 3, 4
O: [1, 0, 1, 0, 1]  # O present in species 0, 2, 4
```

**Concrete Example**:

For elements `['C', 'H', 'O']` and species `['CO', 'H2', 'H2O', 'CH4']`:

```python
[
    [1, 0, 0, 1],   # C: present in CO and CH4
    [0, 1, 1, 1],   # H: present in H2, H2O, and CH4
    [1, 0, 1, 0]    # O: present in CO and H2O
]
```

**Use Cases**:

- **Conservation checks**: Verify element conservation in reactions
- **Species filtering**: Find all species containing a specific element
- **Network analysis**: Identify elemental composition patterns

##### `get_element_density_matrix() -> list[list[int]]`

Generate a matrix showing element counts in each species.

Creates a matrix where entry `[i][j]` represents the number of atoms of element `i` present in species `j`. This is essential for stoichiometric calculations and mass balance equations.

**Returns**:

- `list[list[int]]`: 2D matrix (nelems × nspecies) with integer counts representing the number of atoms of each element in each species

**Example**:
```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)
density_matrix = elem.get_element_density_matrix()

# Print element counts for each species
for i, element in enumerate(elem.elements):
    print(f"{element}: {density_matrix[i]}")
```

**Example Output**:
```
C: [1, 0, 1, 1, 0]  # Number of C atoms in each species
H: [0, 2, 0, 4, 1]  # Number of H atoms in each species
O: [1, 0, 1, 0, 2]  # Number of O atoms in each species
```

**Concrete Example**:

For elements `['C', 'H', 'O']` and species `['CO', 'H2', 'H2O', 'CH4']`:

```python
[
    [1, 0, 0, 1],   # C: 1 in CO, 0 in H2, 0 in H2O, 1 in CH4
    [0, 2, 2, 4],   # H: 0 in CO, 2 in H2, 2 in H2O, 4 in CH4
    [1, 0, 1, 0]    # O: 1 in CO, 0 in H2, 1 in H2O, 0 in CH4
]
```

**Use Cases**:

- **Mass conservation**: Calculate total elemental mass
- **Stoichiometry**: Determine reaction stoichiometric coefficients
- **Abundance tracking**: Monitor elemental abundances over time
- **Network validation**: Verify mass balance in reactions

## Usage Examples

### Basic Element Extraction

```python
from jaff import Network
from jaff.elements import Elements

# Load network
net = Network("networks/react_COthin")

# Create Elements analyzer
elem = Elements(net)

# Access element information
print(f"Number of elements: {elem.nelems}")
print(f"Elements found: {elem.elements}")
```

### Element Conservation Check

```python
from jaff import Network
from jaff.elements import Elements
import numpy as np

net = Network("networks/react_COthin")
elem = Elements(net)

# Get density matrix
density = np.array(elem.get_element_density_matrix())

# Check conservation for a reaction: 2H + O -> H2O
# Indices: H=0, O=1, H2O=2 (example)
reactants = np.array([2, 1, 0])  # 2 H + 1 O
products = np.array([0, 0, 1])   # 1 H2O

# Element balance
reactant_elements = density @ reactants
product_elements = density @ products

if np.allclose(reactant_elements, product_elements):
    print("Reaction conserves elements!")
else:
    print("Element conservation violated!")
```

### Finding Species by Element

```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)

# Get truth matrix
truth_matrix = elem.get_element_truth_matrix()

# Find all species containing carbon
c_index = elem.elements.index('C')
species_with_carbon = [
    net.species[j].name 
    for j in range(len(net.species)) 
    if truth_matrix[c_index][j] == 1
]

print(f"Species containing carbon: {species_with_carbon}")
```

### Computing Total Elemental Mass

```python
from jaff import Network
from jaff.elements import Elements
import numpy as np

net = Network("networks/react_COthin")
elem = Elements(net)

# Get density matrix
density = np.array(elem.get_element_density_matrix())

# Species abundances (example)
abundances = np.array([n.density for n in net.species])

# Total atoms of each element
total_atoms = density @ abundances

for i, element in enumerate(elem.elements):
    print(f"Total {element} atoms: {total_atoms[i]:.2e}")
```

### Matrix Visualization

```python
from jaff import Network
from jaff.elements import Elements
import pandas as pd

net = Network("networks/react_COthin")
elem = Elements(net)

# Create DataFrame for better visualization
density = elem.get_element_density_matrix()
species_names = [s.name for s in net.species]

df = pd.DataFrame(
    density,
    index=elem.elements,
    columns=species_names
)

print(df)
```

**Output**:
```
     CO  H2  H2O  CH4  OH
C     1   0    0    1   0
H     0   2    2    4   1
O     1   0    1    0   1
```

## Implementation Details

### Element Extraction Algorithm

The Elements class extracts elements from species using the following process:

1. **Iterate over all species**: Access each species in the network
2. **Get exploded representation**: Each species has an `exploded` attribute containing individual atoms
3. **Filter alphabetic characters**: Only alphabetic characters are considered element symbols
4. **Create unique set**: Remove duplicates and create a sorted list
5. **Store results**: Save element list and count

### Matrix Generation

Both matrix methods use similar algorithms:

**Truth Matrix**:
```python
for each element:
    for each species:
        matrix[element_idx][species_idx] = 1 if element in species else 0
```

**Density Matrix**:
```python
for each element:
    for each species:
        matrix[element_idx][species_idx] = count(element in species)
```

## Performance Considerations

- **Memory**: Matrices are stored as lists of lists (O(nelems × nspecies))
- **Computation**: Matrix generation is O(nelems × nspecies × atoms_per_species)
- **Caching**: Matrices are computed on-demand and not cached

For large networks (>1000 species), consider:
- Converting to NumPy arrays for faster operations
- Caching matrix results if used multiple times
- Using sparse matrices if many zeros

## See Also

- [Network API](network.md) - Chemical network management
- [Species API](species.md) - Individual species information
- [File Parser API](file-parser.md) - Using elements in templates
- [User Guide - Network Analysis](../tutorials/network-analysis.md) - Analysis examples
