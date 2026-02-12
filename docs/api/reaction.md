# Reaction API

The `Reaction` class represents a chemical reaction in a reaction network, containing information about reactants, products, stoichiometry, and rate laws.

## Overview

A reaction describes the transformation of chemical species (reactants) into other species (products), along with the kinetic rate law that governs the reaction rate. The `Reaction` class is a fundamental component of the reaction network representation.

## Class Definition

```python
class Reaction:
    """
    Represents a chemical reaction with reactants, products, and rate information.
    
    Attributes:
        id (str): Unique identifier for the reaction
        reactants (Dict[str, int]): Mapping of reactant species IDs to stoichiometric coefficients
        products (Dict[str, int]): Mapping of product species IDs to stoichiometric coefficients
        rate_law (str): Mathematical expression for the reaction rate
        reversible (bool): Whether the reaction is reversible
        parameters (Dict[str, float]): Rate parameters and constants
    """
```

## Attributes

### `id`

```python
id: str
```

Unique identifier for the reaction within the network.

**Example:**
```python
reaction.id = "R1"
```

---

### `reactants`

```python
reactants: Dict[str, int]
```

Dictionary mapping reactant species IDs to their stoichiometric coefficients.

**Example:**
```python
# A + 2B → C
reaction.reactants = {"A": 1, "B": 2}
```

---

### `products`

```python
products: Dict[str, int]
```

Dictionary mapping product species IDs to their stoichiometric coefficients.

**Example:**
```python
# A + 2B → C + D
reaction.products = {"C": 1, "D": 1}
```

---

### `rate_law`

```python
rate_law: str
```

Mathematical expression describing the reaction rate. Can reference species concentrations and parameters.

**Example:**
```python
# Mass action kinetics
reaction.rate_law = "k1 * [A] * [B]^2"

# Michaelis-Menten kinetics
reaction.rate_law = "Vmax * [S] / (Km + [S])"
```

---

### `reversible`

```python
reversible: bool
```

Indicates whether the reaction can proceed in both forward and reverse directions.

**Example:**
```python
reaction.reversible = True  # A ⇌ B
reaction.reversible = False  # A → B
```

---

### `parameters`

```python
parameters: Dict[str, float]
```

Dictionary of parameter names and their numerical values used in the rate law.

**Example:**
```python
reaction.parameters = {
    "k1": 0.5,
    "k2": 0.1,
    "Km": 2.0
}
```

---

### `annotation`

```python
annotation: Optional[Dict[str, Any]]
```

Optional metadata and annotations for the reaction (e.g., biological pathway, gene associations).

**Example:**
```python
reaction.annotation = {
    "pathway": "glycolysis",
    "ec_number": "2.7.1.1",
    "gene": "HK1"
}
```

## Methods

### `__init__()`

```python
def __init__(
    self,
    reaction_id: str,
    reactants: Optional[Dict[str, int]] = None,
    products: Optional[Dict[str, int]] = None,
    rate_law: Optional[str] = None,
    reversible: bool = False,
    parameters: Optional[Dict[str, float]] = None
) -> None:
    """
    Initialize a new Reaction instance.
    
    Args:
        reaction_id: Unique identifier for the reaction
        reactants: Dictionary of reactant species IDs and stoichiometries
        products: Dictionary of product species IDs and stoichiometries
        rate_law: Mathematical expression for reaction rate
        reversible: Whether the reaction is reversible
        parameters: Rate parameters and constants
    """
```

**Example:**
```python
from codegen_class import Reaction

# Simple irreversible reaction: A + B → C
reaction = Reaction(
    reaction_id="R1",
    reactants={"A": 1, "B": 1},
    products={"C": 1},
    rate_law="k * [A] * [B]",
    reversible=False,
    parameters={"k": 0.5}
)
```

---

### `add_reactant()`

```python
def add_reactant(self, species_id: str, stoichiometry: int = 1) -> None:
    """
    Add a reactant species to the reaction.
    
    Args:
        species_id: ID of the species to add as reactant
        stoichiometry: Stoichiometric coefficient (default: 1)
    """
```

**Example:**
```python
reaction.add_reactant("A", 1)
reaction.add_reactant("B", 2)  # 2 molecules of B
```

---

### `add_product()`

```python
def add_product(self, species_id: str, stoichiometry: int = 1) -> None:
    """
    Add a product species to the reaction.
    
    Args:
        species_id: ID of the species to add as product
        stoichiometry: Stoichiometric coefficient (default: 1)
    """
```

**Example:**
```python
reaction.add_product("C", 1)
reaction.add_product("D", 3)  # 3 molecules of D
```

