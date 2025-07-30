# Python API

## Core Classes

### Network Class

The main class for loading and working with chemical networks.

```python
from jaff import Network

# Initialize a network
network = Network(fname, errors=False, label=None)
```

**Parameters:**
- `fname` (str): Path to the network file
- `errors` (bool): If True, exit on validation errors (default: False)
- `label` (str): Custom label for the network (default: filename)

### Species Access

```python
# Access species list
species_list = network.species

# Get number of species
n_species = len(network.species)

# Get species by name
species = network.get_species_object("CO")

# Get species index
idx = network.get_species_index("CO")
```

### Reaction Access

```python
# Access reactions list
reactions_list = network.reactions

# Get number of reactions
n_reactions = len(network.reactions)

# Get reaction by verbatim string
idx = network.get_reaction_index("CO + H+ -> HCO+ + photon")
```

### Rate Table Generation

Generate temperature-dependent rate coefficient tables:

```python
rates = network.get_table(
    T_min=10,           # Minimum temperature (K)
    T_max=1000,         # Maximum temperature (K)  
    nT=64,              # Initial number of temperature points
    err_tol=0.01,       # Relative error tolerance
    rate_min=1e-30,     # Minimum rate for error calculation
    rate_max=1e100,     # Maximum rate (clipped)
    verbose=False       # Print adaptive refinement info
)
```

**Returns:** `numpy.ndarray` with shape `(n_reactions, n_temperatures)`

### Network Comparison

Compare two networks:

```python
network1 = Network("file1.dat")
network2 = Network("file2.dat")

# Compare reactions
network1.compare_reactions(network2, verbosity=1)

# Compare species
network1.compare_species(network2, verbosity=1)
```

## Species Properties

Individual species objects have these attributes:

```python
species = network.get_species_object("H2O")

print(species.name)        # Species name
print(species.mass)        # Molecular mass
print(species.charge)      # Electric charge
print(species.index)       # Index in species list
print(species.exploded)    # Elemental composition
print(species.latex)       # LaTeX representation
```

## Reaction Properties

Individual reaction objects have these attributes:

```python
reaction = network.reactions[0]

print(reaction.reactants)  # List of reactant Species objects
print(reaction.products)   # List of product Species objects
print(reaction.rate)       # Sympy rate expression
print(reaction.tmin)       # Minimum temperature (if set)
print(reaction.tmax)       # Maximum temperature (if set)
```

## Utility Methods

```python
# Get LaTeX representation of species
latex_str = network.get_latex("H2O", dollars=True)

# Get reaction verbatim string
verbatim = network.get_reaction_verbatim(idx)

# Check if networks have common elements
# (methods exist but require careful examination of their implementation)
```

## Primitive Variables

Rate expressions can contain these primitive variables:

- `tgas`: Gas temperature (K)
- `av`: Visual extinction (Draine units)
- `crate`: Cosmic ray ionization rate of H₂ (s⁻¹)
- `ntot`: Total number density (cm⁻³)
- `hnuclei`: H nuclei number density (cm⁻³)
- `d2g`: Dust-to-gas mass ratio