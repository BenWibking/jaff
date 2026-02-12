# Network Analysis Tutorial

This tutorial demonstrates how to analyze chemical reaction networks using the `codegen_class` library. You'll learn how to load networks, inspect their structure, analyze species and reactions, and extract useful information.

## Prerequisites

Before starting this tutorial, ensure you have:

- Installed `codegen_class` (see [Installation](../getting-started/installation.md))
- Basic understanding of chemical reaction networks
- Familiarity with Python basics

## Overview

Network analysis allows you to:

- Inspect network structure and properties
- Analyze species and their relationships
- Examine reaction mechanisms
- Identify network patterns
- Extract statistical information

## Loading a Network

First, let's load a chemical reaction network:

```python
from codegen_class import Network

# Load from JAFF file
network = Network.from_jaff("path/to/network.jaff")

# Or from other formats
# network = Network.from_chemkin("mechanism.inp")
# network = Network.from_cantera("mech.yaml")
```

## Basic Network Information

### Network Summary

Get a quick overview of the network:

```python
# Print network summary
print(f"Network: {network.name}")
print(f"Number of species: {len(network.species)}")
print(f"Number of reactions: {len(network.reactions)}")
print(f"Number of elements: {len(network.elements)}")

# Example output:
# Network: Hydrogen Combustion
# Number of species: 15
# Number of reactions: 28
# Number of elements: 3
```

### Species Information

Analyze the species in the network:

```python
# List all species
print("Species in network:")
for species in network.species:
    print(f"  {species.name}: {species.composition}")

# Example output:
#   H2: {H: 2}
#   O2: {O: 2}
#   H2O: {H: 2, O: 1}
#   OH: {H: 1, O: 1}
```

### Reaction Information

Examine the reactions:

```python
# List all reactions
print("\nReactions:")
for i, reaction in enumerate(network.reactions, 1):
    print(f"{i}. {reaction}")

# Example output:
# 1. H2 + O2 => 2OH
# 2. OH + H2 => H2O + H
# 3. H + O2 => OH + O
```

## Detailed Species Analysis

### Species Properties

Analyze individual species properties:

```python
# Get a specific species
h2o = network.get_species("H2O")

print(f"Species: {h2o.name}")
print(f"Composition: {h2o.composition}")
print(f"Molecular weight: {h2o.molecular_weight} g/mol")

# Check if species contains specific elements
if h2o.has_element("O"):
    print(f"Oxygen atoms: {h2o.get_element_count('O')}")
```

### Species Classification

Classify species by their properties:

```python
# Find species containing hydrogen
hydrogen_species = [s for s in network.species if s.has_element("H")]
print(f"\nSpecies containing hydrogen: {len(hydrogen_species)}")
for species in hydrogen_species:
    print(f"  {species.name}")

# Find radicals (species with odd number of electrons)
# This is a simplified example - actual implementation may vary
radicals = [s for s in network.species if s.is_radical]
print(f"\nRadical species: {len(radicals)}")
```

### Species Connectivity

Analyze which species participate in reactions:

```python
def get_species_reactions(network, species_name):
    """Get all reactions involving a species."""
    reactions = []
    for reaction in network.reactions:
        if species_name in reaction.reactants or species_name in reaction.products:
            reactions.append(reaction)
    return reactions

# Find all reactions involving H2O
h2o_reactions = get_species_reactions(network, "H2O")
print(f"\nReactions involving H2O: {len(h2o_reactions)}")
for reaction in h2o_reactions:
    print(f"  {reaction}")
```

## Detailed Reaction Analysis

### Reaction Properties

Analyze reaction properties:

```python
# Examine a specific reaction
reaction = network.reactions[0]

print(f"Reaction: {reaction}")
print(f"Reactants: {reaction.reactants}")
print(f"Products: {reaction.products}")
print(f"Reversible: {reaction.reversible}")

# Analyze stoichiometry
print("\nStoichiometry:")
for species, coeff in reaction.reactants.items():
    print(f"  {species}: {coeff} (reactant)")
for species, coeff in reaction.products.items():
    print(f"  {species}: {coeff} (product)")
```