---

### `set_rate_law()`

```python
def set_rate_law(self, expression: str, parameters: Optional[Dict[str, float]] = None) -> None:
    """
    Set or update the reaction rate law.
    
    Args:
        expression: Mathematical expression for the rate
        parameters: Optional dictionary of parameter values
    """
```

**Example:**
```python
reaction.set_rate_law(
    "k1 * [A] * [B] - k2 * [C]",
    parameters={"k1": 0.5, "k2": 0.1}
)
```

---

### `get_stoichiometry()`

```python
def get_stoichiometry(self, species_id: str) -> int:
    """
    Get the net stoichiometric coefficient for a species.
    
    Args:
        species_id: ID of the species
        
    Returns:
        Net stoichiometry (positive for products, negative for reactants)
    """
```

**Example:**
```python
# For reaction: 2A + B → 3C
stoich_A = reaction.get_stoichiometry("A")  # Returns -2
stoich_C = reaction.get_stoichiometry("C")  # Returns 3
```

---

### `is_balanced()`

```python
def is_balanced(self, species_dict: Dict[str, Species]) -> bool:
    """
    Check if the reaction is mass-balanced.
    
    Args:
        species_dict: Dictionary of species IDs to Species objects
        
    Returns:
        True if reaction conserves mass, False otherwise
    """
```

**Example:**
```python
from codegen_class import Network

network = Network.from_file("model.xml")
reaction = network.get_reaction("R1")

if reaction.is_balanced(network.species):
    print("Reaction is mass-balanced")
```

---

### `to_equation_string()`

```python
def to_equation_string(self, use_names: bool = False) -> str:
    """
    Generate a human-readable equation string.
    
    Args:
        use_names: If True, use species names instead of IDs
        
    Returns:
        String representation like "2A + B → C"
    """
```

**Example:**
```python
# Using IDs
print(reaction.to_equation_string())
# Output: "2A + B → C"

# Using names
print(reaction.to_equation_string(use_names=True))
# Output: "2Glucose + ATP → Glucose-6-phosphate"
```

---

### `to_dict()`

```python
def to_dict(self) -> Dict[str, Any]:
    """
    Convert reaction to dictionary representation.
    
    Returns:
        Dictionary containing all reaction data
    """
```

**Example:**
```python
reaction_data = reaction.to_dict()
# {
#     "id": "R1",
#     "reactants": {"A": 1, "B": 2},
#     "products": {"C": 1},
#     "rate_law": "k * [A] * [B]^2",
#     "reversible": False,
#     "parameters": {"k": 0.5}
# }
```

---

### `from_dict()`

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Reaction":
    """
    Create a Reaction instance from dictionary data.
    
    Args:
        data: Dictionary containing reaction data
        
    Returns:
        New Reaction instance
    """
```

**Example:**
```python
data = {
    "id": "R1",
    "reactants": {"A": 1, "B": 1},
    "products": {"C": 1},
    "rate_law": "k * [A] * [B]",
    "parameters": {"k": 0.5}
}

reaction = Reaction.from_dict(data)
```

## Usage Examples

### Creating Reactions

```python
from codegen_class import Reaction

# Simple mass action reaction
r1 = Reaction(
    reaction_id="R1",
    reactants={"A": 1, "B": 1},
    products={"C": 1},
    rate_law="k1 * [A] * [B]",
    parameters={"k1": 0.5}
)

# Reversible reaction
r2 = Reaction(
    reaction_id="R2",
    reactants={"C": 1},
    products={"A": 1, "B": 1},
    reversible=True,
    rate_law="k_fwd * [C] - k_rev * [A] * [B]",
    parameters={"k_fwd": 0.1, "k_rev": 0.05}
)

# Enzymatic reaction with Michaelis-Menten kinetics
r3 = Reaction(
    reaction_id="R3",
    reactants={"S": 1},
    products={"P": 1},
    rate_law="Vmax * [S] / (Km + [S])",
    parameters={"Vmax": 10.0, "Km": 2.0}
)
```

### Building Reactions Incrementally

```python
# Start with empty reaction
reaction = Reaction(reaction_id="R_complex")

# Add reactants
reaction.add_reactant("ATP", 1)
reaction.add_reactant("Glucose", 1)

# Add products
reaction.add_product("ADP", 1)
reaction.add_product("G6P", 1)

