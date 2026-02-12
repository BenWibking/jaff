# CLI API Reference

The CLI module provides a command-line interface for JAFF code generation, allowing you to process template files from the terminal.

## Overview

The `generate` module offers the main command-line interface for JAFF. It processes template files containing JAFF directives and generates code for chemical reaction networks in multiple programming languages.

## Module: `jaff.generate`

<!-- ::: jaff.generate
    options: -->

      <!-- show_root_heading: true
      <!-- show_source: true
      <!-- heading_level: 2

## Command-Line Interface

### Basic Usage

```bash
python -m jaff.generate --network <network_file> [options]
```

Or if installed:

```bash
jaff-generate --network <network_file> [options]
```

### Required Arguments

#### `--network`

Path to the chemical reaction network file.

**Type**: `str`

**Required**: Yes

**Example**:

```bash
python -m jaff.generate --network networks/react_COthin
```

### Optional Arguments

#### `--outdir`

Output directory where generated files will be saved.

**Type**: `str`

**Default**: Current working directory

**Example**:

```bash
python -m jaff.generate --network networks/react_COthin --outdir output/
```

#### `--indir`

Input directory containing template files to process. All files in this directory will be processed.

**Type**: `str`

**Default**: None

**Example**:

```bash
python -m jaff.generate --network networks/react_COthin --indir templates/
```

#### `--files`

Individual template files to process. You can specify multiple files.

**Type**: `list[str]`

**Default**: None

**Example**:

```bash
python -m jaff.generate --network networks/react_COthin --files template1.cpp template2.f90
```

## Functions

### main()

<!-- ::: jaff.generate.main
    options: -->

      <!-- show_root_heading: true
      <!-- show_source: true
      <!-- heading_level: 3

Main entry point for the JAFF code generator CLI.

**Raises**:

- `RuntimeError`: If no network file is supplied or no valid input files are found
- `FileNotFoundError`: If network file or input files don't exist or are invalid
- `NotADirectoryError`: If the output path is not a directory

## Usage Examples

### Process Single Template

```bash
# Generate code from a single template file
python -m jaff.generate \
    --network networks/react_COthin \
    --files templates/chemistry.cpp \
    --outdir output/
```

### Process Directory of Templates

```bash
# Generate code from all templates in a directory
python -m jaff.generate \
    --network networks/react_COthin \
    --indir templates/ \
    --outdir output/
```

### Process Multiple Templates

```bash
# Generate code from specific template files
python -m jaff.generate \
    --network networks/react_COthin \
    --files template1.cpp template2.f90 template3.c \
    --outdir generated/
```

### Default Output Directory

```bash
# Output to current directory (no --outdir specified)
python -m jaff.generate \
    --network networks/react_COthin \
    --files template.cpp
```

This will generate files in the current working directory with a warning message.

## Workflow

The CLI follows this workflow:

1. **Parse Arguments**: Extract command-line arguments
2. **Validate Network**: Check that network file exists and is valid
3. **Validate Output**: Ensure output directory exists or create it
4. **Collect Files**: Gather template files from `--indir` and/or `--files`
5. **Process Files**: For each template file:
    - Load the network
    - Create a Fileparser instance
    - Parse the template
    - Write output to the output directory
6. **Complete**: All files processed

## Error Handling

### Missing Network File

```bash
$ python -m jaff.generate --files template.cpp
RuntimeError: No network file supplied. Please enter a network file
```

### Network File Not Found

```bash
$ python -m jaff.generate --network missing.dat --files template.cpp
FileNotFoundError: Unable to find network file: /path/to/missing.dat
```

### No Input Files

```bash
$ python -m jaff.generate --network networks/react_COthin
RuntimeError: No valid input files have been supplied
```

### Invalid File Path

```bash
$ python -m jaff.generate --network networks/react_COthin --files missing.cpp
FileNotFoundError: Invalid file path missing.cpp
```

## Advanced Usage

### Combining Input Methods

You can combine `--indir` and `--files`:

```bash
# Process all files in templates/ plus specific files
python -m jaff.generate \
    --network networks/react_COthin \
    --indir templates/ \
    --files extra_template.cpp another_template.f90 \
    --outdir output/
```

### Creating Output Directory

The CLI automatically creates the output directory if it doesn't exist:

```bash
# output/ will be created if it doesn't exist
python -m jaff.generate \
    --network networks/react_COthin \
    --files template.cpp \
    --outdir output/new_folder/
```

### File Extensions

The CLI determines the target language from the file extension:

| Extension                                    | Language |
| -------------------------------------------- | -------- |
| `.cpp`, `.cxx`, `.cc`                        | C++      |
| `.hpp`, `.hxx`, `.hh`, `.h`                  | C/C++    |
| `.c`                                         | C        |
| `.f`, `.for`, `.f90`, `.f95`, `.f03`, `.f08` | Fortran  |

**Example**:

```bash
# These will use appropriate language-specific code generation
python -m jaff.generate \
    --network networks/react_COthin \
    --files chemistry.cpp rates.f90 solver.c \
    --outdir output/
```

## Integration with Build Systems

### Makefile Integration

```makefile
NETWORK = networks/react_COthin
TEMPLATES = $(wildcard templates/*.cpp)
OUTPUT_DIR = generated/

.PHONY: generate
generate:
	python -m jaff.generate \
		--network $(NETWORK) \
		--indir templates/ \
		--outdir $(OUTPUT_DIR)

.PHONY: clean
clean:
	rm -rf $(OUTPUT_DIR)
```

### CMake Integration

```cmake
# Generate code during configure
execute_process(
    COMMAND python -m jaff.generate
      <!--   --network ${CMAKE_SOURCE_DIR}/networks/react_COthin
      <!--   --indir ${CMAKE_SOURCE_DIR}/templates
      <!--   --outdir ${CMAKE_BINARY_DIR}/generated
    RESULT_VARIABLE JAFF_RESULT
)

if(NOT JAFF_RESULT EQUAL 0)
    message(FATAL_ERROR "JAFF code generation failed")
endif()

# Include generated files
include_directories(${CMAKE_BINARY_DIR}/generated)
```

### Python Script Integration

```python
import subprocess
from pathlib import Path

def generate_code(network_file, template_dir, output_dir):
    """Run JAFF code generation."""
    result = subprocess.run([
      <!--   'python', '-m', 'jaff.generate',
      <!--   '--network', network_file,
      <!--   '--indir', template_dir,
      <!--   '--outdir', output_dir
    ], capture_output=True, text=True)

    if result.returncode != 0:
      <!--   raise RuntimeError(f"Code generation failed: {result.stderr}")

    return result.stdout

# Usage
generate_code(
    network_file='networks/react_COthin',
    template_dir='templates/',
    output_dir='output/'
)
```

## Programmatic Usage

You can also call the CLI functionality directly from Python:

```python
from jaff.generate import main
import sys

# Set command-line arguments
sys.argv = [
    'jaff.generate',
    '--network', 'networks/react_COthin',
    '--files', 'template.cpp',
    '--outdir', 'output/'
]

# Run the generator
main()
```

Or use the underlying components directly:

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network
net = Network("networks/react_COthin")

# Process template
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# Write output
Path("output/").mkdir(exist_ok=True)
with open("output/template.cpp", "w") as f:
    f.write(output)
```

## Environment Variables

Currently, the CLI does not use environment variables, but you can set them in your shell scripts:

```bash
#!/bin/bash
export JAFF_NETWORK="networks/react_COthin"
export JAFF_OUTPUT="output/"

python -m jaff.generate \
    --network $JAFF_NETWORK \
    --files template.cpp \
    --outdir $JAFF_OUTPUT
```

## Exit Codes

| Code | Meaning                       |
| ---- | ----------------------------- |
| 0    | Success - all files processed |
| 1    | Error - see error message     |

## Logging and Output

The CLI provides informative messages during processing:

```bash
$ python -m jaff.generate --network networks/react_COthin --files template.cpp

No output directory has been supplied.
Files will be generated at /current/working/directory

Processing template.cpp...
Generated output/template.cpp
```

## See Also

- [File Parser API](file-parser.md) - Template parsing details
- [Code Generation Guide](../user-guide/code-generation.md) - How to create templates
- [Template Syntax](../user-guide/template-syntax.md) - JAFF directive reference
- [Tutorial: Code Generation](../tutorials/code-generation.md) - Step-by-step guide