### Reaction Classification

Classify reactions by type:

```python
# Find decomposition reactions (1 reactant, multiple products)
decomposition = [r for r in network.reactions 
                 if len(r.reactants) == 1 and len(r.products) > 1]
print(f"\nDecomposition reactions: {len(decomposition)}")

# Find synthesis reactions (multiple reactants, 1 product)
synthesis = [r for r in network.reactions 
             if len(r.reactants) > 1 and len(r.products) == 1]
print(f"Synthesis reactions: {len(synthesis)}")

# Find exchange reactions (2 reactants, 2 products)
exchange = [r for r in network.reactions 
            if len(r.reactants) == 2 and len(r.products) == 2]
print(f"Exchange reactions: {len(exchange)}")
```

### Reaction Rate Analysis

Analyze reaction rate expressions:

```python
# Examine rate parameters
for reaction in network.reactions:
    rate = reaction.rate
    print(f"\n{reaction}")
    print(f"  Rate type: {rate.type}")
    
    if hasattr(rate, 'A'):
        print(f"  Pre-exponential factor: {rate.A}")
    if hasattr(rate, 'beta'):
        print(f"  Temperature exponent: {rate.beta}")
    if hasattr(rate, 'Ea'):
        print(f"  Activation energy: {rate.Ea}")
```

## Network Structure Analysis

### Element Balance

Verify element balance in reactions:

```python
def check_element_balance(reaction, network):
    """Check if a reaction is element-balanced."""
    element_balance = {}
    
    # Count elements in reactants
    for species_name, coeff in reaction.reactants.items():
        species = network.get_species(species_name)
        for element, count in species.composition.items():
            element_balance[element] = element_balance.get(element, 0) - count * coeff
    
    # Count elements in products
    for species_name, coeff in reaction.products.items():
        species = network.get_species(species_name)
        for element, count in species.composition.items():
            element_balance[element] = element_balance.get(element, 0) + count * coeff
    
    return all(count == 0 for count in element_balance.values())

# Check all reactions
unbalanced = []
for reaction in network.reactions:
    if not check_element_balance(reaction, network):
        unbalanced.append(reaction)

if unbalanced:
    print(f"Warning: {len(unbalanced)} unbalanced reactions found!")
else:
    print("All reactions are element-balanced ✓")
```

### Network Connectivity Graph

Build a species connectivity graph:

```python
from collections import defaultdict

def build_connectivity_graph(network):
    """Build a graph showing which species are connected via reactions."""
    graph = defaultdict(set)
    
    for reaction in network.reactions:
        reactant_species = list(reaction.reactants.keys())
        product_species = list(reaction.products.keys())
        
        # Connect all reactants to all products
        for reactant in reactant_species:
            for product in product_species:
                graph[reactant].add(product)
                if reaction.reversible:
                    graph[product].add(reactant)
    
    return graph

# Build and analyze the graph
graph = build_connectivity_graph(network)

# Find most connected species
most_connected = max(graph.items(), key=lambda x: len(x[1]))
print(f"\nMost connected species: {most_connected[0]}")
print(f"Connected to {len(most_connected[1])} other species")
```

### Pathway Analysis

Find reaction pathways between species:

```python
def find_pathways(network, start_species, end_species, max_steps=5):
    """Find reaction pathways from start to end species."""
    from collections import deque
    
    queue = deque([(start_species, [start_species])])
    pathways = []
    visited = set()
    
    while queue:
        current, path = queue.popleft()
        
        if len(path) > max_steps:
            continue
        
        if current == end_species:
            pathways.append(path)
            continue
        
        if current in visited:
            continue
        visited.add(current)
        
        # Find reactions where current is a reactant
        for reaction in network.reactions:
            if current in reaction.reactants:
                for product in reaction.products:
                    if product not in path:
                        queue.append((product, path + [product]))
    
    return pathways

# Find pathways from H2 to H2O
pathways = find_pathways(network, "H2", "H2O", max_steps=3)
print(f"\nPathways from H2 to H2O ({len(pathways)} found):")
for i, pathway in enumerate(pathways[:5], 1):  # Show first 5
    print(f"{i}. {' -> '.join(pathway)}")
```

