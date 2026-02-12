# Species API Reference

The `Species` class represents a chemical species in a reaction network. It encapsulates information about a species' name, initial concentration, and optional metadata.

## Overview

Species are the fundamental building blocks of chemical reaction networks. Each species has:

- A unique name/identifier
- An optional initial concentration
- Optional metadata for tracking additional properties

## Class Definition

```python
class Species:
    """
    Represents a chemical species in a reaction network.

    Attributes:
        name (str): Species name/identifier
        index (int): Zero-based index in the species list
        mass (dict): Dictionary of element masses
        charge (int): Electrical charge
        exploded (list): Parsed element composition
    """
```

## Usage Examples

### Creating a Species

```python
from jaff.species import Species

# Create a simple species
h2o = Species("H2O")

# Create a species with initial concentration
glucose = Species("glucose", initial_concentration=1.0)

# Create a species with metadata
enzyme = Species(
    "enzyme_A",
    initial_concentration=0.01,
    metadata={"compartment": "cytoplasm", "mw": 45000}
)
```

### Accessing Properties

```python
species = Species("ATP", initial_concentration=2.5)

# Get species name
print(species.name)  # "ATP"

# Get initial concentration
print(species.initial_concentration)  # 2.5

# Check if concentration is set
if species.has_initial_concentration():
    print(f"{species.name}: {species.initial_concentration} M")
```

### Species Comparison

```python
s1 = Species("A", initial_concentration=1.0)
s2 = Species("A", initial_concentration=2.0)
s3 = Species("B", initial_concentration=1.0)

# Species are equal if names match (concentration doesn't matter)
print(s1 == s2)  # True
print(s1 == s3)  # False

# Species can be used in sets and dicts
species_set = {s1, s2, s3}
print(len(species_set))  # 2 (s1 and s2 are same species)
```

### Working with Metadata

```python
# Add metadata during creation
protein = Species(
    "protein_X",
    metadata={
        "type": "enzyme",
        "ec_number": "1.2.3.4",
        "organism": "E. coli"
    }
)

# Access metadata
ec = protein.metadata.get("ec_number")
organism = protein.metadata["organism"]

# Check for metadata key
if "type" in protein.metadata:
    print(f"Type: {protein.metadata['type']}")
```

## Properties and Methods

### Properties

#### `name`

The unique identifier for the species.

**Type:** `str`

**Example:**

```python
s = Species("glucose")
print(s.name)  # "glucose"
```

#### `initial_concentration`

The initial concentration of the species (optional).

**Type:** `float | None`

**Example:**

```python
s1 = Species("A", initial_concentration=1.5)
s2 = Species("B")

print(s1.initial_concentration)  # 1.5
print(s2.initial_concentration)  # None
```

#### `metadata`

Dictionary containing additional properties about the species.

**Type:** `dict`

**Example:**

```python
s = Species("enzyme", metadata={"compartment": "nucleus"})
print(s.metadata)  # {"compartment": "nucleus"}
```

### Methods

#### `has_initial_concentration()`

Check if the species has an initial concentration set.

**Returns:** `bool`

**Example:**

```python
s1 = Species("A", initial_concentration=1.0)
s2 = Species("B")

print(s1.has_initial_concentration())  # True
print(s2.has_initial_concentration())  # False
```

#### `to_dict()`

Convert the species to a dictionary representation.

**Returns:** `dict` - Dictionary containing species data

**Example:**

```python
s = Species("ATP", initial_concentration=2.5, metadata={"type": "nucleotide"})
data = s.to_dict()
# Returns:
# {
#     "name": "ATP",
#     "initial_concentration": 2.5,
#     "metadata": {"type": "nucleotide"}
# }
```

#### `from_dict(data)`

Create a Species instance from a dictionary.

**Parameters:**

- `data` (dict): Dictionary containing species information

**Returns:** `Species` - New Species instance

**Example:**

```python
data = {
    "name": "glucose",
    "initial_concentration": 5.0,
    "metadata": {"formula": "C6H12O6"}
}

species = Species.from_dict(data)
print(species.name)  # "glucose"
print(species.initial_concentration)  # 5.0
```

#### `copy()`

Create a deep copy of the species.

**Returns:** `Species` - Copy of the species

**Example:**

```python
original = Species("A", initial_concentration=1.0, metadata={"x": 1})
copy = original.copy()

# Modify copy without affecting original
copy.initial_concentration = 2.0
copy.metadata["x"] = 2

print(original.initial_concentration)  # 1.0
print(copy.initial_concentration)  # 2.0
```

## Special Methods

### String Representation