# Set rate law
reaction.set_rate_law(
    "k_cat * [E] * [ATP] * [Glucose] / ((Km_ATP + [ATP]) * (Km_Glc + [Glucose]))",
    parameters={
        "k_cat": 100.0,
        "Km_ATP": 0.5,
        "Km_Glc": 0.1
    }
)
```

### Working with Reaction Networks

```python
from codegen_class import Network, Reaction

# Create network
network = Network(network_id="glycolysis")

# Add reactions
r1 = Reaction(
    reaction_id="HK",
    reactants={"Glucose": 1, "ATP": 1},
    products={"G6P": 1, "ADP": 1},
    rate_law="k * [Glucose] * [ATP]",
    parameters={"k": 0.5}
)

network.add_reaction(r1)

# Access reactions
reaction = network.get_reaction("HK")
print(reaction.to_equation_string())
```

### Analyzing Reactions

```python
# Get stoichiometric information
net_stoich = reaction.get_stoichiometry("ATP")  # -1 (consumed)

# Check mass balance
if reaction.is_balanced(network.species):
    print("Reaction conserves mass")

# Export reaction data
reaction_dict = reaction.to_dict()
import json
print(json.dumps(reaction_dict, indent=2))
```

### Custom Rate Laws

```python
# Hill equation for cooperative binding
r_hill = Reaction(
    reaction_id="R_coop",
    reactants={"S": 1},
    products={"P": 1},
    rate_law="Vmax * [S]^n / (K^n + [S]^n)",
    parameters={
        "Vmax": 10.0,
        "K": 5.0,
        "n": 2.5  # Hill coefficient
    }
)

# Allosteric regulation
r_allosteric = Reaction(
    reaction_id="R_allosteric",
    reactants={"S": 1},
    products={"P": 1},
    rate_law="Vmax * [S] / (Km * (1 + [I]/Ki) + [S])",
    parameters={
        "Vmax": 10.0,
        "Km": 1.0,
        "Ki": 0.5
    }
)
```

## Rate Law Syntax

Rate laws are mathematical expressions that can include:

- **Species concentrations**: `[SpeciesID]` or `{SpeciesID}`
- **Parameters**: Parameter names from the `parameters` dictionary
- **Operators**: `+`, `-`, `*`, `/`, `^` (power)
- **Functions**: `exp()`, `log()`, `ln()`, `sqrt()`, `abs()`
- **Constants**: Numeric literals

**Examples:**

```python
# Mass action
"k * [A] * [B]"

# Michaelis-Menten
"Vmax * [S] / (Km + [S])"

# Competitive inhibition
"Vmax * [S] / (Km * (1 + [I]/Ki) + [S])"

# Hill equation
"Vmax * [S]^n / (K^n + [S]^n)"

# Reversible mass action
"kf * [A] * [B] - kr * [C] * [D]"
```

## Common Patterns

### Irreversible Mass Action

```python
Reaction(
    reaction_id="R1",
    reactants={"A": 1, "B": 1},
    products={"C": 1},
    rate_law="k * [A] * [B]",
    reversible=False,
    parameters={"k": 0.5}
)
```

### Reversible Reaction

```python
Reaction(
    reaction_id="R2",
    reactants={"A": 1},
    products={"B": 1},
    reversible=True,
    rate_law="kf * [A] - kr * [B]",
    parameters={"kf": 1.0, "kr": 0.5}
)
```

### Enzyme Kinetics

```python
Reaction(
    reaction_id="R_enzyme",
    reactants={"S": 1},
    products={"P": 1},
    rate_law="kcat * [E] * [S] / (Km + [S])",
    parameters={
        "kcat": 100.0,
        "Km": 1.0
    }
)
```

## Integration with Network

Reactions are typically created as part of a `Network`:

```python
from codegen_class import Network

# Load network from file
network = Network.from_file("model.xml")

# Access reactions
for reaction in network.reactions.values():
    print(f"{reaction.id}: {reaction.to_equation_string()}")

# Get specific reaction
reaction = network.get_reaction("R1")

# Modify reaction
reaction.set_rate_law("k * [A]^2 * [B]", parameters={"k": 0.8})
```

## See Also

- [Species API](species.md) - Chemical species representation
- [Network API](network.md) - Reaction network container
- [Code Generation](codegen.md) - Generating simulation code
- [User Guide: Reactions](../user-guide/reactions.md) - Working with reactions
- [User Guide: Rates](../user-guide/rates.md) - Rate law expressions

## Notes

- Reaction IDs must be unique within a network
- Stoichiometric coefficients must be positive integers
- Rate laws are stored as strings and interpreted during code generation
- The `reversible` flag is informational; reversibility is implemented via the rate law
- Mass balance checking requires species with defined molecular formulas
