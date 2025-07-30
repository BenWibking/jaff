# JAFF Documentation

**Just Another Fancy Format** - An astrochemical network parser that supports multiple reaction network formats.

## Overview

JAFF is a Python library designed to parse and analyze astrochemical reaction networks from various formats including KIDA, UDFA, PRIZMO, KROME, and UCLCHEM. It provides tools for:

- Loading and parsing chemical reaction networks
- Validating reactions (sink/source detection, recombinations, isomers, duplicates)
- Analyzing species properties and compositions
- Generating differential equations for chemical kinetics
- Temperature-dependent rate coefficient calculations

## Key Features

- **Multi-format support**: Automatically detects and parses multiple network formats
- **Validation tools**: Built-in checks for network consistency
- **Species analysis**: Automatic extraction of elemental composition and properties
- **Rate calculations**: Temperature-dependent rate coefficient evaluation
- **ODE generation**: Creates differential equations for chemical kinetics modeling

## Quick Example

```python
from jaff import Network

# Load a chemical network
network = Network("path/to/network_file.dat")

# Access species and reactions
print(f"Network contains {len(network.species)} species")
print(f"Network contains {len(network.reactions)} reactions")

# Generate rate coefficient table
rates = network.get_table(T_min=10, T_max=1000, nT=64)
```

## Getting Started

- [Installation Guide](installation.md) - How to install JAFF
- [Quick Start](quickstart.md) - Basic usage examples
- [Command Line Interface](cli.md) - Using JAFF from the command line
- [Python API](api.md) - Programming with JAFF

## Supported Formats

JAFF can automatically detect and parse the following reaction network formats:

- **KIDA**: Kinetic Database for Astrochemistry format
- **UDFA**: UMIST Database for Astrochemistry format
- **PRIZMO**: Uses `->` separator with `VARIABLES{}` blocks
- **KROME**: Comma-separated values with `@format:` header
- **UCLCHEM**: Comma-separated with `,NAN,` marker

Learn more about [supported formats](formats.md).