# Code Generation Tutorial

This tutorial walks you through generating code from chemical reaction networks using `codegen_class`. You'll learn how to use templates, customize output, and integrate generated code into your projects.

## Overview

Code generation in `codegen_class` transforms JAFF network definitions into executable code in various programming languages. This tutorial covers:

- Basic code generation workflow
- Using built-in templates
- Customizing generated code
- Working with different output formats
- Integrating generated code

## Prerequisites

Before starting, ensure you have:

- `codegen_class` installed (see [Installation](../getting-started/installation.md))
- A JAFF network file (we'll use `examples/simple_network.jaff`)
- Basic understanding of reaction networks

## Basic Code Generation

### Step 1: Prepare Your Network

Create a simple network file `my_network.jaff`:

```jaff
network MyNetwork {
    species {
        A;
        B;
        C;
    }
    
    reactions {
        A -> B [k1];
        B -> C [k2];
        A + B -> C [k3];
    }
}
```

### Step 2: Generate Python Code

Use the CLI to generate Python code:

```bash
jaff codegen my_network.jaff --output my_network.py --language python
```

This creates `my_network.py` with:

```python
# Generated from my_network.jaff
import numpy as np

class MyNetwork:
    """Chemical reaction network: MyNetwork"""
    
    def __init__(self):
        # Species indices
        self.A = 0
        self.B = 1
        self.C = 2
        
        # Number of species
        self.n_species = 3
        
        # Species names
        self.species_names = ['A', 'B', 'C']
        
        # Rate constants (initialize with default values)
        self.k1 = 1.0
        self.k2 = 1.0
        self.k3 = 1.0
    
    def dydt(self, t, y):
        """
        Compute derivatives dy/dt
        
        Args:
            t: Current time
            y: Current state vector [A, B, C]
        
        Returns:
            numpy array of derivatives
        """
        # Extract species concentrations
        A = y[self.A]
        B = y[self.B]
        C = y[self.C]
        
        # Initialize derivatives
        dy = np.zeros(self.n_species)
        
        # Reaction 1: A -> B
        r1 = self.k1 * A
        dy[self.A] -= r1
        dy[self.B] += r1
        
        # Reaction 2: B -> C
        r2 = self.k2 * B
        dy[self.B] -= r2
        dy[self.C] += r2
        
        # Reaction 3: A + B -> C
        r3 = self.k3 * A * B
        dy[self.A] -= r3
        dy[self.B] -= r3
        dy[self.C] += r3
        
        return dy
```

### Step 3: Use Generated Code

Use the generated class in your simulation:

```python
from scipy.integrate import solve_ivp
from my_network import MyNetwork

# Create network instance
network = MyNetwork()

# Set rate constants
network.k1 = 0.1
network.k2 = 0.05
network.k3 = 0.02

# Initial conditions
y0 = [10.0, 5.0, 0.0]  # [A, B, C]

# Time span
t_span = (0, 100)
t_eval = np.linspace(0, 100, 1000)

# Solve ODEs
solution = solve_ivp(
    network.dydt,
    t_span,
    y0,
    t_eval=t_eval,
    method='LSODA'
)

# Plot results
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
for i, name in enumerate(network.species_names):
    plt.plot(solution.t, solution.y[i], label=name)
plt.xlabel('Time')
plt.ylabel('Concentration')
plt.legend()
plt.grid(True)
plt.show()
```

## Using the Python API

For more control, use the Python API directly:

```python
from codegen_class import JAFFParser, PythonCodeGenerator

# Parse network
parser = JAFFParser()
network = parser.parse_file('my_network.jaff')

# Create code generator
generator = PythonCodeGenerator()

# Generate code
code = generator.generate(network)

# Write to file
with open('my_network.py', 'w') as f:
    f.write(code)
```

### Customizing Generation

Configure the generator with options:

```python
from codegen_class import PythonCodeGenerator, CodeGenOptions

# Create options
options = CodeGenOptions(
    include_docstrings=True,
    include_comments=True,
    use_numpy=True,
    vectorized=True,
    add_validation=True,
    class_name='ChemicalNetwork'
)

# Create generator with options
generator = PythonCodeGenerator(options)
code = generator.generate(network)
```

## Advanced Templates

### Using Custom Templates

Create a custom Jinja2 template `my_template.j2`:

```jinja2
# {{ network.name }} - Custom Template
# Generated: {{ generation_timestamp }}

class {{ network.name }}:
    """{{ network.description or 'Chemical reaction network' }}"""
    
    def __init__(self):
        # Species
        {% for species in network.species %}
        self.{{ species.name }} = {{ loop.index0 }}
        {% endfor %}
        
        # Rate constants
        {% for reaction in network.reactions %}
        self.{{ reaction.rate_constant }} = 1.0
        {% endfor %}
    
    def rates(self, concentrations):
        """Compute reaction rates"""
        {% for species in network.species %}
        {{ species.name }} = concentrations[self.{{ species.name }}]
        {% endfor %}
        
        rates = []
        {% for reaction in network.reactions %}
        # {{ reaction.equation }}
        r{{ loop.index }} = self.{{ reaction.rate_constant }}{% for reactant in reaction.reactants %} * {{ reactant.species }}{% if reactant.stoichiometry > 1 %}**{{ reactant.stoichiometry }}{% endif %}{% endfor %}
        rates.append(r{{ loop.index }})
        {% endfor %}
        
        return rates
```

Use the custom template:

```python
from codegen_class import TemplateCodeGenerator

generator = TemplateCodeGenerator(template_file='my_template.j2')
code = generator.generate(network)
```

### Template Variables

Templates have access to these variables:

```python
{
    'network': network,              # Network object
    'generation_timestamp': str,     # ISO timestamp
    'generator_version': str,        # codegen_class version
    'options': dict,                 # Generation options
    'metadata': dict                 # Custom metadata
}
```

## Language-Specific Generation

### C++ Code Generation

Generate optimized C++ code:

```bash
jaff codegen network.jaff --output network.cpp --language cpp
```

Example output structure:

```cpp
#ifndef MY_NETWORK_H
#define MY_NETWORK_H

#include <vector>
#include <array>

class MyNetwork {
public:
    // Species indices
    static constexpr size_t A = 0;
    static constexpr size_t B = 1;
    static constexpr size_t C = 2;
    static constexpr size_t N_SPECIES = 3;
    
    // Rate constants
    double k1, k2, k3;
    
    MyNetwork();
    
    void dydt(double t, const std::vector<double>& y, 
              std::vector<double>& dy) const;
};

#endif // MY_NETWORK_H
```

### MATLAB Code Generation

Generate MATLAB/Octave functions:

```bash
jaff codegen network.jaff --output network.m --language matlab
```

Example output:

```matlab
function dy = my_network(t, y, params)
    % MY_NETWORK - Chemical reaction network ODE system
    %
    % Inputs:
    %   t - time
    %   y - state vector [A, B, C]
    %   params - structure with rate constants
    %
    % Outputs:
    %   dy - derivatives vector
    
    % Extract species
    A = y(1);
    B = y(2);
    C = y(3);
    
    % Extract parameters
    k1 = params.k1;
    k2 = params.k2;
    k3 = params.k3;
    
    % Initialize derivatives
    dy = zeros(3, 1);
    
    % Reactions
    r1 = k1 * A;
    dy(1) = dy(1) - r1;
    dy(2) = dy(2) + r1;
    
    r2 = k2 * B;
    dy(2) = dy(2) - r2;
    dy(3) = dy(3) + r2;
    
    r3 = k3 * A * B;
    dy(1) = dy(1) - r3;
    dy(2) = dy(2) - r3;
    dy(3) = dy(3) + r3;
end
```

## Working with Large Networks

### Optimizing Large Networks

For networks with many species/reactions:

```python
from codegen_class import PythonCodeGenerator, CodeGenOptions

# Enable optimizations
options = CodeGenOptions(
    vectorized=True,          # Use vectorized operations
    sparse_jacobian=True,     # Generate sparse Jacobian
    inline_small_expr=True,   # Inline simple expressions
    optimize_level=2          # Optimization level (0-3)
)

generator = PythonCodeGenerator(options)
code = generator.generate(large_network)
```

### Generating Jacobian

Include analytical Jacobian for faster integration:

```python
options = CodeGenOptions(
    include_jacobian=True,
    sparse_jacobian=True  # For large networks
)

generator = PythonCodeGenerator(options)
code = generator.generate(network)
```

Generated code includes:

```python
def jacobian(self, t, y):
    """
    Compute Jacobian matrix dF/dy
    
    Returns:
        Sparse matrix or dense numpy array
    """
    # ... Jacobian computation
```

## Batch Code Generation

Generate code for multiple networks:

```python
from pathlib import Path
from codegen_class import JAFFParser, PythonCodeGenerator

parser = JAFFParser()
generator = PythonCodeGenerator()

# Process all JAFF files
for jaff_file in Path('networks').glob('*.jaff'):
    network = parser.parse_file(jaff_file)
    code = generator.generate(network)
    
    output_file = jaff_file.with_suffix('.py')
    output_file.write_text(code)
    print(f"Generated: {output_file}")
```

## Validation and Testing

### Validating Generated Code

Test generated code automatically:

```python
from codegen_class import PythonCodeGenerator, validate_generated_code

generator = PythonCodeGenerator()
code = generator.generate(network)

# Validate syntax
is_valid, errors = validate_generated_code(code, language='python')

if is_valid:
    print("Generated code is valid!")
else:
    print("Errors found:")
    for error in errors:
        print(f"  - {error}")
```

### Conservation Laws

Verify conservation laws in generated code:

```python
from codegen_class import verify_conservation

# Check if network conserves mass
conserved = verify_conservation(network)

if conserved:
    print("Network satisfies conservation laws")
    # Include conservation checks in generated code
    options = CodeGenOptions(add_conservation_checks=True)
    generator = PythonCodeGenerator(options)
    code = generator.generate(network)
```

## Integration Examples

### Integration with SciPy

```python
from scipy.integrate import solve_ivp
import numpy as np

# Load generated network
from my_network import MyNetwork

network = MyNetwork()
network.k1 = 0.1
network.k2 = 0.05

# Solve
y0 = [10.0, 0.0, 0.0]
sol = solve_ivp(
    network.dydt,
    [0, 100],
    y0,
    method='BDF',
    jac=network.jacobian if hasattr(network, 'jacobian') else None
)
```

### Integration with Numba (JIT)

Accelerate generated code with Numba:

```python
from codegen_class import PythonCodeGenerator, CodeGenOptions

options = CodeGenOptions(
    use_numba=True,           # Add @njit decorators
    numba_parallel=False,     # Use parallel=True for large networks
)

generator = PythonCodeGenerator(options)
code = generator.generate(network)
```

### Integration with JAX

Generate JAX-compatible code:

```python
options = CodeGenOptions(
    backend='jax',
    use_jax_jit=True,
    use_jax_vmap=True
)

generator = PythonCodeGenerator(options)
code = generator.generate(network)
```

## Troubleshooting

### Common Issues

**Issue**: Generated code has syntax errors

```python
# Solution: Validate network before generation
from codegen_class import validate_network

errors = validate_network(network)
if errors:
    for error in errors:
        print(f"Network error: {error}")
else:
    code = generator.generate(network)
```

**Issue**: Rate expressions are incorrect

```python
# Solution: Check reaction definitions
for reaction in network.reactions:
    print(f"{reaction.equation}: rate = {reaction.rate_law}")
```

**Issue**: Missing imports in generated code

```python
# Solution: Specify required imports
options = CodeGenOptions(
    extra_imports=['numpy as np', 'scipy.sparse']
)
generator = PythonCodeGenerator(options)
```

## Best Practices

1. **Validate First**: Always validate your network before generation
2. **Use Version Control**: Track generated code changes
3. **Add Comments**: Enable comments in generated code for maintainability
4. **Test Thoroughly**: Validate generated code with known test cases
5. **Optimize Wisely**: Profile before optimizing for large networks
6. **Document Parameters**: Include parameter documentation in templates
7. **Separate Concerns**: Keep network definitions separate from simulation code

## Next Steps

- Learn about [Custom Templates](../user-guide/template-syntax.md)
- Explore [Template Variables](../reference/template-variables.md)
- See [Network Analysis Tutorial](network-analysis.md)
- Read the [Code Generation API](../api/codegen.md)

## Summary

In this tutorial, you learned:

- ✅ How to generate code from JAFF networks
- ✅ Using built-in and custom templates
- ✅ Generating code for different languages
- ✅ Optimizing for large networks
- ✅ Integrating generated code with scientific Python
- ✅ Validating and testing generated code

Continue experimenting with different networks and templates to master code generation!
