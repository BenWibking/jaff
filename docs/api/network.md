# Network API Reference

The `Network` class is the core of JAFF, representing a chemical reaction network loaded from a file.

## Overview

The `Network` class loads and validates chemical reaction networks, providing access to species, reactions, and network properties. It automatically parses various network file formats and validates the network structure.

```python
from jaff import Network

# Load a network
net = Network("networks/react_COthin")

# Access properties
print(f"Species: {len(net.species)}")
print(f"Reactions: {len(net.reactions)}")
print(f"Label: {net.label}")
```

## Class Reference

```python
class Network:
    """
    Main class for chemical reaction networks.

    Attributes:
        label (str): Network name/identifier
        species (list): List of Species objects
        reactions (list): List of Reaction objects
        fname (str): Source filename
        rates (dict): Rate constants dictionary
    """
```

        - get_number_of_species
        - get_species_index
        - get_species_object
        - get_reaction_index
        - get_reaction_by_verbatim
        - get_sfluxes
        - get_sodes
        - compare_reactions
        - compare_species
        - check_sink_sources
        - check_recombinations
        - check_isomers
        - check_unique_reactions

## Constructor

### `Network(fname, errors=False, label=None, funcfile=None, replace_nH=True)`

Create a Network object by loading a chemical reaction network file.

**Parameters:**

- `fname` (str): Path to the network file
- `errors` (bool): If True, raise exceptions on validation errors. Default: False
- `label` (str): Custom label for the network. Default: filename without extension
- `funcfile` (str): Path to auxiliary function file for custom rate expressions. Default: None
- `replace_nH` (bool): Replace hydrogen nuclei density expressions. Default: True

**Returns:**

- `Network`: Initialized network object

**Raises:**

- `FileNotFoundError`: If network file doesn't exist
- `ValueError`: If network file format is invalid
- `Exception`: If errors=True and network has validation issues

**Example:**

```python
from jaff import Network

# Basic usage
net = Network("networks/react_COthin")

# With error checking
net = Network("networks/mynetwork.dat", errors=True)

# With custom label
net = Network("networks/react_COthin", label="CO_chemistry")

# With auxiliary functions
net = Network("networks/react_COthin", funcfile="aux_funcs.txt")
```

## Attributes

### Core Attributes

| Attribute        | Type               | Description                                     |
| ---------------- | ------------------ | ----------------------------------------------- |
| `species`        | `list[Species]`    | List of all species in the network              |
| `reactions`      | `list[Reaction]`   | List of all reactions in the network            |
| `species_dict`   | `dict[str, int]`   | Dictionary mapping species names to indices     |
| `reactions_dict` | `dict[str, int]`   | Dictionary mapping reaction verbatim to indices |
| `label`          | `str`              | Network identifier/label                        |
| `file_name`      | `str`              | Path to the original network file               |
| `mass_dict`      | `dict[str, float]` | Atomic mass dictionary                          |
| `rlist`          | `np.ndarray`       | Reactant matrix (nreact × nspec)                |
| `plist`          | `np.ndarray`       | Product matrix (nreact × nspec)                 |

### Energy Attributes

| Attribute    | Type         | Description              |
| ------------ | ------------ | ------------------------ |
| `dEdt_chem`  | `sympy.Expr` | Chemical energy equation |
| `dEdt_other` | `sympy.Expr` | Other energy terms       |

### Photochemistry

| Attribute        | Type             | Description            |
| ---------------- | ---------------- | ---------------------- |
| `photochemistry` | `Photochemistry` | Photochemistry handler |

## Methods

### Species Access Methods

#### `get_number_of_species()`

Get the total number of species in the network.

**Returns:**

- `int`: Number of species

**Example:**

```python
nspec = net.get_number_of_species()
print(f"Network has {nspec} species")
```

#### `get_species_index(name)`

Get the array index of a species by name.

**Parameters:**

- `name` (str): Species name

**Returns:**

- `int`: Species index in the species array

**Raises:**

- `KeyError`: If species name not found

**Example:**

