# JAFF Command Reference

This page provides a complete reference for all JAFF (JSON Aggregated File Format) command-line interface commands and options.

## Overview

JAFF provides a powerful CLI for working with chemical reaction network files. The main commands allow you to parse, validate, convert, and analyze network files.

## Installation

After installing the package, the `jaff` command becomes available:

```bash
pip install codegen-class
```

## Global Options

These options can be used with any JAFF command:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message and exit |
| `--version` | Show version information |
| `--verbose`, `-v` | Enable verbose output |
| `--quiet`, `-q` | Suppress all output except errors |
| `--log-level LEVEL` | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

## Commands

### `jaff parse`

Parse and validate a network file.

**Usage:**
```bash
jaff parse [OPTIONS] INPUT_FILE
```

**Arguments:**

- `INPUT_FILE` - Path to the network file to parse

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | string | auto | Input format (jaff, chemkin, cantera, sbml, auto) |
| `--validate` | flag | True | Validate the parsed network |
| `--strict` | flag | False | Use strict validation mode |
| `--output`, `-o` | path | - | Output file for parsed network (JSON) |
| `--pretty` | flag | False | Pretty-print JSON output |

**Examples:**

```bash
# Parse a JAFF file with validation
jaff parse network.jaff

# Parse and output to JSON
jaff parse network.jaff -o output.json --pretty

# Parse CHEMKIN file with strict validation
jaff parse mech.ck --format chemkin --strict

# Parse without validation
jaff parse network.jaff --no-validate
```

**Exit Codes:**

- `0` - Success
- `1` - Parse error
- `2` - Validation error
- `3` - File not found

---

### `jaff convert`

Convert between different network file formats.

**Usage:**
```bash
jaff convert [OPTIONS] INPUT_FILE OUTPUT_FILE
```

**Arguments:**

- `INPUT_FILE` - Source network file
- `OUTPUT_FILE` - Destination file path

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--from`, `-f` | string | auto | Source format |
| `--to`, `-t` | string | auto | Target format (detected from extension) |
| `--validate` | flag | True | Validate during conversion |
| `--preserve-comments` | flag | False | Preserve comments when possible |

**Supported Formats:**

- `jaff` - JAFF JSON format
- `chemkin` - CHEMKIN format
- `cantera` - Cantera YAML format
- `sbml` - Systems Biology Markup Language

**Examples:**

```bash
# Convert CHEMKIN to JAFF
jaff convert mech.ck network.jaff

# Convert with explicit formats
jaff convert input.txt output.yaml --from chemkin --to cantera

# Convert and preserve comments
jaff convert network.jaff output.ck --preserve-comments
```

---

### `jaff validate`

Validate a network file against schema and consistency rules.

**Usage:**
```bash
jaff validate [OPTIONS] INPUT_FILE
```

**Arguments:**

- `INPUT_FILE` - Network file to validate

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | string | auto | File format |
| `--strict` | flag | False | Enable strict validation |
| `--schema` | path | - | Custom JSON schema file |
| `--check-thermodynamics` | flag | False | Validate thermodynamic consistency |
| `--check-mass-balance` | flag | False | Check mass balance for all reactions |
| `--report`, `-r` | path | - | Output validation report to file |

**Validation Checks:**

1. **Schema Validation** - JSON structure matches schema
2. **Reference Integrity** - All species referenced exist
3. **Uniqueness** - No duplicate species or reaction IDs
4. **Mass Balance** - Reactions conserve mass (optional)
5. **Thermodynamic Consistency** - Rates and equilibria are consistent (optional)

**Examples:**

```bash
# Basic validation
jaff validate network.jaff

# Strict validation with all checks
jaff validate network.jaff --strict --check-thermodynamics --check-mass-balance

# Validate with custom schema
jaff validate network.jaff --schema custom-schema.json

