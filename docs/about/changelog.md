# Changelog

All notable changes to JAFF will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive MkDocs documentation with Material theme
- Complete API reference documentation
- User guides for all major features
- Interactive tutorials
- Template syntax documentation
- Network format specifications

### Changed
- Improved type annotations throughout codebase
- Enhanced docstrings for all public APIs
- Optimized CSE (Common Subexpression Elimination)

### Fixed
- Various bug fixes in network parsing
- Improved error messages

## [1.0.0] - 2024-01-15

### Added
- Initial stable release
- Support for multiple network formats (JAFF, KROME, KIDA, UDFA, PRIZMO, UCL_CHEM)
- Multi-language code generation (C, C++, Fortran, Python)
- Common Subexpression Elimination (CSE) optimization
- Template-based code generation with Fileparser
- Element analysis with Elements class
- Command-line interface (CLI)
- Comprehensive test suite

### Core Features
- Network loading and parsing
- Species and reaction management
- Rate coefficient calculation
- ODE system generation
- Analytical Jacobian generation
- Flux calculations
- Photochemistry support
- JAFF binary format for fast loading

## [0.9.0] - 2023-12-01

### Added
- Beta release for testing
- Basic documentation
- Examples directory

### Changed
- Refactored code generation system
- Improved performance for large networks

### Fixed
- Network validation issues
- CSE edge cases

## [0.8.0] - 2023-10-15

### Added
- Support for KROME format
- Support for UDFA format
- Basic CLI interface

### Changed
- Reorganized module structure
- Updated dependencies

## [0.7.0] - 2023-08-01

### Added
- Initial public alpha release
- JAFF native format parser
- Basic code generation for C++
- Fortran code generation
- Python code generation

### Known Issues
- Limited format support
- Documentation incomplete

## Version History Summary

| Version | Date | Major Changes |
|---------|------|---------------|
| 1.0.0 | 2024-01-15 | Stable release, full documentation |
| 0.9.0 | 2023-12-01 | Beta release, improved performance |
| 0.8.0 | 2023-10-15 | Added KROME/UDFA support |
| 0.7.0 | 2023-08-01 | Initial alpha release |

## Migration Guides

### Migrating from 0.9.x to 1.0.0

No breaking changes. All 0.9.x code should work with 1.0.0.

**New features available:**
```python
# Use new JAFF binary format for faster loading
net.to_jaff_file("network.jaff")
net2 = Network("network.jaff")

# Enhanced error checking
net = Network("network.dat", errors=True)
```

### Migrating from 0.8.x to 0.9.0

**Breaking changes:**
- `Codegen.get_rate()` renamed to `Codegen.get_rates()`
- `Network.load()` removed, use `Network(filename)` constructor

**Example migration:**
```python
# Old (0.8.x)
net = Network()
net.load("network.dat")
cg = Codegen(net)
rates = cg.get_rate()

# New (0.9.x+)
net = Network("network.dat")
cg = Codegen(network=net)
rates = cg.get_rates()
```

## Deprecation Notices

### Deprecated in 1.0.0
- None

### Removed in 1.0.0
- Legacy `Network.load()` method (use constructor)
- Old CLI syntax (updated to argparse-based)

## Future Plans

### Version 1.1.0 (Planned)
- Support for additional network formats
- GPU code generation (CUDA, HIP)
- Performance profiling tools
- Network visualization tools
- Interactive Jupyter widgets

### Version 1.2.0 (Planned)
- Machine learning integration
- Network optimization tools
- Automated testing framework
- Benchmark suite

### Version 2.0.0 (Future)
- Major API redesign
- Plugin system
- Database integration
- Cloud deployment support

## Contributing

We welcome contributions! See [Contributing Guide](../development/contributing.md) for details.

### Reporting Issues

Found a bug? Please report it:
- **GitHub Issues**: https://github.com/tgrassi/jaff/issues
- Include Python version, JAFF version, and minimal reproducible example

### Requesting Features

Have an idea? We'd love to hear it:
- Open a GitHub issue with the "enhancement" label
- Describe your use case
- Provide examples if possible

## Release Process

1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md with release notes
3. Create git tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions automatically builds and publishes to PyPI
6. Update documentation

## Security

### Reporting Security Issues

**Do not** open public issues for security vulnerabilities.

Instead, email security concerns to the maintainers (see README.md).

### Security Updates

Security fixes are released as patch versions (e.g., 1.0.1, 1.0.2) and backported to supported versions.

## License

JAFF is licensed under the MIT License. See [LICENSE](license.md) for details.

---

**See Also:**
- [Installation Guide](../getting-started/installation.md)
- [Quick Start](../getting-started/quickstart.md)
- [API Reference](../api/index.md)