```python
s1 = Species("ATP")
s2 = Species("glucose", initial_concentration=5.0)

print(str(s1))   # "Species(ATP)"
print(repr(s1))  # "Species('ATP', initial_concentration=None)"

print(str(s2))   # "Species(glucose, C0=5.0)"
print(repr(s2))  # "Species('glucose', initial_concentration=5.0)"
```

### Hashing and Equality

Species objects are hashable and can be used in sets and as dictionary keys:

```python
species_dict = {
    Species("A"): "reactant",
    Species("B"): "product"
}

species_set = {Species("A"), Species("B"), Species("A")}
print(len(species_set))  # 2
```

**Note:** Species equality is based solely on the name. Two species with the same name but different concentrations are considered equal.

## Integration with Networks

Species objects are typically created and managed through the Network class:

```python
from jaff.network import Network

network = Network()

# Add species
network.add_species("A", initial_concentration=1.0)
network.add_species("B", initial_concentration=2.0)

# Get species
species_a = network.get_species("A")
print(species_a.name)  # "A"
print(species_a.initial_concentration)  # 1.0

# List all species
all_species = network.species
for sp in all_species:
    print(f"{sp.name}: {sp.initial_concentration}")
```

## Common Patterns

### Batch Creation

```python
# Create multiple species from a list
species_names = ["A", "B", "C", "D"]
species_list = [Species(name) for name in species_names]

# Create species with concentrations
initial_concs = {"A": 1.0, "B": 2.0, "C": 0.5}
species_dict = {
    name: Species(name, initial_concentration=conc)
    for name, conc in initial_concs.items()
}
```

### Species Validation

```python
def validate_species(species: Species) -> bool:
    """Validate species has required properties."""
    if not species.name:
        return False

    if species.has_initial_concentration():
        if species.initial_concentration < 0:
            return False

    return True

s = Species("ATP", initial_concentration=1.0)
print(validate_species(s))  # True
```

### Filtering Species

```python
species_list = [
    Species("A", initial_concentration=1.0),
    Species("B", initial_concentration=0.0),
    Species("C"),
    Species("D", initial_concentration=2.5),
]

# Filter species with concentrations
has_conc = [s for s in species_list if s.has_initial_concentration()]

# Filter species with non-zero concentrations
nonzero = [
    s for s in species_list
    if s.has_initial_concentration() and s.initial_concentration > 0
]
```

## Serialization

### JSON Export/Import

```python
import json

# Export to JSON
species = Species("glucose", initial_concentration=5.0,
                 metadata={"formula": "C6H12O6"})
json_str = json.dumps(species.to_dict(), indent=2)

# Import from JSON
data = json.loads(json_str)
restored = Species.from_dict(data)
```

### YAML Export/Import

```python
import yaml

# Export to YAML
species_data = species.to_dict()
yaml_str = yaml.dump(species_data)

# Import from YAML
loaded_data = yaml.safe_load(yaml_str)
restored = Species.from_dict(loaded_data)
```

## Error Handling

```python
# Invalid species name
try:
    s = Species("")  # May raise ValueError
except ValueError as e:
    print(f"Error: {e}")

# Invalid concentration
try:
    s = Species("A", initial_concentration="invalid")
except TypeError as e:
    print(f"Error: {e}")

# Handle missing data in from_dict
try:
    data = {"initial_concentration": 1.0}  # Missing 'name'
    s = Species.from_dict(data)
except KeyError as e:
    print(f"Missing required field: {e}")
```

## Best Practices

### Naming Conventions

```python
# Use descriptive, consistent names
good_names = [
    Species("glucose"),
    Species("ATP"),
    Species("enzyme_hexokinase"),
    Species("Ca2+"),
]

# Avoid ambiguous or inconsistent names
# Bad: Species("s1"), Species("x"), Species("thing")
```

### Initial Concentrations

```python
# Set initial concentrations when creating the species
s1 = Species("A", initial_concentration=1.0)

# Don't modify concentration directly (immutable pattern)
# Instead, create a new species or update through network
```

### Metadata Usage

```python
# Use metadata for additional properties
species = Species(
    "protein_kinase",
    metadata={
        "type": "enzyme",
        "compartment": "cytoplasm",
        "kcat": 100.0,  # turnover number
        "km": 0.1,      # Michaelis constant
        "notes": "Regulated by phosphorylation"
    }
)

# Access metadata safely
compartment = species.metadata.get("compartment", "unknown")
```

## Related Classes

- [`Network`](network.md) - Container for species and reactions
- [`Reaction`](reaction.md) - Represents reactions between species
- [`Element`](elements.md) - AST elements for code generation

## See Also

- [User Guide: Species](../user-guide/species.md)
- [User Guide: Loading Networks](../user-guide/loading-networks.md)
- [Tutorial: Basic Usage](../tutorials/basic-usage.md)
