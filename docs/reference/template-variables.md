# Template Variables Reference

This page provides a comprehensive reference for all variables available in Jinja2 templates when generating code with `codegen_class`.

## Overview

When you create a template for code generation, the template engine provides several variables that contain information about the chemical reaction network. These variables allow you to access network structure, species, reactions, and rates in your templates.

---

## Top-Level Variables

### `network`

**Type:** `Network` object

The main network object containing all information about the chemical reaction network.

**Usage:**
```jinja2
// Network name: {{ network.name }}
```

**Attributes:**

- `name` (str): Name of the network
- `species` (list): List of all species in the network
- `reactions` (list): List of all reactions in the network
- `rates` (dict): Dictionary of rate constants and expressions
- `metadata` (dict): Additional metadata from the network file

**Example:**
```jinja2
/*
 * Generated code for network: {{ network.name }}
 * Total species: {{ network.species|length }}
 * Total reactions: {{ network.reactions|length }}
 */
```

---

### `species`

**Type:** List of `Species` objects

A list of all chemical species in the network.

**Usage:**
```jinja2
{% for s in species %}
    species_{{ s.index }} = "{{ s.name }}"
{% endfor %}
```

**Individual Species Attributes:**

- `name` (str): Species name
- `index` (int): Zero-based index of the species
- `id` (str): Unique identifier (usually same as name)
- `initial_amount` (float, optional): Initial concentration/amount
- `charge` (int, optional): Charge state
- `compartment` (str, optional): Cellular compartment

**Example:**
```jinja2
const char* species_names[] = {
{% for s in species %}
    "{{ s.name }}"{{ "," if not loop.last }}
{% endfor %}
};
```

---

### `reactions`

**Type:** List of `Reaction` objects

A list of all reactions in the network.

**Usage:**
```jinja2
{% for r in reactions %}
    // Reaction {{ r.index }}: {{ r.equation }}
{% endfor %}
```

**Individual Reaction Attributes:**

- `index` (int): Zero-based index of the reaction
- `id` (str): Unique reaction identifier
- `equation` (str): String representation (e.g., "A + B -> C")
- `reactants` (list): List of reactant species
- `products` (list): List of product species
- `reactant_stoichiometry` (dict): Reactant stoichiometric coefficients
- `product_stoichiometry` (dict): Product stoichiometric coefficients
- `rate_law` (str): Rate law expression
- `reversible` (bool): Whether the reaction is reversible
- `modifiers` (list, optional): Species that modify the rate

**Example:**
```jinja2
void compute_rates(double* rates, double* species, double* params) {
{% for r in reactions %}
    // {{ r.equation }}
    rates[{{ r.index }}] = {{ r.rate_law }};
{% endfor %}
}
```

---

### `rates`

**Type:** Dictionary mapping rate names to values/expressions

Contains all rate constants and parameter expressions defined in the network.

**Usage:**
```jinja2
{% for name, value in rates.items() %}
    double {{ name }} = {{ value }};
{% endfor %}
```

**Example:**
```jinja2
struct Parameters {
{% for name, value in rates.items() %}
    double {{ name }}; // Default: {{ value }}
{% endfor %}
};

void init_parameters(struct Parameters* p) {
{% for name, value in rates.items() %}
    p->{{ name }} = {{ value }};
{% endfor %}
}
```

---

## Network Object Details

### Network Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Network name |
| `species` | list | All species objects |
| `reactions` | list | All reaction objects |
| `rates` | dict | Rate constants and parameters |
| `metadata` | dict | Additional network information |
| `num_species` | int | Total number of species |
| `num_reactions` | int | Total number of reactions |

**Example:**
```jinja2
#define NUM_SPECIES {{ network.num_species }}
#define NUM_REACTIONS {{ network.num_reactions }}
```

---

## Species Object Details

### Species Attributes

| Attribute | Type | Description | Required |
|-----------|------|-------------|----------|
| `name` | str | Species name/identifier | Yes |
| `index` | int | Zero-based position in species list | Yes |
| `id` | str | Unique ID (usually = name) | Yes |
| `initial_amount` | float | Starting concentration | No |
| `initial_concentration` | float | Alias for initial_amount | No |
| `charge` | int | Electrical charge | No |
| `compartment` | str | Location/compartment | No |
| `boundary_condition` | bool | Fixed concentration flag | No |

**Example:**
```jinja2
// Initialize species concentrations
double initial_concentrations[NUM_SPECIES] = {
{% for s in species %}
    {{ s.initial_amount if s.initial_amount is defined else 0.0 }}{{ "," if not loop.last }}
{% endfor %}
};
```

