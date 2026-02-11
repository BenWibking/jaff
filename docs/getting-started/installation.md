# Installation

This guide will help you install JAFF on your system.

## Requirements

JAFF requires Python 3.9 or higher. Check your Python version:

```bash
python --version
```

## Installation Methods

### Method 1: From PyPI (Recommended)

Once published, you can install JAFF directly from PyPI:

```bash
pip install jaff
```

### Method 2: From Source

For the latest development version or to contribute:

```bash
# Clone the repository
git clone https://github.com/tgrassi/jaff.git
cd jaff

# Install in regular mode
pip install .
```

### Method 3: Development Installation

If you plan to modify JAFF or contribute to development:

```bash
# Clone the repository
git clone https://github.com/tgrassi/jaff.git
cd jaff

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

This installs JAFF in "editable" mode, so changes you make to the source code are immediately reflected without reinstalling.

## Dependencies

JAFF automatically installs the following dependencies:

### Core Dependencies

- **numpy** (≥2.0.0) - Numerical computations
- **scipy** (≥1.13.0) - Scientific computing
- **sympy** (≥1.14.0) - Symbolic mathematics
- **tqdm** (≥4.67.1) - Progress bars
- **h5py** (≥3.9.0) - HDF5 file support

### Development Dependencies

When installing with `[dev]`:

- **pytest** (≥7.0) - Testing framework
- **pytest-cov** - Code coverage
- **ruff** - Linting and formatting
- **check-jsonschema** - JSON schema validation

## Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with other packages:

=== "Using venv"

    ```bash
    # Create virtual environment
    python -m venv jaff-env
    
    # Activate (Linux/macOS)
    source jaff-env/bin/activate
    
    # Activate (Windows)
    jaff-env\Scripts\activate
    
    # Install JAFF
    pip install jaff
    ```

=== "Using conda"

    ```bash
    # Create conda environment
    conda create -n jaff-env python=3.11
    
    # Activate
    conda activate jaff-env
    
    # Install JAFF
    pip install jaff
    ```

=== "Using uv"

    ```bash
    # Create virtual environment with uv (faster)
    uv venv
    
    # Activate
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows
    
    # Install JAFF
    uv pip install jaff
    ```

## Verifying Installation

After installation, verify that JAFF is working correctly:

```bash
# Check JAFF version
python -c "import jaff; print(jaff.__version__)"

# Run the CLI
jaff --help
```

You should see the JAFF help message listing available commands.

## Testing Your Installation

Try loading a sample network:

```python
from jaff import Network

# This will work if you're in the cloned repository
# or have sample network files
net = Network("networks/test.dat")
print(f"Loaded network with {len(net.species)} species")
print(f"and {len(net.reactions)} reactions")
```

## Troubleshooting

### ImportError: No module named 'jaff'

Make sure you've activated your virtual environment and that the installation completed successfully.

### Version Conflicts

If you encounter dependency conflicts:

```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing again
pip install jaff
```

### NumPy/SciPy Installation Issues

On some systems, you may need to install NumPy and SciPy separately:

```bash
# Install scientific stack first
pip install numpy scipy

# Then install JAFF
pip install jaff
```

### Permission Errors

If you get permission errors on Linux/macOS:

```bash
# Install for current user only
pip install --user jaff

# Or use sudo (not recommended)
sudo pip install jaff
```

## Platform-Specific Notes

### Windows

On Windows, you may need to install Microsoft Visual C++ Build Tools for some dependencies.

### macOS

If using Homebrew Python:

```bash
# Use Homebrew Python
brew install python
pip3 install jaff
```

### Linux

Most Linux distributions work out of the box. For minimal installations:

```bash
# Debian/Ubuntu - install Python and pip
sudo apt-get update
sudo apt-get install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip

# Then install JAFF
pip3 install jaff
```

## Next Steps

Now that JAFF is installed:

- **Quick Start**: Follow the [Quick Start Guide](quickstart.md) to run your first network analysis
- **Basic Concepts**: Learn about [chemical networks and reactions](concepts.md)
- **User Guide**: Explore detailed [usage documentation](../user-guide/loading-networks.md)

## Updating JAFF

To update to the latest version:

```bash
# Update from PyPI
pip install --upgrade jaff

# Update from source (development)
cd jaff
git pull
pip install -e ".[dev]"
```

## Uninstalling

To remove JAFF from your system:

```bash
pip uninstall jaff
```
