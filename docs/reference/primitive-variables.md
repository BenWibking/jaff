# Primitive Variables Reference

This page documents all primitive variables available in JAFF templates for code generation. Primitive variables are the basic building blocks that templates can use to access network data and generate code.

## Overview

Primitive variables are automatically populated by the JAFF code generation system and made available to templates through the Jinja2 templating engine. These variables provide access to:

- Network metadata and structure
- Species information
- Reaction details
- Rate constants and parameters
- Custom user-defined data

## Core Variables

### Network-Level Variables

#### `network`

The complete network object containing all species, reactions, and metadata.

**Type:** `Network`

**Attributes:**

- `network.name` (str): Network name
- `network.species` (list): List of all species
- `network.reactions` (list): List of all reactions
- `network.metadata` (dict): Additional metadata
- `network.description` (str): Network description

**Example:**

```jinja2
// Network: {{ network.name }}
// Total species: {{ network.species|length }}
// Total reactions: {{ network.reactions|length }}
```

#### `species`

List of all species in the network.

**Type:** `list[Species]`

**Example:**

```jinja2
{% for s in species %}
const {{ s.id }} = Species("{{ s.name }}");
{% endfor %}
```

#### `reactions`

List of all reactions in the network.

**Type:** `list[Reaction]`

**Example:**

```jinja2
{% for r in reactions %}
// Reaction {{ loop.index }}: {{ r.equation }}
{% endfor %}
```

### Species Variables

When iterating over species, each species object has the following attributes:

#### `id`

Unique identifier for the species.

**Type:** `str`

**Example:**

```jinja2
{{ species[0].id }}  // e.g., "sp1"
```

#### `name`

Human-readable name of the species.

**Type:** `str`

**Example:**

```jinja2
{{ species[0].name }}  // e.g., "Hydrogen"
```

#### `initial_amount`

Initial concentration or amount of the species.

**Type:** `float`

**Example:**

```jinja2
{{ species[0].initial_amount }}  // e.g., 1.0
```

#### `constant`

Whether the species concentration is constant (boundary condition).

**Type:** `bool`

**Example:**

```jinja2
{% if species[0].constant %}
// This is a boundary species
{% endif %}
```

#### `compartment`

Compartment where the species is located.

**Type:** `str` or `None`

**Example:**

```jinja2
{{ species[0].compartment }}  // e.g., "cytoplasm"
```

#### `metadata`

Additional species-specific metadata.

**Type:** `dict`

**Example:**

```jinja2
{{ species[0].metadata.molecular_weight }}
```

### Reaction Variables

When iterating over reactions, each reaction object has the following attributes:

#### `id`

Unique identifier for the reaction.

**Type:** `str`

**Example:**

```jinja2
{{ reactions[0].id }}  // e.g., "r1"
```

#### `name`

Human-readable name of the reaction.

**Type:** `str`

**Example:**

```jinja2
{{ reactions[0].name }}  // e.g., "Forward reaction"
```

#### `equation`

String representation of the reaction equation.

**Type:** `str`

**Example:**

```jinja2
{{ reactions[0].equation }}  // e.g., "A + B -> C"
```

#### `reactants`

List of reactant species with stoichiometry.

**Type:** `list[dict]`

**Structure:** Each item is `{"species": Species, "stoichiometry": float}`

**Example:**

```jinja2
{% for reactant in reactions[0].reactants %}
  {{ reactant.species.name }}: {{ reactant.stoichiometry }}
{% endfor %}
```

#### `products`

List of product species with stoichiometry.

**Type:** `list[dict]`

**Structure:** Each item is `{"species": Species, "stoichiometry": float}`

**Example:**

```jinja2
{% for product in reactions[0].products %}
  {{ product.species.name }}: {{ product.stoichiometry }}
{% endfor %}
```

#### `modifiers`

List of modifier species (catalysts, inhibitors).

**Type:** `list[Species]`

**Example:**

```jinja2
{% for modifier in reactions[0].modifiers %}
  {{ modifier.name }}
{% endfor %}
```