---

## Reaction Object Details

### Reaction Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `index` | int | Zero-based reaction index |
| `id` | str | Unique reaction identifier |
| `equation` | str | Human-readable equation |
| `reactants` | list | List of reactant Species objects |
| `products` | list | List of product Species objects |
| `reactant_stoichiometry` | dict | {species_name: coefficient} for reactants |
| `product_stoichiometry` | dict | {species_name: coefficient} for products |
| `rate_law` | str | Mathematical rate expression |
| `reversible` | bool | Reversibility flag |
| `modifiers` | list | Species affecting rate (catalysts, etc.) |

### Stoichiometry Dictionaries

The stoichiometry dictionaries map species names to their coefficients:

```jinja2
{% for r in reactions %}
Reaction {{ r.index }}: {{ r.equation }}
Reactants:
{% for species_name, coeff in r.reactant_stoichiometry.items() %}
  - {{ species_name }}: {{ coeff }}
{% endfor %}
Products:
{% for species_name, coeff in r.product_stoichiometry.items() %}
  - {{ species_name }}: {{ coeff }}
{% endfor %}
{% endfor %}
```

### Rate Law Expressions

Rate laws are provided as strings with species names that need to be substituted:

```jinja2
{% for r in reactions %}
    // {{ r.equation }}
    // Raw rate law: {{ r.rate_law }}
    double rate_{{ r.index }} = {{ r.rate_law }};
{% endfor %}
```

---

## Jinja2 Template Features

### Loops

Iterate over species, reactions, or rates:

```jinja2
{% for s in species %}
    // Species {{ loop.index }}: {{ s.name }}
{% endfor %}
```

**Loop Variables:**

- `loop.index`: 1-based iteration counter
- `loop.index0`: 0-based iteration counter
- `loop.first`: True on first iteration
- `loop.last`: True on last iteration
- `loop.length`: Total iterations

### Conditionals

```jinja2
{% for s in species %}
{% if s.initial_amount is defined %}
    // {{ s.name }} starts at {{ s.initial_amount }}
{% else %}
    // {{ s.name }} starts at 0.0
{% endif %}
{% endfor %}
```

### Filters

Jinja2 provides many built-in filters:

```jinja2
// Total species: {{ species|length }}
// Network name (uppercase): {{ network.name|upper }}
// First species: {{ species|first }}
// Last species: {{ species|last }}
```

**Common Filters:**

- `|length`: Get list/dict size
- `|upper`: Convert to uppercase
- `|lower`: Convert to lowercase
- `|join(sep)`: Join list elements
- `|default(value)`: Provide default if undefined
- `|sort`: Sort a list

### Comments

```jinja2
{# This is a template comment - won't appear in output #}
```

---

## Common Patterns

### Enumerate Species with Indices

```jinja2
enum Species {
{% for s in species %}
    SPECIES_{{ s.name|upper }} = {{ s.index }}{{ "," if not loop.last }}
{% endfor %}
};
```

### Create Stoichiometry Matrix

```jinja2
// Stoichiometry matrix (reactions x species)
int stoich[NUM_REACTIONS][NUM_SPECIES] = {
{% for r in reactions %}
    { // Reaction {{ r.index }}: {{ r.equation }}
    {% for s in species %}
        {{ r.product_stoichiometry.get(s.name, 0) - r.reactant_stoichiometry.get(s.name, 0) }}{{ "," if not loop.last }}
    {% endfor %}
    }{{ "," if not loop.last }}
{% endfor %}
};
```

### Generate ODE System

```jinja2
void compute_derivatives(double* dydt, double* y, double* params) {
{% for s in species %}
    dydt[{{ s.index }}] = 0.0;
{% endfor %}

{% for r in reactions %}
    // Reaction {{ r.index }}: {{ r.equation }}
    double rate_{{ r.index }} = {{ r.rate_law }};
    
    {% for species_name, coeff in r.reactant_stoichiometry.items() %}
    dydt[SPECIES_{{ species_name|upper }}] -= {{ coeff }} * rate_{{ r.index }};
    {% endfor %}
    
    {% for species_name, coeff in r.product_stoichiometry.items() %}
    dydt[SPECIES_{{ species_name|upper }}] += {{ coeff }} * rate_{{ r.index }};
    {% endfor %}
{% endfor %}
}
```

### Initialize Parameters

