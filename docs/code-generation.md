# Code Generation

JAFF includes a plugin-based code generation system that can create ODE solver implementations from your chemical network in different programming languages.

## Overview

The `Builder` class provides a simple interface to generate complete ODE solver code from a loaded network. Currently supported templates include:

- **python_solve_ivp**: Python solver using SciPy's `solve_ivp`
- **fortran_dlsodes**: Fortran solver using the DLSODES sparse ODE solver

## Basic Usage

```python
from jaff import Network
from jaff.builder import Builder

# Load your network
network = Network("network.dat")

# Create a builder instance
builder = Builder(network)

# Generate Python solver code
builder.build(template="python_solve_ivp")

# Generate Fortran solver code
builder.build(template="fortran_dlsodes")
```

Generated code is placed in the `builds/` directory within the JAFF installation.

## Python Solver Template

The `python_solve_ivp` template generates a complete Python solver with the following structure:

### Generated Files

- `commons.py`: Common variables and species/reaction indices
- `rates.py`: Rate coefficient calculation functions
- `fluxes.py`: Flux calculation for each reaction
- `ode.py`: ODE right-hand side function
- `main.py`: Example solver implementation

### Example Usage

After generation, you can use the solver like this:

```python
# In the builds directory
from ode import ode_rhs
from scipy.integrate import solve_ivp
import numpy as np

# Initial conditions
n_species = 50  # Number from your network
y0 = np.ones(n_species) * 1e-10  # Initial abundances

# Time span
t_span = (0, 1e6)  # seconds

# Physical parameters
params = {
    'tgas': 100.0,    # Temperature (K)
    'av': 1.0,        # Visual extinction
    'crate': 1e-17,   # Cosmic ray rate
    'ntot': 1e4       # Total density (cm^-3)
}

# Solve ODEs
sol = solve_ivp(
    lambda t, y: ode_rhs(t, y, **params),
    t_span, 
    y0,
    method='BDF',
    rtol=1e-8,
    atol=1e-20
)
```

## Fortran Solver Template

The `fortran_dlsodes` template generates Fortran 90 code optimized for sparse chemical networks.

### Generated Files

- `commons.f90`: Module with common variables
- `rates.f90`: Rate coefficient calculations
- `fluxes.f90`: Flux calculations
- `ode.f90`: ODE and Jacobian routines
- `main.f90`: Example program
- `Makefile`: Build configuration

### Building and Running

```bash
cd builds/fortran_dlsodes
make
./chemical_solver
```

## Template System

The code generation uses a template preprocessor system. Templates are stored in `src/jaff/templates/` and plugins in `src/jaff/plugins/`.

### Template Structure

Each template contains source files with placeholders:

```python
# @JAFF:COMMONS
# This will be replaced with generated code
# @:COMMONS
```

### Plugin Structure

Each plugin must provide a `plugin.py` file with a `main()` function:

```python
def main(network, path_template):
    from jaff.preprocessor import Preprocessor
    
    p = Preprocessor()
    
    # Get generated code sections
    commons = network.get_commons()
    rates = network.get_rates()
    
    # Process template files
    p.preprocess(
        path_template,
        ["file1.py", "file2.py"],
        [{"PLACEHOLDER1": commons}, {"PLACEHOLDER2": rates}],
        comment="#"  # Comment character for the language
    )
```

## Customizing Generated Code

The generated code provides a starting point that you can customize:

1. **Modify physical parameters**: Add new variables to the parameter structure
2. **Change solver settings**: Adjust tolerances, methods, or time stepping
3. **Add diagnostics**: Include additional output or analysis
4. **Optimize performance**: Profile and optimize bottlenecks

## Creating Custom Templates

To create a new template:

1. Create a new directory in `src/jaff/templates/your_template/`
2. Add template files with placeholders
3. Create a plugin in `src/jaff/plugins/your_template/plugin.py`
4. Implement the `main()` function to process your templates

Example template file:
```python
# rates.py template
import numpy as np

# @JAFF:RATES
# Rate calculation functions will be inserted here
# @:RATES

def calculate_all_rates(T, av, crate):
    rates = np.zeros(N_REACTIONS)
    # @JAFF:RATE_CALLS
    # Individual rate calculations
    # @:RATE_CALLS
    return rates
```

## Available Code Sections

The network object provides these code generation methods:

- `network.get_commons()`: Variable declarations and indices
- `network.get_rates()`: Rate coefficient calculations
- `network.get_fluxes()`: Flux calculations for each reaction
- `network.get_ode()`: ODE right-hand side implementation
- `network.get_jacobian()`: Analytical Jacobian (if available)

## Best Practices

1. **Test the generated code**: Always verify results against known solutions
2. **Profile performance**: Chemical networks can be computationally intensive
3. **Use appropriate solvers**: Stiff ODEs require implicit methods (BDF, DLSODES)
4. **Check conservation**: Ensure element conservation in your solutions
5. **Version control**: Track both the network file and generated code