# Generate validation report
jaff validate network.jaff --report validation-report.txt
```

---

### `jaff info`

Display information about a network file.

**Usage:**
```bash
jaff info [OPTIONS] INPUT_FILE
```

**Arguments:**

- `INPUT_FILE` - Network file to analyze

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | string | auto | File format |
| `--detailed`, `-d` | flag | False | Show detailed statistics |
| `--species` | flag | False | List all species |
| `--reactions` | flag | False | List all reactions |
| `--output`, `-o` | path | - | Save info to file |

**Information Displayed:**

- Number of species
- Number of reactions
- Network metadata (if present)
- File format and version
- Statistics (min/max stoichiometry, rate constants, etc.)

**Examples:**

```bash
# Basic info
jaff info network.jaff

# Detailed statistics
jaff info network.jaff --detailed

# List all species
jaff info network.jaff --species

# Save info to file
jaff info network.jaff --output network-info.txt
```

---

### `jaff generate`

Generate code from a network file using templates.

**Usage:**
```bash
jaff generate [OPTIONS] INPUT_FILE
```

**Arguments:**

- `INPUT_FILE` - Network file to generate code from

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--template`, `-t` | path | - | Template file or directory |
| `--output`, `-o` | path | `./generated` | Output directory |
| `--language`, `-l` | string | - | Target language (python, cpp, fortran, julia) |
| `--format`, `-f` | string | auto | Input format |
| `--config`, `-c` | path | - | Configuration file for code generation |
| `--force` | flag | False | Overwrite existing files |
| `--dry-run` | flag | False | Show what would be generated without writing |

**Built-in Templates:**

- `python` - Python/NumPy implementation
- `cpp` - C++ implementation
- `fortran` - Fortran 90 implementation
- `julia` - Julia implementation
- `matlab` - MATLAB implementation

**Examples:**

```bash
# Generate Python code
jaff generate network.jaff --language python

# Generate with custom template
jaff generate network.jaff --template my-template.j2 --output ./src

# Dry run to preview
jaff generate network.jaff --language cpp --dry-run

# Generate with configuration
jaff generate network.jaff --config codegen-config.yaml
```

---

### `jaff merge`

Merge multiple network files into one.

**Usage:**
```bash
jaff merge [OPTIONS] FILE1 FILE2 [FILE3 ...] OUTPUT_FILE
```

**Arguments:**

- `FILE1, FILE2, ...` - Network files to merge
- `OUTPUT_FILE` - Output merged network file

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | string | union | Merge strategy (union, intersection) |
| `--resolve-conflicts` | string | error | Conflict resolution (error, first, last, merge) |
| `--validate` | flag | True | Validate merged network |
| `--preserve-metadata` | flag | True | Keep metadata from source files |

**Examples:**

```bash
# Merge two networks
jaff merge network1.jaff network2.jaff merged.jaff

# Merge with conflict resolution
jaff merge net1.jaff net2.jaff merged.jaff --resolve-conflicts first

# Merge multiple files
jaff merge *.jaff combined.jaff
```

---

### `jaff diff`

Compare two network files and show differences.

**Usage:**
```bash
jaff diff [OPTIONS] FILE1 FILE2
```

**Arguments:**

- `FILE1` - First network file
- `FILE2` - Second network file

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | string | text | Output format (text, json, html) |
| `--output`, `-o` | path | - | Save diff to file |
| `--ignore-order` | flag | False | Ignore ordering of species/reactions |
| `--tolerance` | float | 1e-10 | Numerical tolerance for rate comparisons |
| `--context`, `-c` | int | 3 | Context lines in diff output |

**Examples:**

```bash
# Compare two files
jaff diff network1.jaff network2.jaff

# Compare with tolerance
jaff diff old.jaff new.jaff --tolerance 1e-6

# Generate HTML diff report
jaff diff v1.jaff v2.jaff --format html --output diff.html
```

---

### `jaff export`

Export network data in various formats for analysis or visualization.

**Usage:**
```bash
jaff export [OPTIONS] INPUT_FILE
```

**Arguments:**

- `INPUT_FILE` - Network file to export

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | string | - | Export format (csv, graphml, dot, json) |
| `--output`, `-o` | path | - | Output file |
| `--species-only` | flag | False | Export only species data |
| `--reactions-only` | flag | False | Export only reactions data |

**Export Formats:**

- `csv` - Comma-separated values (species or reactions table)
- `graphml` - GraphML network representation
- `dot` - Graphviz DOT format
- `json` - Plain JSON (non-JAFF structure)