## Statistical Analysis

### Network Statistics

Compute various network statistics:

```python
import statistics

# Reaction stoichiometry statistics
reactant_counts = [len(r.reactants) for r in network.reactions]
product_counts = [len(r.products) for r in network.reactions]

print("\nNetwork Statistics:")
print(f"Average reactants per reaction: {statistics.mean(reactant_counts):.2f}")
print(f"Average products per reaction: {statistics.mean(product_counts):.2f}")

# Species participation
participation = {species.name: 0 for species in network.species}
for reaction in network.reactions:
    for species in reaction.reactants:
        participation[species] += 1
    for species in reaction.products:
        participation[species] += 1

print(f"\nMost active species:")
sorted_species = sorted(participation.items(), key=lambda x: x[1], reverse=True)
for species, count in sorted_species[:5]:
    print(f"  {species}: {count} reactions")
```

### Distribution Analysis

Analyze distributions of network properties:

```python
import matplotlib.pyplot as plt

# Species composition distribution
element_counts = {}
for species in network.species:
    for element, count in species.composition.items():
        element_counts[element] = element_counts.get(element, 0) + count

# Plot element distribution
plt.figure(figsize=(10, 6))
plt.bar(element_counts.keys(), element_counts.values())
plt.xlabel('Element')
plt.ylabel('Total Count')
plt.title('Element Distribution in Network')
plt.savefig('element_distribution.png')
plt.close()

# Reaction degree distribution
degree_dist = {}
for count in participation.values():
    degree_dist[count] = degree_dist.get(count, 0) + 1

plt.figure(figsize=(10, 6))
plt.bar(degree_dist.keys(), degree_dist.values())
plt.xlabel('Number of Reactions')
plt.ylabel('Number of Species')
plt.title('Species Participation Distribution')
plt.savefig('participation_distribution.png')
plt.close()

print("Distribution plots saved!")
```

## Export Analysis Results

### Generate Report

Create a comprehensive analysis report:

```python
def generate_network_report(network, output_file="network_report.txt"):
    """Generate a comprehensive network analysis report."""
    with open(output_file, 'w') as f:
        f.write(f"Network Analysis Report: {network.name}\n")
        f.write("=" * 60 + "\n\n")
        
        # Basic information
        f.write("1. BASIC INFORMATION\n")
        f.write(f"   Species: {len(network.species)}\n")
        f.write(f"   Reactions: {len(network.reactions)}\n")
        f.write(f"   Elements: {len(network.elements)}\n\n")
        
        # Species list
        f.write("2. SPECIES LIST\n")
        for species in network.species:
            f.write(f"   {species.name}: {species.composition}\n")
        f.write("\n")
        
        # Reaction list
        f.write("3. REACTIONS\n")
        for i, reaction in enumerate(network.reactions, 1):
            f.write(f"   {i}. {reaction}\n")
        f.write("\n")
        
        # Statistics
        f.write("4. STATISTICS\n")
        participation = {species.name: 0 for species in network.species}
        for reaction in network.reactions:
            for species in list(reaction.reactants.keys()) + list(reaction.products.keys()):
                participation[species] += 1
        
        sorted_species = sorted(participation.items(), key=lambda x: x[1], reverse=True)
        f.write("   Most active species:\n")
        for species, count in sorted_species[:10]:
            f.write(f"     {species}: {count} reactions\n")
    
    print(f"Report saved to {output_file}")

# Generate the report
generate_network_report(network)
```

### Export to Different Formats

Export analysis results:

```python
import json

# Export network structure to JSON
network_data = {
    "name": network.name,
    "species": [{"name": s.name, "composition": s.composition} 
                for s in network.species],
    "reactions": [str(r) for r in network.reactions],
    "statistics": {
        "num_species": len(network.species),
        "num_reactions": len(network.reactions),
        "num_elements": len(network.elements)
    }
}

with open("network_structure.json", 'w') as f:
    json.dump(network_data, f, indent=2)

print("Network structure exported to JSON")
```

## Advanced Analysis Examples