```python
idx = net.get_species_index("CO")
print(f"CO is at index {idx}")
```

#### `get_species_object(name)`

Get the Species object by name.

**Parameters:**

- `name` (str): Species name

**Returns:**

- `Species`: The species object

**Raises:**

- `KeyError`: If species name not found

**Example:**

```python
co = net.get_species_object("CO")
print(f"Mass: {co.mass}, Charge: {co.charge}")
```

### Reaction Access Methods

#### `get_reaction_index(name)`

Get the array index of a reaction by its verbatim string.

**Parameters:**

- `name` (str): Reaction verbatim (e.g., "H + O -> OH")

**Returns:**

- `int`: Reaction index

**Raises:**

- `KeyError`: If reaction not found

**Example:**

```python
idx = net.get_reaction_index("H + O -> OH")
print(f"Reaction is at index {idx}")
```

#### `get_reaction_by_verbatim(verbatim, rtype=None)`

Get a Reaction object by its verbatim string.

**Parameters:**

- `verbatim` (str): Reaction string (e.g., "H + O -> OH")
- `rtype` (str): Optional reaction type filter. Default: None

**Returns:**

- `Reaction` or `None`: The matching reaction or None if not found

**Example:**

```python
reaction = net.get_reaction_by_verbatim("H + O -> OH")
if reaction:
    print(f"Rate type: {reaction.rtype}")
```

#### `get_reaction_verbatim(idx)`

Get the verbatim string representation of a reaction.

**Parameters:**

- `idx` (int): Reaction index

**Returns:**

- `str`: Reaction verbatim string

**Example:**

```python
verbatim = net.get_reaction_verbatim(0)
print(f"First reaction: {verbatim}")
```

### Symbolic Expression Methods

#### `get_sfluxes()`

Get symbolic expressions for reaction fluxes.

**Returns:**

- `list[sympy.Expr]`: List of flux expressions for each species

**Description:**

Returns the net flux for each species from all reactions as symbolic SymPy expressions. These represent the rate of change of each species concentration.

**Example:**

```python
fluxes = net.get_sfluxes()
for i, flux in enumerate(fluxes[:3]):
    print(f"Species {i} flux: {flux}")
```

#### `get_sodes()`

Get symbolic ordinary differential equations for the network.

**Returns:**

- `list[sympy.Expr]`: List of ODE expressions (dn_i/dt) for each species

**Description:**

Returns the complete ODE system as symbolic SymPy expressions. These can be used for symbolic manipulation or code generation.

**Example:**

```python
odes = net.get_sodes()
for i, ode in enumerate(odes[:3]):
    print(f"dn_{i}/dt = {ode}")
```

### Validation Methods

#### `check_sink_sources(errors)`

Check for species that only appear as reactants (sinks) or products (sources).

**Parameters:**

- `errors` (bool): If True, raise exception on finding sinks/sources

**Description:**

Validates that species participate in both production and destruction reactions. Warns or errors if pure sinks or sources are found.

**Example:**

```python
net.check_sink_sources(errors=True)
```

#### `check_recombinations(errors)`

Check for proper recombination reaction formatting.

**Parameters:**

- `errors` (bool): If True, raise exception on finding issues

**Description:**

Validates recombination reactions follow proper conventions.

#### `check_isomers(errors)`

Check for isomer issues in the network.

**Parameters:**

- `errors` (bool): If True, raise exception on finding isomer issues

**Description:**

Identifies species with identical composition but different names.

#### `check_unique_reactions(errors)`

Check that all reactions are unique (no duplicates).

**Parameters:**

- `errors` (bool): If True, raise exception on finding duplicates

**Description:**

Validates that the network doesn't contain duplicate reactions.

**Example:**

```python
# Run all validation checks
net.check_sink_sources(errors=False)
net.check_recombinations(errors=False)
net.check_isomers(errors=False)
net.check_unique_reactions(errors=False)
```

### Comparison Methods

#### `compare_reactions(other, verbosity=1)`

Compare reactions between two networks.

**Parameters:**

