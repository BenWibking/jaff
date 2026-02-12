# Basic Usage Tutorial

Welcome to the basic usage tutorial for `codegen_class`! This guide will walk you through the fundamental steps of loading a chemical reaction network and generating code from it.

## Overview

In this tutorial, you will learn how to:

1. Load a reaction network from a file
2. Inspect the network structure
3. Generate code using built-in templates
4. Customize the output

## Prerequisites

Before starting this tutorial, ensure you have:

- Installed `codegen_class` (see [Installation](../getting-started/installation.md))
- A text editor
- Basic familiarity with chemical reaction networks
- Python 3.8 or higher

## Tutorial Steps

### Step 1: Create a Sample Network File

First, let's create a simple reaction network file. Create a file named `simple_network.txt` with the following content:

```/dev/null/simple_network.txt
# Simple Hydrogen-Oxygen Reaction Network
# Format: Reactants -> Products : Rate

# Formation of water
H2 + O2 -> H2O2 : k1
H2O2 + H2 -> 2H2O : k2

# Reverse reactions
H2O2 -> H2 + O2 : k3
2H2O -> H2O2 + H2 : k4
```

This network describes a simplified water formation mechanism with:

- 3 chemical species: H2, O2, H2O, H2O2
- 4 reactions with rate constants k1, k2, k3, k4

### Step 2: Load the Network

Now let's load this network using Python:

```/dev/null/example.py
from codegen_class import Network

# Load the network from file
network = Network.from_file('simple_network.txt')

# Display basic information
print(f"Network loaded successfully!")
print(f"Number of species: {len(network.species)}")
print(f"Number of reactions: {len(network.reactions)}")
```

**Expected Output:**
```
Network loaded successfully!
Number of species: 4
Number of reactions: 4
```

### Step 3: Inspect the Network

Let's examine the loaded network in more detail:

```/dev/null/inspect.py
# List all species
print("\nSpecies in the network:")
for species in network.species:
    print(f"  - {species.name}")

# List all reactions
print("\nReactions in the network:")
for i, reaction in enumerate(network.reactions, 1):
    reactants = ' + '.join([f"{r.stoich}{r.species.name}" if r.stoich > 1 
                            else r.species.name for r in reaction.reactants])
    products = ' + '.join([f"{p.stoich}{p.species.name}" if p.stoich > 1 
                          else p.species.name for p in reaction.products])
    print(f"  {i}. {reactants} -> {products}")
```

**Expected Output:**
```
Species in the network:
  - H2
  - O2
  - H2O2
  - H2O

Reactions in the network:
  1. H2 + O2 -> H2O2
  2. H2O2 + H2 -> 2H2O
  3. H2O2 -> H2 + O2
  4. 2H2O -> H2O2 + H2
```

### Step 4: Generate Code (Python)

Now let's generate Python code for this network:

```/dev/null/generate_python.py
from codegen_class import CodeGenerator

# Create a code generator
generator = CodeGenerator(network)

# Generate Python code
python_code = generator.generate('python')

# Save to file
with open('network_odes.py', 'w') as f:
    f.write(python_code)

print("Python code generated successfully!")
print("\nGenerated file: network_odes.py")
```

The generated `network_odes.py` file will contain:

```/dev/null/network_odes.py
import numpy as np

def odes(t, y, k):
    """
    ODE system for chemical reaction network
    
    Parameters:
    -----------
    t : float
        Time
    y : array-like
        Species concentrations [H2, O2, H2O2, H2O]
    k : array-like
        Rate constants [k1, k2, k3, k4]
    
    Returns:
    --------
    dydt : numpy.ndarray
        Time derivatives of species concentrations
    """
    # Extract species concentrations
    H2 = y[0]
    O2 = y[1]
    H2O2 = y[2]
    H2O = y[3]
    
    # Extract rate constants
    k1, k2, k3, k4 = k
    
    # Calculate reaction rates
    r1 = k1 * H2 * O2
    r2 = k2 * H2O2 * H2
    r3 = k3 * H2O2
    r4 = k4 * H2O**2
    
    # Calculate derivatives
    dydt = np.zeros(4)
    dydt[0] = -r1 - r2 + r3 + r4  # dH2/dt
    dydt[1] = -r1 + r3             # dO2/dt
    dydt[2] = r1 - r2 - r3 + r4    # dH2O2/dt
    dydt[3] = 2*r2 - 2*r4          # dH2O/dt
    
    return dydt
```

### Step 5: Generate Code (C++)

You can also generate C++ code:

```/dev/null/generate_cpp.py
# Generate C++ code
cpp_code = generator.generate('cpp')

# Save to file
with open('network_odes.cpp', 'w') as f:
    f.write(cpp_code)

print("C++ code generated successfully!")
```

### Step 6: Use the Generated Code

Now let's use the generated Python code to solve the ODE system:

```/dev/null/solve_odes.py
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
from network_odes import odes

# Initial conditions (concentrations)
y0 = [1.0, 0.5, 0.0, 0.0]  # [H2, O2, H2O2, H2O]

# Rate constants
k = [0.1, 0.2, 0.05, 0.01]  # [k1, k2, k3, k4]

# Time span
t_span = (0, 50)
t_eval = np.linspace(0, 50, 500)

# Solve the ODE system
solution = solve_ivp(
    lambda t, y: odes(t, y, k),
    t_span,
    y0,
    t_eval=t_eval,
    method='LSODA'
)

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(solution.t, solution.y[0], label='H2')
plt.plot(solution.t, solution.y[1], label='O2')
plt.plot(solution.t, solution.y[2], label='H2O2')
plt.plot(solution.t, solution.y[3], label='H2O')
plt.xlabel('Time')
plt.ylabel('Concentration')
plt.title('Chemical Reaction Network Dynamics')
plt.legend()
plt.grid(True)
plt.savefig('network_dynamics.png')
plt.show()

print("Simulation complete! Results saved to network_dynamics.png")
```

### Step 7: Using the Command-Line Interface

Alternatively, you can generate code directly from the command line:

```bash
# Generate Python code
jaff simple_network.txt --output network_odes.py --language python

# Generate C++ code
jaff simple_network.txt --output network_odes.cpp --language cpp

# Generate MATLAB code
jaff simple_network.txt --output network_odes.m --language matlab

# View network information without generating code
jaff simple_network.txt --info
```

## Common Patterns

### Pattern 1: Loading Different File Formats

```/dev/null/load_formats.py
# Load from different formats
network1 = Network.from_file('network.txt')      # Plain text
network2 = Network.from_file('network.json')     # JSON
network3 = Network.from_file('network.yaml')     # YAML
network4 = Network.from_file('network.xml')      # SBML XML
```

### Pattern 2: Network Validation

```/dev/null/validate.py
# Check if network is valid
if network.validate():
    print("Network is valid!")
else:
    print("Network has issues:")
    for error in network.errors:
        print(f"  - {error}")
```

### Pattern 3: Accessing Species and Reactions

```/dev/null/access.py
# Access species by name
h2_species = network.get_species('H2')
print(f"Species: {h2_species.name}")

# Access reactions by index
first_reaction = network.reactions[0]
print(f"Reaction rate: {first_reaction.rate}")

# Find reactions involving a specific species
h2_reactions = network.find_reactions_with_species('H2')
print(f"H2 appears in {len(h2_reactions)} reactions")
```

### Pattern 4: Network Statistics

```/dev/null/statistics.py
# Get network statistics
stats = network.statistics()
print(f"Total species: {stats['num_species']}")
print(f"Total reactions: {stats['num_reactions']}")
print(f"Reversible reactions: {stats['num_reversible']}")
print(f"Max reactants: {stats['max_reactants']}")
print(f"Max products: {stats['max_products']}")
```

## Troubleshooting

### Issue: File Not Found

**Problem:** `FileNotFoundError: No such file or directory`

**Solution:** Ensure the file path is correct and the file exists:

```/dev/null/check_file.py
import os

if os.path.exists('simple_network.txt'):
    network = Network.from_file('simple_network.txt')
else:
    print("File not found! Please check the path.")
```

### Issue: Parse Error

**Problem:** `ParseError: Invalid reaction format`

**Solution:** Check your network file syntax. Common issues:

- Missing reaction arrow (`->`)
- Invalid species names (use alphanumeric and underscores only)
- Missing rate constant

### Issue: Code Generation Fails

**Problem:** `CodeGenerationError: Template not found`

**Solution:** Verify the template name is correct:

```/dev/null/check_template.py
# List available templates
available = generator.list_templates()
print("Available templates:", available)

# Use a valid template
code = generator.generate(available[0])
```

## Best Practices

1. **Validate Input Files:** Always validate your network files before generating code
2. **Use Descriptive Names:** Give species and rate constants meaningful names
3. **Document Your Network:** Add comments to network files to explain the chemistry
4. **Test Generated Code:** Always test the generated code with sample data
5. **Version Control:** Keep your network files and templates in version control

## Next Steps

Now that you've mastered the basics, explore more advanced topics:

- [Code Generation Tutorial](code-generation.md) - Learn advanced code generation techniques
- [Custom Templates](custom-templates.md) - Create your own code templates
- [Network Analysis](network-analysis.md) - Analyze network properties and behavior
- [Loading Networks Guide](../user-guide/loading-networks.md) - Detailed guide on loading networks

## Summary

In this tutorial, you learned how to:

✅ Create a simple reaction network file  
✅ Load the network into Python  
✅ Inspect network structure and properties  
✅ Generate code in multiple languages  
✅ Use the generated code to solve ODEs  
✅ Work with the command-line interface  

You're now ready to work with more complex networks and explore advanced features!

## Example Files

All example files from this tutorial are available in the `examples/basic-usage/` directory:

- `simple_network.txt` - Sample network file
- `load_network.py` - Network loading example
- `generate_code.py` - Code generation example
- `solve_odes.py` - ODE solver example

## Additional Resources

- [API Reference](../api/network.md) - Complete API documentation
- [User Guide](../user-guide/loading-networks.md) - Comprehensive user guide
- [Examples Repository](https://github.com/yourusername/codegen_class/tree/main/examples) - More examples

---

**Questions or issues?** Check our [FAQ](../getting-started/quickstart.md#faq) or [open an issue](https://github.com/yourusername/codegen_class/issues) on GitHub.
