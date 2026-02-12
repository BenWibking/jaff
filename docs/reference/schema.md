# Schema Reference

This page provides a complete reference for all data schemas used in the JAFF codegen_class library.

## Overview

The JAFF library uses well-defined schemas for:

- **Network files**: JSON structure for chemical reaction networks
- **Configuration files**: YAML/JSON structure for code generation settings
- **Template metadata**: Schema for template configuration
- **API responses**: Structure of programmatic outputs

---

## Network File Schema

### Root Structure

The network file is a JSON document with the following top-level structure:

```json
{
  "network_name": "string",
  "description": "string (optional)",
  "species": [...],
  "reactions": [...],
  "parameters": {...} (optional),
  "metadata": {...} (optional)
}
```

### Fields

#### `network_name` (required)
- **Type**: `string`
- **Description**: Unique identifier for the network
- **Example**: `"glycolysis"`, `"mapk_pathway"`

#### `description` (optional)
- **Type**: `string`
- **Description**: Human-readable description of the network
- **Example**: `"Simplified glycolysis pathway"`

#### `species` (required)
- **Type**: `array` of species objects
- **Description**: List of all chemical species in the network
- **See**: [Species Schema](#species-schema)

#### `reactions` (required)
- **Type**: `array` of reaction objects
- **Description**: List of all reactions in the network
- **See**: [Reaction Schema](#reaction-schema)

#### `parameters` (optional)
- **Type**: `object`
- **Description**: Global parameters and constants
- **Example**:
```json
{
  "temperature": 298.15,
  "volume": 1.0,
  "avogadro": 6.022e23
}
```

#### `metadata` (optional)
- **Type**: `object`
- **Description**: Additional metadata about the network
- **Fields**:
    - `created`: ISO 8601 timestamp
    - `author`: string
    - `version`: string
    - `tags`: array of strings
    - `references`: array of citation strings

---

## Species Schema

Each species object in the `species` array has the following structure:

```json
{
  "id": "string",
  "name": "string",
  "initial_amount": number,
  "compartment": "string (optional)",
  "boundary": boolean (optional),
  "constant": boolean (optional),
  "metadata": {...} (optional)
}
```

### Fields

#### `id` (required)
- **Type**: `string`
- **Description**: Unique identifier for the species
- **Pattern**: `^[A-Za-z_][A-Za-z0-9_]*$` (valid identifier)
- **Example**: `"ATP"`, `"glucose_6p"`

#### `name` (required)
- **Type**: `string`
- **Description**: Display name of the species
- **Example**: `"Adenosine Triphosphate"`, `"Glucose-6-Phosphate"`

#### `initial_amount` (required)
- **Type**: `number`
- **Description**: Initial concentration or amount
- **Units**: Depends on model (typically mM or molecule count)
- **Example**: `1.0`, `1000`

#### `compartment` (optional)
- **Type**: `string`
- **Description**: Cellular compartment containing the species
- **Default**: `"default"`
- **Example**: `"cytoplasm"`, `"mitochondria"`, `"nucleus"`

#### `boundary` (optional)
- **Type**: `boolean`
- **Description**: Whether species is a boundary condition (fixed)
- **Default**: `false`

#### `constant` (optional)
- **Type**: `boolean`
- **Description**: Whether species amount is constant
- **Default**: `false`

#### `metadata` (optional)
- **Type**: `object`
- **Description**: Additional species-specific metadata
- **Example**:
```json
{
  "formula": "C10H16N5O13P3",
  "mass": 507.18,
  "charge": -4
}
```

---

## Reaction Schema

Each reaction object in the `reactions` array has the following structure:

```json
{
  "id": "string",
  "name": "string",
  "reactants": {...},
  "products": {...},
  "rate_law": "string",
  "parameters": {...},
  "reversible": boolean (optional),
  "metadata": {...} (optional)
}
```

### Fields

#### `id` (required)
- **Type**: `string`
- **Description**: Unique identifier for the reaction
- **Pattern**: `^[A-Za-z_][A-Za-z0-9_]*$`
- **Example**: `"R1"`, `"hexokinase"`

#### `name` (required)
- **Type**: `string`
- **Description**: Display name of the reaction
- **Example**: `"Hexokinase"`, `"Glucose phosphorylation"`

#### `reactants` (required)
- **Type**: `object`
- **Description**: Map of species IDs to stoichiometric coefficients
- **Example**:
```json
{
  "glucose": 1,
  "ATP": 1
}
```

#### `products` (required)
- **Type**: `object`
- **Description**: Map of species IDs to stoichiometric coefficients
- **Example**:
```json
{
  "glucose_6p": 1,
  "ADP": 1
}
```

#### `rate_law` (required)
- **Type**: `string`
- **Description**: Mathematical expression for reaction rate
- **Syntax**: Standard mathematical notation
- **Example**: `"k1 * glucose * ATP"`, `"Vmax * S / (Km + S)"`

#### `parameters` (required)
- **Type**: `object`
- **Description**: Kinetic parameters for the reaction
- **Example**:
```json
{
  "k1": 0.1,
  "Vmax": 10.0,
  "Km": 0.5
}
```

#### `reversible` (optional)
- **Type**: `boolean`
- **Description**: Whether reaction can proceed in reverse
- **Default**: `false`

#### `metadata` (optional)
- **Type**: `object`
- **Description**: Additional reaction metadata
- **Fields**:
    - `enzyme`: string
    - `ec_number`: string (e.g., "2.7.1.1")
    - `mechanism`: string
    - `references`: array of strings

---

## Configuration Schema

Configuration files (YAML or JSON) for code generation:

```yaml
# Output settings
output:
  directory: "generated"
  language: "python"  # or "c", "cpp", "julia", etc.
  filename: "network"

# Template settings
template:
  path: "templates/ode_model.jinja2"
  custom_variables:
    author: "Your Name"
    date: "2024-01-01"

# Code generation options
options:
  include_comments: true
  include_metadata: true
  vectorized: true
  sparse_jacobian: false
  
# Formatting
formatting:
  indent_size: 4
  line_width: 88
  use_tabs: false
```

### Configuration Fields

#### `output`
- **`directory`**: Output directory path (string)
- **`language`**: Target programming language (string)
- **`filename`**: Base filename without extension (string)

#### `template`
- **`path`**: Path to Jinja2 template file (string)
- **`custom_variables`**: Additional template variables (object)

#### `options`
- **`include_comments`**: Add explanatory comments (boolean, default: true)
- **`include_metadata`**: Include network metadata (boolean, default: true)
- **`vectorized`**: Use vectorized operations (boolean, default: false)
- **`sparse_jacobian`**: Generate sparse Jacobian (boolean, default: false)

#### `formatting`
- **`indent_size`**: Number of spaces per indent (integer, default: 4)
- **`line_width`**: Maximum line length (integer, default: 88)
- **`use_tabs`**: Use tabs instead of spaces (boolean, default: false)

---

## Template Metadata Schema

Template files can include YAML front matter:

```yaml
---
name: "ODE Model Template"
description: "Generates ODE system for simulation"
language: "python"
version: "1.0.0"
author: "JAFF Team"
requires:
  - numpy
  - scipy
outputs:
  - type: "module"
    extension: ".py"
variables:
  - name: "use_numba"
    type: "boolean"
    default: false
    description: "Enable Numba JIT compilation"
---
```

### Metadata Fields

#### `name` (required)
- **Type**: `string`
- **Description**: Template display name

#### `description` (optional)
- **Type**: `string`
- **Description**: Template purpose and functionality

#### `language` (required)
- **Type**: `string`
- **Description**: Target programming language

#### `version` (optional)
- **Type**: `string`
- **Description**: Template version (semver recommended)

#### `author` (optional)
- **Type**: `string`
- **Description**: Template author

#### `requires` (optional)
- **Type**: `array` of strings
- **Description**: Required libraries/dependencies

#### `outputs` (optional)
- **Type**: `array` of output objects
- **Fields**:
    - `type`: "module", "script", "header", etc.
    - `extension`: file extension (e.g., ".py", ".cpp")

#### `variables` (optional)
- **Type**: `array` of variable definition objects
- **Fields**:
    - `name`: variable name (string)
    - `type`: variable type (string)
    - `default`: default value (any)
    - `description`: explanation (string)

---

## API Response Schema

### Network Load Response

```json
{
  "success": true,
  "network": {
    "name": "string",
    "num_species": 10,
    "num_reactions": 8,
    "species": [...],
    "reactions": [...]
  },
  "warnings": [],
  "errors": []
}
```

### Code Generation Response

```json
{
  "success": true,
  "output_file": "path/to/generated/file.py",
  "template_used": "templates/ode_model.jinja2",
  "lines_generated": 250,
  "warnings": [],
  "errors": []
}
```

### Validation Response

```json
{
  "valid": true,
  "issues": [
    {
      "type": "warning",
      "location": "reactions[0].rate_law",
      "message": "Unused parameter 'k2'",
      "suggestion": "Remove from parameters or use in rate law"
    }
  ]
}
```

---

## Validation Rules

### Network Validation

1. **Species IDs must be unique**
   - Error: `"Duplicate species ID: 'ATP'"`

2. **Reaction IDs must be unique**
   - Error: `"Duplicate reaction ID: 'R1'"`

3. **Species referenced in reactions must exist**
   - Error: `"Unknown species 'glucose' in reaction 'R1'"`

4. **Rate law parameters must be defined**
   - Error: `"Undefined parameter 'k1' in rate law for reaction 'R1'"`

5. **Stoichiometric coefficients must be positive**
   - Error: `"Invalid stoichiometry: -1 for species 'ATP'"`

6. **Initial amounts must be non-negative**
   - Error: `"Negative initial amount for species 'glucose'"`

### Configuration Validation

1. **Template file must exist**
   - Error: `"Template not found: 'templates/missing.jinja2'"`

2. **Language must be supported**
   - Error: `"Unsupported language: 'fortran'"`

3. **Output directory must be writable**
   - Error: `"Cannot write to directory: '/readonly'"`

---

## Type Definitions

### Stoichiometry Map

```typescript
type StoichiometryMap = {
  [speciesId: string]: number  // positive integer
}
```

### Parameter Map

```typescript
type ParameterMap = {
  [paramName: string]: number  // any numeric value
}
```

### Metadata Object

```typescript
type Metadata = {
  [key: string]: string | number | boolean | array | object
}
```

---

## Schema Versioning

The JAFF schema follows semantic versioning:

- **Current version**: `1.0.0`
- **Compatibility**: Files with `schema_version` field are validated accordingly
- **Migration**: Tools provided for upgrading older schema versions

### Specifying Schema Version

Add to network file:

```json
{
  "schema_version": "1.0.0",
  "network_name": "my_network",
  ...
}
```

---

## Examples

### Complete Network File

```json
{
  "schema_version": "1.0.0",
  "network_name": "simple_enzyme",
  "description": "Simple enzyme kinetics",
  "species": [
    {
      "id": "S",
      "name": "Substrate",
      "initial_amount": 10.0,
      "compartment": "cytoplasm"
    },
    {
      "id": "E",
      "name": "Enzyme",
      "initial_amount": 1.0,
      "compartment": "cytoplasm",
      "constant": true
    },
    {
      "id": "P",
      "name": "Product",
      "initial_amount": 0.0,
      "compartment": "cytoplasm"
    }
  ],
  "reactions": [
    {
      "id": "R1",
      "name": "Enzymatic conversion",
      "reactants": {"S": 1},
      "products": {"P": 1},
      "rate_law": "Vmax * E * S / (Km + S)",
      "parameters": {
        "Vmax": 10.0,
        "Km": 0.5
      },
      "reversible": false,
      "metadata": {
        "mechanism": "Michaelis-Menten"
      }
    }
  ],
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "author": "JAFF User",
    "version": "1.0"
  }
}
```

---

## Related Documentation

- [Network Formats](formats.md) - Supported file formats
- [Template Variables](template-variables.md) - Variables in templates
- [CLI Reference](../api/cli.md) - Command-line usage
- [API Reference](../api/overview.md) - Programmatic API

---

## JSON Schema Files

Formal JSON Schema definitions are available:

- `schemas/network.schema.json` - Network file schema
- `schemas/config.schema.json` - Configuration file schema
- `schemas/template.schema.json` - Template metadata schema

Use these for validation in your editor or CI/CD pipeline.