- `other` (Network): Another network to compare with
- `verbosity` (int): Level of output detail (0=quiet, 1=normal, 2=verbose)

**Description:**

Compares reaction lists and identifies differences between networks.

**Example:**

```python
net1 = Network("networks/version1.dat")
net2 = Network("networks/version2.dat")
net1.compare_reactions(net2, verbosity=2)
```

#### `compare_species(other, verbosity=1)`

Compare species lists between two networks.

**Parameters:**

- `other` (Network): Another network to compare with
- `verbosity` (int): Level of output detail

**Example:**

```python
net1.compare_species(net2, verbosity=1)
```

### Serialization Methods

#### `to_jaff_file(filename)`

Save the network to a JAFF format file.

**Parameters:**

- `filename` (str): Output file path (will be gzip-compressed JSON)

**Description:**

Serializes the network to a compressed JSON format for fast loading.

**Example:**

```python
net.to_jaff_file("mynetwork.jaff")

# Load it back
net2 = Network("mynetwork.jaff")
```

## Supported File Formats

The Network class automatically detects and parses various file formats:

### JAFF Format

Native JAFF format with simple reaction syntax:

```text
# Species are auto-detected from reactions
H + O -> OH, 1.2e-10 * (tgas/300)^0.5
H2 + O -> OH + H, 3.4e-11 * exp(-500/tgas)
```

### KROME Format

KROME network files with `@format:` specification:

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
1,H,O,,,OH,,,0,1e4,1.2e-10*(T/300)**0.5
```

### KIDA Format

Kinetic Database for Astrochemistry format:

```text
H + O -> OH : 1.2e-10 : 0.5 : 0.0
```

### UDFA Format

UMIST Database for Astrochemistry format with `:` separators.

### PRIZMO Format

PRIZMO format with variable definitions:

```text
VARIABLES{
    k1 = 1.2e-10
}

H + O -> OH, k1 * sqrt(tgas)
```

### UCL_CHEM Format

UCL_CHEM format with NAN placeholders.

## Matrix Properties

### Reactant Matrix (`rlist`)

A matrix of shape `(nreact, nspec)` where `rlist[i, j]` is the stoichiometric coefficient of species `j` as a reactant in reaction `i`.

```python
import numpy as np

# Check which species are reactants in reaction 0
reactants = net.rlist[0]
for i, coef in enumerate(reactants):
    if coef > 0:
        print(f"{net.species[i].name}: {coef}")
```

### Product Matrix (`plist`)

A matrix of shape `(nreact, nspec)` where `plist[i, j]` is the stoichiometric coefficient of species `j` as a product in reaction `i`.

```python
# Check products of reaction 0
products = net.plist[0]
for i, coef in enumerate(products):
    if coef > 0:
        print(f"{net.species[i].name}: {coef}")
```

## Usage Examples

### Example 1: Basic Network Loading

```python
from jaff import Network

# Load network
net = Network("networks/react_COthin")

# Display info
print(f"Network: {net.label}")
print(f"Species: {len(net.species)}")
print(f"Reactions: {len(net.reactions)}")

# List species
print("\nFirst 5 species:")
for sp in net.species[:5]:
    print(f"  {sp.name}: mass={sp.mass:.2f}, charge={sp.charge}")
```

### Example 2: Finding Species

```python
# Fast lookup using dictionary
idx = net.species_dict["CO"]
co = net.species[idx]

# Or use helper method
co = net.get_species_object("CO")

print(f"CO: index={co.index}, mass={co.mass}, charge={co.charge}")
```

### Example 3: Exploring Reactions

```python
# Iterate through reactions
for i, reaction in enumerate(net.reactions[:5]):
    print(f"{i}: {reaction.verbatim}")

    # Calculate rate at 100 K
    k = reaction.rate(100.0)
    print(f"   Rate at 100K: {k:.2e}")
```

### Example 4: Network Validation

```python
# Load with full validation
try:
    net = Network("mynetwork.dat", errors=True)
    print("Network is valid!")
except Exception as e:
    print(f"Validation error: {e}")