**Examples:**

```bash
# Export to CSV
jaff export network.jaff --format csv --output species.csv --species-only

# Export network graph
jaff export network.jaff --format graphml --output network.graphml

# Export to Graphviz
jaff export network.jaff --format dot --output network.dot
```

---

## Configuration Files

JAFF commands can read settings from configuration files to avoid repetitive command-line arguments.

### Configuration File Format

Configuration files use YAML format:

```yaml
# jaff-config.yaml
parse:
  validate: true
  strict: false
  
generate:
  language: python
  output: ./generated
  template: custom-template.j2
  
validate:
  check_mass_balance: true
  check_thermodynamics: false
```

### Using Configuration Files

```bash
# Use config file
jaff --config jaff-config.yaml parse network.jaff

# Command-line options override config
jaff --config config.yaml parse network.jaff --strict
```

---

## Environment Variables

JAFF respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `JAFF_CONFIG` | Default configuration file | - |
| `JAFF_TEMPLATE_DIR` | Directory for custom templates | `~/.jaff/templates` |
| `JAFF_LOG_LEVEL` | Default logging level | `INFO` |
| `JAFF_CACHE_DIR` | Cache directory | `~/.jaff/cache` |

---

## Return Codes

All JAFF commands use consistent return codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Validation error |
| 3 | File not found |
| 4 | Parse error |
| 5 | Configuration error |
| 10 | Internal error |

---

## Batch Processing

### Processing Multiple Files

Use shell wildcards and loops:

```bash
# Validate all JAFF files
for file in *.jaff; do
  jaff validate "$file"
done

# Convert all CHEMKIN files
for file in *.ck; do
  jaff convert "$file" "${file%.ck}.jaff"
done
```

### Using `xargs`

```bash
# Parallel validation
find . -name "*.jaff" | xargs -P 4 -I {} jaff validate {}
```

---

## Scripting Examples

### Python Script

```python
import subprocess
import sys

def validate_network(filename):
    result = subprocess.run(
        ['jaff', 'validate', filename],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

if __name__ == '__main__':
    if validate_network('network.jaff'):
        print("Validation passed!")
        sys.exit(0)
    else:
        print("Validation failed!")
        sys.exit(1)
```

### Bash Script

```bash
#!/bin/bash

# Convert and validate pipeline
convert_and_validate() {
  local input=$1
  local output=$2
  
  jaff convert "$input" "$output" || {
    echo "Conversion failed"
    return 1
  }
  
  jaff validate "$output" --strict || {
    echo "Validation failed"
    return 2
  }
  
  echo "Success!"
  return 0
}

convert_and_validate "input.ck" "output.jaff"
```

---

## Advanced Usage

### Custom Templates

Create your own Jinja2 templates for code generation:

```bash
# Use custom template directory
export JAFF_TEMPLATE_DIR=~/my-templates

# Generate with custom template
jaff generate network.jaff --template my-custom.j2
```

### Pipeline Integration

```bash
# Parse, validate, and generate in one pipeline
jaff parse input.ck --output temp.jaff && \
jaff validate temp.jaff --strict && \
jaff generate temp.jaff --language python
```

---

## Debugging

### Enable Verbose Output

```bash
# Show debug information
jaff --log-level DEBUG parse network.jaff

# Very verbose
jaff -vvv parse network.jaff
```

### Validation Debugging

```bash
# Get detailed validation report
jaff validate network.jaff --strict --report validation.log

# Check specific aspects
jaff validate network.jaff --check-mass-balance --check-thermodynamics
```

---

## See Also

- [Format Reference](formats.md) - Network file format specifications
- [Template Variables](template-variables.md) - Variables available in templates
- [Code Generation Guide](../user-guide/code-generation.md) - Detailed code generation documentation
- [Network Formats](../user-guide/network-formats.md) - Supported network formats

---

## Getting Help

- Use `--help` with any command for detailed usage
- Visit the [GitHub repository](https://github.com/your-username/codegen_class)
- Check [troubleshooting guide](../getting-started/troubleshooting.md)
- Report issues on [GitHub Issues](https://github.com/your-username/codegen_class/issues)