```jinja2
struct Parameters {
{% for name, value in rates.items() %}
    double {{ name }};
{% endfor %}
};

void init_defaults(struct Parameters* p) {
{% for name, value in rates.items() %}
    p->{{ name }} = {{ value }};
{% endfor %}
}
```

---

## Advanced Usage

### Accessing Nested Data

```jinja2
{% for r in reactions %}
Reaction {{ r.index }}:
  Reactants: {{ r.reactants|map(attribute='name')|join(', ') }}
  Products: {{ r.products|map(attribute='name')|join(', ') }}
{% endfor %}
```

### Custom Macros

Define reusable template components:

```jinja2
{% macro species_declaration(s) %}
const Species {{ s.name }} = {
    .name = "{{ s.name }}",
    .index = {{ s.index }},
    .initial = {{ s.initial_amount|default(0.0) }}
};
{% endmacro %}

{% for s in species %}
{{ species_declaration(s) }}
{% endfor %}
```

### Whitespace Control

Use `-` to strip whitespace:

```jinja2
const char* names[] = {
{%- for s in species %}
    "{{ s.name }}"{{ "," if not loop.last }}
{%- endfor %}
};
```

---

## Type Information

### Variable Types Summary

| Variable | Python Type | Description |
|----------|-------------|-------------|
| `network` | `Network` | Main network object |
| `species` | `list[Species]` | All species |
| `reactions` | `list[Reaction]` | All reactions |
| `rates` | `dict[str, float\|str]` | Rate parameters |

### Species Type

```python
class Species:
    name: str
    index: int
    id: str
    initial_amount: Optional[float]
    charge: Optional[int]
    compartment: Optional[str]
    boundary_condition: Optional[bool]
```

### Reaction Type

```python
class Reaction:
    index: int
    id: str
    equation: str
    reactants: list[Species]
    products: list[Species]
    reactant_stoichiometry: dict[str, int]
    product_stoichiometry: dict[str, int]
    rate_law: str
    reversible: bool
    modifiers: Optional[list[Species]]
```

---

## Examples by Language

### C Example

```jinja2
#define NUM_SPECIES {{ network.num_species }}
#define NUM_REACTIONS {{ network.num_reactions }}

typedef enum {
{% for s in species %}
    {{ s.name|upper }}_IDX = {{ s.index }}{{ "," if not loop.last }}
{% endfor %}
} species_index_t;

void reaction_rates(double *rates, double *species, double *params) {
{% for r in reactions %}
    rates[{{ r.index }}] = {{ r.rate_law }};
{% endfor %}
}
```

### Python Example

```jinja2
class {{ network.name|title }}Network:
    def __init__(self):
        self.species_names = [
        {%- for s in species %}
            "{{ s.name }}"{{ "," if not loop.last }}
        {%- endfor %}
        ]
        
        self.num_species = {{ network.num_species }}
        self.num_reactions = {{ network.num_reactions }}
    
    def compute_rates(self, species, params):
        rates = [0.0] * self.num_reactions
        {% for r in reactions %}
        rates[{{ r.index }}] = {{ r.rate_law }}
        {% endfor %}
        return rates
```

### MATLAB Example

```jinja2
function dydt = {{ network.name }}_ode(t, y, params)
    % Species indices
    {% for s in species %}
    {{ s.name }} = {{ s.index + 1 }}; % MATLAB uses 1-based indexing
    {% endfor %}
    
    % Reaction rates
    {% for r in reactions %}
    r{{ r.index }} = {{ r.rate_law }};
    {% endfor %}
    
    % ODEs
    dydt = zeros({{ network.num_species }}, 1);
    {% for r in reactions %}
    {% for species_name, coeff in r.product_stoichiometry.items() %}
    dydt({{ species_name }}) = dydt({{ species_name }}) + {{ coeff }} * r{{ r.index }};
    {% endfor %}
    {% for species_name, coeff in r.reactant_stoichiometry.items() %}
    dydt({{ species_name }}) = dydt({{ species_name }}) - {{ coeff }} * r{{ r.index }};
    {% endfor %}
    {% endfor %}
end
```

---

## See Also

- [Template Syntax Guide](../user-guide/template-syntax.md) - Learn Jinja2 syntax
- [Code Generation Guide](../user-guide/code-generation.md) - How to use templates
- [Primitive Variables](primitive-variables.md) - Built-in template helpers
- [API: CodeGenerator](../api/codegen.md) - Template engine API

---

## Related Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Template Examples Repository](https://github.com/your-org/codegen_class-templates)

---

*Last updated: 2024*