```

### Example 5: Element Conservation

```python
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)

print(f"Elements: {elem.elements}")
print(f"Number of elements: {elem.nelems}")

# Get element density matrix
density = elem.get_element_density_matrix()
print(f"Density matrix shape: {len(density)} × {len(density[0])}")
```

### Example 6: Comparing Networks

```python
# Load two versions of a network
net_old = Network("networks/version1.dat", label="v1")
net_new = Network("networks/version2.dat", label="v2")

# Compare them
net_old.compare_species(net_new)
net_old.compare_reactions(net_new)
```

### Example 7: Symbolic ODEs

```python
# Get symbolic ODE expressions
odes = net.get_sodes()

# Print first 3 ODEs
for i, ode in enumerate(odes[:3]):
    species = net.species[i]
    print(f"d{species.name}/dt = {ode}")
```

### Example 8: Network Export

```python
# Save to JAFF format
net.to_jaff_file("output/network.jaff")

# Reload (much faster than parsing original format)
net2 = Network("output/network.jaff")
```

## Best Practices

### 1. Always Validate New Networks

```python
# Enable error checking for new networks
net = Network("mynetwork.dat", errors=True)
```

### 2. Use Species Dictionary for Lookups

```python
# Fast O(1) lookup
idx = net.species_dict["CO"]

# Slower O(n) search - avoid
for sp in net.species:
    if sp.name == "CO":
        idx = sp.index
```

### 3. Cache Network Objects

```python
# Load once, reuse many times
net = Network("networks/react_COthin")

# Use net for multiple code generations
from jaff import Codegen
cg_cpp = Codegen(network=net, lang="c++")
cg_f90 = Codegen(network=net, lang="f90")
```

### 4. Handle Missing Species Gracefully

```python
try:
    idx = net.species_dict["UnknownSpecies"]
except KeyError:
    print("Species not found in network")
```

### 5. Use JAFF Format for Performance

```python
# Convert to JAFF format for faster loading
net = Network("large_network.dat")
net.to_jaff_file("large_network.jaff")

# Future loads are much faster
net = Network("large_network.jaff")
```

## Common Patterns

### Pattern 1: Filter Reactions by Type

```python
# Get all photo-reactions
photo_reactions = [r for r in net.reactions if r.rtype == "photo"]
print(f"Found {len(photo_reactions)} photo-reactions")
```

### Pattern 2: Find Species by Element

```python
from jaff.elements import Elements

elem = Elements(net)
truth_matrix = elem.get_element_truth_matrix()

# Find all species containing carbon
carbon_idx = elem.elements.index("C")
carbon_species = [
    net.species[i] for i in range(len(net.species))
    if truth_matrix[i][carbon_idx]
]
```

### Pattern 3: Calculate Network Statistics

```python
# Species statistics
masses = [sp.mass for sp in net.species]
charges = [sp.charge for sp in net.species]

print(f"Average mass: {np.mean(masses):.2f} amu")
print(f"Charged species: {sum(1 for c in charges if c != 0)}")

# Reaction statistics
reaction_types = {}
for r in net.reactions:
    reaction_types[r.rtype] = reaction_types.get(r.rtype, 0) + 1

for rtype, count in reaction_types.items():
    print(f"{rtype}: {count} reactions")
```

## Performance Notes

- **Loading**: First load parses the file format (slow). Use `to_jaff_file()` to create a fast-loading binary format.
- **Species Lookup**: Use `species_dict` for O(1) lookups instead of iterating.
- **Validation**: Disable `errors=False` for faster loading if network is already validated.
- **Large Networks**: Networks with 1000+ species/reactions may take several seconds to load.

## See Also

- [Species API](../api/species.md) - Species class documentation
- [Reaction API](../api/reactions.md) - Reaction class documentation
- [Elements API](elements.md) - Element analysis
- [Codegen API](codegen.md) - Code generation
- [File Parser API](file-parser.md) - Template processing

---

**Next**: Learn about [Code Generation](codegen.md) with the Codegen class.