### Subnetwork Extraction

Extract a subnetwork containing only specific species:

```python
def extract_subnetwork(network, species_list):
    """Extract a subnetwork containing only specified species."""
    subnetwork_reactions = []
    
    for reaction in network.reactions:
        # Check if all species in reaction are in the list
        all_species = set(reaction.reactants.keys()) | set(reaction.products.keys())
        if all_species.issubset(set(species_list)):
            subnetwork_reactions.append(reaction)
    
    return subnetwork_reactions

# Extract hydrogen-oxygen subnetwork
h2_o2_species = ["H2", "O2", "H2O", "OH", "H", "O", "HO2", "H2O2"]
subnetwork = extract_subnetwork(network, h2_o2_species)
print(f"\nH2-O2 subnetwork: {len(subnetwork)} reactions")
```

### Sensitivity Analysis

Identify key species and reactions:

```python
def identify_key_species(network):
    """Identify species that participate in many reactions."""
    participation = {species.name: 0 for species in network.species}
    
    for reaction in network.reactions:
        for species in list(reaction.reactants.keys()) + list(reaction.products.keys()):
            participation[species] += 1
    
    # Define "key species" as those in top 20% by participation
    threshold = statistics.quantile(participation.values(), 0.8)
    key_species = [s for s, count in participation.items() if count >= threshold]
    
    return key_species

key_species = identify_key_species(network)
print(f"\nKey species ({len(key_species)}):")
for species in key_species:
    print(f"  {species}")
```

## Next Steps

Now that you know how to analyze networks, you can:

1. **Optimize networks**: Identify and remove redundant reactions
2. **Validate mechanisms**: Check for element balance and thermodynamic consistency
3. **Visualize networks**: Create network graphs and plots
4. **Compare mechanisms**: Analyze differences between network versions

## Related Documentation

- [Loading Networks](../user-guide/loading-networks.md)
- [Network Formats](../user-guide/network-formats.md)
- [Network API Reference](../api/network.md)
- [Species Guide](../user-guide/species.md)

## Complete Example

Here's a complete analysis script:

```python
#!/usr/bin/env python3
"""Complete network analysis example."""

from codegen_class import Network
import statistics

def analyze_network(jaff_file):
    """Perform comprehensive network analysis."""
    # Load network
    network = Network.from_jaff(jaff_file)
    print(f"Analyzing network: {network.name}")
    print("=" * 60)
    
    # Basic info
    print(f"\nBasic Information:")
    print(f"  Species: {len(network.species)}")
    print(f"  Reactions: {len(network.reactions)}")
    print(f"  Elements: {len(network.elements)}")
    
    # Species analysis
    print(f"\nSpecies Analysis:")
    for element in network.elements:
        species_with_element = [s for s in network.species if s.has_element(element)]
        print(f"  {element}: {len(species_with_element)} species")
    
    # Reaction analysis
    print(f"\nReaction Classification:")
    decomposition = [r for r in network.reactions 
                     if len(r.reactants) == 1 and len(r.products) > 1]
    synthesis = [r for r in network.reactions 
                 if len(r.reactants) > 1 and len(r.products) == 1]
    print(f"  Decomposition: {len(decomposition)}")
    print(f"  Synthesis: {len(synthesis)}")
    
    # Participation analysis
    participation = {species.name: 0 for species in network.species}
    for reaction in network.reactions:
        for species in list(reaction.reactants.keys()) + list(reaction.products.keys()):
            participation[species] += 1
    
    print(f"\nMost Active Species:")
    sorted_species = sorted(participation.items(), key=lambda x: x[1], reverse=True)
    for species, count in sorted_species[:5]:
        print(f"  {species}: {count} reactions")
    
    # Generate report
    generate_network_report(network, "analysis_report.txt")
    print(f"\nDetailed report saved to analysis_report.txt")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyze_network(sys.argv[1])
    else:
        print("Usage: python analysis_example.py <network.jaff>")
```

This tutorial has shown you how to perform comprehensive analysis of chemical reaction networks. Experiment with these techniques on your own networks to gain deeper insights into their structure and properties!