#### `rate_law`

The rate law expression for the reaction.

**Type:** `str` or `dict`

**Example:**

```jinja2
{{ reactions[0].rate_law }}  // e.g., "k1 * A * B"
```

#### `parameters`

Reaction-specific parameters (rate constants, etc.).

**Type:** `dict`

**Example:**

```jinja2
{{ reactions[0].parameters.k1 }}  // e.g., 0.001
```

#### `reversible`

Whether the reaction is reversible.

**Type:** `bool`

**Example:**

```jinja2
{% if reactions[0].reversible %}
// This is a reversible reaction
{% endif %}
```

#### `metadata`

Additional reaction-specific metadata.

**Type:** `dict`

**Example:**

```jinja2
{{ reactions[0].metadata.enzyme }}
```

## Parameter Variables

### `parameters`

Global parameters defined in the network.

**Type:** `dict`

**Example:**

```jinja2
{% for name, value in parameters.items() %}
const {{ name }} = {{ value }};
{% endfor %}
```

### Individual Parameter Access

Parameters can be accessed directly by name:

```jinja2
{{ k_forward }}  // Access parameter k_forward
{{ temperature }}  // Access parameter temperature
```

## Metadata Variables

### `metadata`

Network-level metadata dictionary.

**Type:** `dict`

**Example:**

```jinja2
{{ metadata.author }}
{{ metadata.created_date }}
{{ metadata.description }}
```

## Configuration Variables

### `config`

Code generation configuration settings.

**Type:** `dict`

**Available keys:**

- `config.language`: Target programming language
- `config.output_format`: Output format specification
- `config.precision`: Numerical precision
- `config.options`: Additional generation options

**Example:**

```jinja2
{% if config.language == "python" %}
# Python-specific code
{% elif config.language == "cpp" %}
// C++-specific code
{% endif %}
```

## Helper Variables

### Loop Variables

Jinja2 provides special loop variables when iterating:

#### `loop.index`

Current iteration (1-indexed).

```jinja2
{% for s in species %}
  // Species {{ loop.index }}: {{ s.name }}
{% endfor %}
```

#### `loop.index0`

Current iteration (0-indexed).

```jinja2
{% for s in species %}
  species[{{ loop.index0 }}] = "{{ s.name }}";
{% endfor %}
```

#### `loop.first`

True if this is the first iteration.

```jinja2
{% for s in species %}
  {% if loop.first %}
  // First species
  {% endif %}
{% endfor %}
```

#### `loop.last`

True if this is the last iteration.

```jinja2
{% for s in species %}
  {{ s.name }}{% if not loop.last %}, {% endif %}
{% endfor %}
```

#### `loop.length`

Total number of iterations.

```jinja2
{% for s in species %}
  // Processing {{ loop.index }} of {{ loop.length }}
{% endfor %}
```

### Mathematical Variables

#### `pi`

Mathematical constant π.

**Type:** `float`

**Value:** 3.141592653589793

```jinja2
const PI = {{ pi }};
```

#### `e`

