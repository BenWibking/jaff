# Loading Networks

This guide covers how to load chemical reaction networks in JAFF from various file formats.

## Overview

JAFF can load chemical reaction networks from multiple file formats commonly used in astrochemistry. The `Network` class automatically detects the format and parses the file appropriately.

```python
from jaff import Network

# Load a network - format is auto-detected
net = Network("networks/react_COthin")
```

## Basic Loading

### Simple Loading

The simplest way to load a network:

```python
from jaff import Network

# Load network from file
net = Network("path/to/network.dat")

# Access network properties
print(f"Loaded: {net.label}")
print(f"Species: {len(net.species)}")
print(f"Reactions: {len(net.reactions)}")
```

### With Error Checking

Enable validation to catch issues:

```python
# Enable error checking
net = Network("mynetwork.dat", errors=True)
```

This will raise exceptions if the network has:
- Species that only appear as reactants (sinks)
- Species that only appear as products (sources)
- Duplicate reactions
- Isomer issues
- Invalid reaction formatting

### Custom Labels

Specify a custom label for the network:

```python
# Default label is the filename
net1 = Network("networks/react_COthin")
print(net1.label)  # "react_COthin"

# Custom label
net2 = Network("networks/react_COthin", label="CO_chemistry")
print(net2.label)  # "CO_chemistry"
```

## Supported Formats

JAFF automatically detects and parses multiple network file formats.

### JAFF Format (.dat)

JAFF's native format with simple, readable syntax:

```text
# Comments start with #
# Format: Reactants -> Products, rate_expression

H + O -> OH, 1.2e-10 * (tgas/300)^0.5
H2 + O -> OH + H, 3.4e-11 * exp(-500/tgas)
C + O2 -> CO + O, 5.6e-12
```

**Features:**
- Simple syntax
- Automatic species detection
- SymPy expressions for rates
- Comments with `#`

**Loading:**

```python
net = Network("mynetwork.dat")
```

### KROME Format

KROME network files with format specification:

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
1,H,O,,,OH,,,0,1e4,1.2e-10*(T/300)**0.5
2,H2,O,,,OH,H,,0,1e4,3.4e-11*exp(-500/T)

# Variables
@var:te=tgas*8.617343e-5
@var:invtgas=1.0/tgas
```

**Features:**
- Structured format with indices
- Temperature range (tmin, tmax)
- Variable definitions with `@var:`
- Custom format specification with `@format:`

**Loading:**

```python
net = Network("krome_network.dat")
# KROME format auto-detected from @format: line
```

### KIDA Format

Kinetic Database for Astrochemistry format:

```text
H + O -> OH : 1.2e-10 : 0.5 : 0.0
H2 + O -> OH + H : 3.4e-11 : 0.0 : 500.0
```

**Format:** `Reactants -> Products : α : β : γ`

Where rate = α × (T/300)^β × exp(-γ/T)

**Loading:**

```python
net = Network("kida_network.dat")
# Auto-detected from colon-separated format
```

### UDFA Format

UMIST Database for Astrochemistry format:

```text
H:O:OH:1.2e-10:0.5:0.0:0:1e4
H2:O:OH:H:3.4e-11:0.0:500.0:0:1e4
```

**Features:**
- Colon-separated values
- Temperature ranges
- Compact format

**Loading:**

```python
net = Network("udfa_network.dat")
```

### PRIZMO Format

PRIZMO format with variable blocks:

```text
VARIABLES{
    k1 = 1.2e-10
    k2 = 3.4e-11
    sqrtt = sqrt(tgas)
}

