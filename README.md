# JAFF
(Just Another Fancy Format)

An astrochemical network parser that supports multiple reaction network formats including KIDA, UDFA, PRIZMO, KROME, and UCLCHEM.

## Installation

### From source
```bash
git clone https://github.com/tgrassi/jaff.git
cd jaff
pip install .
```

### For development
```bash
git clone https://github.com/tgrassi/jaff.git
cd jaff
pip install -e .  # Editable install
```

## Quick Start

### Command Line Usage

After installation, you can use the `jaff` command:

```bash
# Load and validate a network file
jaff networks/gas_reactions_kida.uva.2024.in

# Check mass and charge conservation
jaff networks/react_COthin --check-mass --check-charge

# List all species and reactions
jaff networks/test.dat --list-species --list-reactions

# Exit on validation errors
jaff network_file.dat --errors
```

### Python API Usage

```python
from jaff import Network

# Load a chemical network
network = Network("path/to/network_file.dat")

# Access species
for species in network.species:
    print(f"{species.name}: mass={species.mass}, charge={species.charge}")

# Access reactions
for reaction in network.reactions:
    print(f"{reaction}")
    
# Check conservation laws
network.check_mass(errors=False)
network.check_charge(errors=False)

# Generate ODEs for the network
odes = network.get_odes()
```

## Features

- **Multi-format support**: Automatically detects and parses KIDA, UDFA, PRIZMO, KROME, and UCLCHEM formats
- **Validation**: Checks for mass and charge conservation in reactions
- **Species analysis**: Automatic extraction of elemental composition and properties
- **Rate calculations**: Temperature-dependent rate coefficient evaluation
- **ODE generation**: Creates differential equations for chemical kinetics

## Supported Network Formats

- **KIDA**: Kinetic Database for Astrochemistry format
    Reference: [A&A, 689, A63 (2024)](https://doi.org/10.1051/0004-6361/202450606)
- **UDFA**: UMIST Database for Astrochemistry format
    Reference: [A&A, 682, A109 (2024)](https://doi.org/10.1051/0004-6361/202346908)
- **PRIZMO**: Uses `->` separator with `VARIABLES{}` blocks
    Reference:[MNRAS 494, 4471–4491 (2020)](https://doi.org/10.1093/mnras/staa971)
- **KROME**: Comma-separated values with `@format:` header
    Reference: [MNRAS 439, 2386–2419 (2014)](https://doi.org/10.1093/mnras/stu114)
- **UCLCHEM**: Comma-separated with `,NAN,` marker (UNDER CONSTRUCTION)     
    Reference: [J. Holdship et al 2017 AJ 154 38](https://doi.org/10.3847/1538-3881/aa773f)

## Primitive Variables

The following variables are recognized in rate expressions:

- `tgas`: gas temperature, K      
- `av`: visual extinction, Draine units      
- `crate`: cosmic rays ionization rate of H2, 1/s     
- `ntot`: total number density, 1/cm3      
- `hnuclei`: H nuclei number density, 1/cm3     
- `d2g`: dust-to-gas mass ratio     

## Examples

Example network files can be found in the `networks/` directory.

## Development

To contribute or modify JAFF:

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/jaff

# Lint code
ruff check src/jaff
```

-----------------------------
![xkcd:927](./assets/xkcd.png)               
![https://xkcd.com/927/](https://xkcd.com/927/)