Mathematical constant e (Euler's number).

**Type:** `float`

**Value:** 2.718281828459045

```jinja2
const E = {{ e }};
```

## Custom Variables

Users can define custom variables in their network files or pass them during code generation.

### Defining Custom Variables

In YAML format:

```yaml
custom_variables:
  simulation_time: 100.0
  output_interval: 0.1
  solver_type: "RK45"
```

### Accessing Custom Variables

```jinja2
const SIMULATION_TIME = {{ custom_variables.simulation_time }};
const OUTPUT_INTERVAL = {{ custom_variables.output_interval }};
const SOLVER = "{{ custom_variables.solver_type }}";
```

## Type Checking

### Checking Variable Types

```jinja2
{% if species is iterable %}
  // species is a list or iterable
{% endif %}

{% if network.name is string %}
  // network.name is a string
{% endif %}

{% if reactions[0].reversible is sameas true %}
  // Reaction is reversible
{% endif %}
```

## Conditional Variables

### Optional Variables

Some variables may not be present in all networks:

```jinja2
{% if compartment is defined %}
  // Compartment: {{ compartment }}
{% endif %}

{% if species[0].metadata.notes is defined %}
  // Notes: {{ species[0].metadata.notes }}
{% endif %}
```

## Variable Scope

### Template-Level Scope

Variables defined in templates are scoped to that template:

```jinja2
{% set num_species = species|length %}
// Total: {{ num_species }}
```

### Block-Level Scope

Variables defined in blocks are scoped to that block:

```jinja2
{% for r in reactions %}
  {% set reactant_count = r.reactants|length %}
  // Reaction with {{ reactant_count }} reactants
{% endfor %}
```

## Best Practices

### 1. Use Meaningful Variable Names

```jinja2
// Good
{% set species_count = species|length %}

// Avoid
{% set n = species|length %}
```

### 2. Check for Existence

```jinja2
{% if species[0].compartment is defined and species[0].compartment %}
  compartment = "{{ species[0].compartment }}";
{% endif %}
```

### 3. Use Filters for Formatting

```jinja2
// Capitalize names
{{ species[0].name|capitalize }}

// Format numbers
{{ parameters.k1|round(4) }}

// Safe string escaping
{{ reaction.equation|escape }}
```

### 4. Avoid Deep Nesting

```jinja2
// Good - use intermediate variables
{% set reaction_rate = reactions[0].parameters.k_forward %}
rate = {{ reaction_rate }};

// Avoid - deep nesting
rate = {{ reactions[0].parameters.k_forward }};
```

## Common Patterns

### Generating Arrays

```jinja2
double species_amounts[] = {
  {% for s in species %}
  {{ s.initial_amount }}{% if not loop.last %},{% endif %}
  {% endfor %}
};
```

### Generating Switch Statements

```jinja2
switch (reaction_id) {
  {% for r in reactions %}
  case {{ loop.index0 }}:  // {{ r.name }}
    return {{ r.parameters.k }};
  {% endfor %}
  default:
    return 0.0;
}
```

### Conditional Compilation

```jinja2
{% if config.debug_mode %}
#define DEBUG 1
{% endif %}

{% if config.use_openmp %}
#pragma omp parallel for
{% endif %}
```

## Examples

### Complete Variable Usage Example

```jinja2
/*
 * Network: {{ network.name }}
 * Generated: {{ metadata.generated_date }}
 * Species: {{ species|length }}
 * Reactions: {{ reactions|length }}
 */

#include <vector>
#include <string>

namespace {{ network.name|lower }} {

// Species definitions
enum SpeciesID {
  {% for s in species %}
  {{ s.id|upper }}{% if not loop.last %},{% endif %}  // {{ s.name }}
  {% endfor %}
};

// Initial conditions
const double initial_amounts[{{ species|length }}] = {
  {% for s in species %}
  {{ s.initial_amount }}{% if not loop.last %},{% endif %}  // {{ s.name }}
  {% endfor %}
};

// Reaction rate constants
{% for r in reactions %}
{% for param_name, param_value in r.parameters.items() %}
const double {{ r.id }}_{{ param_name }} = {{ param_value }};
{% endfor %}
{% endfor %}

// Rate laws
{% for r in reactions %}
double rate_{{ r.id }}(const double* species) {
  {% if r.rate_law %}
  return {{ r.rate_law }};
  {% else %}
  // Custom rate law for {{ r.name }}
  double rate = {{ r.parameters.k if r.parameters.k is defined else 1.0 }};
  {% for reactant in r.reactants %}
  rate *= pow(species[{{ reactant.species.id|upper }}], {{ reactant.stoichiometry }});
  {% endfor %}
  return rate;
  {% endif %}
}
{% endfor %}

} // namespace {{ network.name|lower }}
```

## See Also

- [Template Variables](template-variables.md) - Higher-level template variables
- [Template Syntax](../user-guide/template-syntax.md) - Jinja2 template syntax
- [Code Generation](../user-guide/code-generation.md) - Code generation guide
- [Network API](../api/network.md) - Network object API reference