H + O -> OH, k1 * sqrtt
H2 + O -> OH + H, k2 * exp(-500/tgas)
```

**Features:**
- Variable definition blocks
- Arrow notation (`->`)
- Fortran-style expressions

**Loading:**

```python
net = Network("prizmo_network.dat")
# Auto-detected from VARIABLES{ block
```

### UCL_CHEM Format

UCL_CHEM format with NAN placeholders:

```text
H,O,NAN,OH,NAN,NAN,1.2e-10,0.5,0.0
H2,O,NAN,OH,H,NAN,3.4e-11,0.0,500.0
```

**Features:**
- Comma-separated values
- NAN placeholders for empty slots
- Compact reaction specification

**Loading:**

```python
net = Network("uclchem_network.dat")
# Auto-detected from ,NAN, patterns
```

## Advanced Loading

### Auxiliary Function Files

Use custom rate function definitions:

```python
# Load with auxiliary functions
net = Network(
    "network.dat",
    funcfile="aux_functions.txt"
)
```

**Auxiliary function file format:**

```text
# Define custom functions
function_name1 = expression1
function_name2 = expression2
```

### Hydrogen Nuclei Replacement

Control replacement of hydrogen nuclei density:

```python
# Enable replacement (default)
net = Network("network.dat", replace_nH=True)

# Disable replacement
net = Network("network.dat", replace_nH=False)
```

This affects how expressions like `get_hnuclei(n)` are handled.

### JAFF Binary Format

For faster loading of large networks, save to JAFF binary format:

```python
# First load and save
net = Network("large_network.dat")
net.to_jaff_file("large_network.jaff")

# Future loads are much faster
net = Network("large_network.jaff")
```

**Performance comparison:**
- Text format: ~10-30 seconds for large networks
- JAFF format: <1 second

## Error Handling

### Common Issues

**File Not Found:**

```python
try:
    net = Network("nonexistent.dat")
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

**Invalid Format:**

```python
try:
    net = Network("invalid.dat")
except ValueError as e:
    print(f"Parse error: {e}")
```

**Validation Errors:**

```python
try:
    net = Network("network.dat", errors=True)
except Exception as e:
    print(f"Validation error: {e}")
```

### Validation Warnings

When `errors=False` (default), validation issues produce warnings:

```python
net = Network("network.dat", errors=False)
# Output:
# WARNING: Species 'X' only appears as reactant
# WARNING: Duplicate reaction found: H + O -> OH
```

## Loading Multiple Networks

### Load and Compare

```python
# Load multiple networks
net1 = Network("version1.dat", label="v1")
net2 = Network("version2.dat", label="v2")

# Compare species
net1.compare_species(net2)

# Compare reactions
net1.compare_reactions(net2)
```

### Merge Networks

```python
# Load networks
net1 = Network("network1.dat")
net2 = Network("network2.dat")

# Combine species lists
all_species = list(set(
    [s.name for s in net1.species] +
    [s.name for s in net2.species]
))

print(f"Total unique species: {len(all_species)}")
```

## Inspecting Loaded Networks

### Basic Information

```python
net = Network("network.dat")

print(f"Label: {net.label}")
print(f"File: {net.file_name}")
print(f"Species count: {len(net.species)}")
print(f"Reaction count: {len(net.reactions)}")
```

### Species Details

```python
# List all species
for i, species in enumerate(net.species):
    print(f"{i}: {species.name} (mass={species.mass:.2f})")

# Find specific species
if "CO" in net.species_dict:
    idx = net.species_dict["CO"]
    co = net.species[idx]
    print(f"CO: index={idx}, mass={co.mass}")
```

### Reaction Details

```python
# List reactions
for i, reaction in enumerate(net.reactions[:10]):
    print(f"{i}: {reaction.verbatim}")

# Reaction types
reaction_types = {}
for r in net.reactions:
    rtype = r.rtype
    reaction_types[rtype] = reaction_types.get(rtype, 0) + 1

for rtype, count in reaction_types.items():
    print(f"{rtype}: {count} reactions")
```

### Network Statistics

```python
import numpy as np

# Species statistics
masses = [s.mass for s in net.species]
charges = [s.charge for s in net.species]

print(f"Average mass: {np.mean(masses):.2f} amu")
print(f"Mass range: {np.min(masses):.2f} - {np.max(masses):.2f}")
print(f"Neutral species: {sum(1 for c in charges if c == 0)}")
print(f"Ions: {sum(1 for c in charges if c != 0)}")

# Reaction statistics
print(f"Total reactions: {len(net.reactions)}")
print(f"Reactant matrix shape: {net.rlist.shape}")
print(f"Product matrix shape: {net.plist.shape}")
```

## Best Practices

### 1. Always Validate New Networks

```python
# First load with validation
net = Network("new_network.dat", errors=True)
```

### 2. Use JAFF Format for Large Networks

```python
# Convert once
net = Network("large_network.dat")
net.to_jaff_file("large_network.jaff")

# Use binary format thereafter
net = Network("large_network.jaff")
```

### 3. Cache Loaded Networks

```python
# Load once, use many times
_network_cache = {}

def get_network(filename):
    if filename not in _network_cache:
        _network_cache[filename] = Network(filename)
    return _network_cache[filename]

# Reuse cached networks
net = get_network("network.dat")
```

### 4. Check Species Before Using

```python
def safe_get_species(net, name):
    if name in net.species_dict:
        return net.species[net.species_dict[name]]
    else:
        print(f"Warning: Species '{name}' not in network")
        return None

co = safe_get_species(net, "CO")
```

### 5. Document Network Sources

```python
# Keep metadata
network_info = {
    "file": "react_COthin",
    "source": "KIDA database",
    "date": "2024-01-15",
    "description": "CO chemistry network",
    "label": net.label,
    "species": len(net.species),
    "reactions": len(net.reactions)
}
```

## Common Patterns

### Pattern 1: Batch Loading

```python
import glob

# Load all networks in directory
network_files = glob.glob("networks/*.dat")
networks = []

for file in network_files:
    try:
        net = Network(file, errors=False)
        networks.append(net)
        print(f"Loaded {net.label}: {len(net.species)} species")
    except Exception as e:
        print(f"Failed to load {file}: {e}")
```

### Pattern 2: Format Detection

```python
def detect_format(filename):
    """Detect network file format."""
    with open(filename) as f:
        content = f.read()
    
    if "@format:" in content:
        return "KROME"
    elif "VARIABLES{" in content:
        return "PRIZMO"
    elif ",NAN," in content:
        return "UCL_CHEM"
    elif " : " in content and "->" in content:
        return "KIDA or UDFA"
    elif "->" in content:
        return "JAFF or PRIZMO"
    else:
        return "Unknown"

format_type = detect_format("network.dat")
print(f"Detected format: {format_type}")
```

### Pattern 3: Network Filtering

```python
def filter_species(net, min_mass=None, max_mass=None):
    """Filter species by mass range."""
    filtered = []
    for species in net.species:
        if min_mass and species.mass < min_mass:
            continue
        if max_mass and species.mass > max_mass:
            continue
        filtered.append(species)
    return filtered

# Get species between 10 and 50 amu
mid_mass_species = filter_species(net, min_mass=10, max_mass=50)
```

## Troubleshooting

### Issue: "Species not found"

```python
# Check if species exists
if "CO" not in net.species_dict:
    print("CO not in network")
    print("Available species:", [s.name for s in net.species[:10]])
```

### Issue: "Parsing error"

```python
# Try with error checking disabled
try:
    net = Network("problematic.dat", errors=False)
    print("Loaded with warnings")
except Exception as e:
    print(f"Failed: {e}")
    # Inspect file manually
```

### Issue: "Slow loading"

```python
# Convert to JAFF format
import time

start = time.time()
net = Network("large.dat")
print(f"Text format: {time.time() - start:.2f}s")

net.to_jaff_file("large.jaff")

start = time.time()
net2 = Network("large.jaff")
print(f"JAFF format: {time.time() - start:.2f}s")
```

## See Also

- [Network Formats](network-formats.md) - Detailed format specifications
- [Network API](../api/network.md) - Network class reference
- [Quick Start](../getting-started/quickstart.md) - Getting started guide
- [Basic Concepts](../getting-started/concepts.md) - Understanding networks

---

**Next:** Learn about [Network File Formats](network-formats.md) in detail.
