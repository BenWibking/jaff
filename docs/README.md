# JAFF Documentation

This directory contains the source files for the JAFF documentation site, built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## Building the Documentation

### Prerequisites

Install the required dependencies:

```bash
pip install -r docs/requirements.txt
```

Or install JAFF with documentation dependencies:

```bash
pip install -e ".[docs]"
```

### Local Development

To build and serve the documentation locally:

```bash
# Serve with live reload (recommended for development)
mkdocs serve

# The site will be available at http://127.0.0.1:8000
```

### Building Static Site

To build the static HTML site:

```bash
# Build the site
mkdocs build

# Output will be in the site/ directory
```

### Strict Mode

Build with strict mode to catch warnings as errors:

```bash
mkdocs build --strict
```

## Documentation Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/            # Installation and quick start
│   ├── installation.md
│   ├── quickstart.md
│   └── concepts.md
├── user-guide/                 # Detailed user guides
│   ├── loading-networks.md
│   ├── network-formats.md
│   ├── species.md
│   ├── reactions.md
│   ├── rates.md
│   ├── code-generation.md
│   └── template-syntax.md
├── tutorials/                  # Step-by-step tutorials
│   ├── basic-usage.md
│   ├── code-generation.md
│   ├── custom-templates.md
│   └── network-analysis.md
├── api/                        # API reference
│   ├── index.md
│   ├── network.md
│   ├── species.md
│   ├── reaction.md
│   ├── codegen.md
│   ├── file-parser.md
│   ├── elements.md
│   └── cli.md
├── reference/                  # Reference documentation
│   ├── formats.md
│   ├── jaff-commands.md
│   ├── template-variables.md
│   ├── primitive-variables.md
│   └── schema.md
├── development/                # Development guides
│   ├── contributing.md
│   ├── code-style.md
│   ├── testing.md
│   └── releases.md
├── about/                      # About pages
│   ├── license.md
│   ├── changelog.md
│   └── credits.md
├── assets/                     # Images and media
├── stylesheets/                # Custom CSS
│   └── extra.css
├── javascripts/                # Custom JavaScript
│   └── mathjax.js
└── requirements.txt            # Documentation dependencies
```

## Writing Documentation

### Markdown Format

Documentation is written in Markdown with MkDocs Material extensions:

- **Admonitions**: `!!! note`, `!!! warning`, `!!! tip`
- **Code blocks**: Use triple backticks with language
- **Tabbed content**: Use `===` for tabs
- **LaTeX math**: Use `\(...\)` for inline, `\[...\]` for display
- **Icons**: Use `:material-icon-name:` syntax

### Code Blocks

Use proper syntax highlighting:

````markdown
```python
from jaff import Network
net = Network("networks/test.dat")
```
````

### Admonitions

```markdown
!!! note "Important Note"
    This is a note with a custom title.

!!! warning
    This is a warning.

!!! tip "Pro Tip"
    This is a helpful tip.
```

### API Documentation

API docs are auto-generated from docstrings using `mkdocstrings`:

```markdown
::: jaff.network.Network
    options:
      show_root_heading: true
      show_source: true
```

### LaTeX Math

Use MathJax for mathematical expressions:

```markdown
Inline math: \( E = mc^2 \)

Display math:
\[
\frac{dn_i}{dt} = \sum_j \nu_{ij} k_j \prod_k n_k^{\alpha_{jk}}
\]
```

### Links

- Internal: `[Link Text](page.md)`
- External: `[Link Text](https://example.com)`
- API reference: `[Network](../api/network.md)`

## Deployment

### GitHub Pages

Documentation is automatically deployed to GitHub Pages via GitHub Actions.

The workflow is defined in `.github/workflows/docs.yml` and triggers on:
- Push to `main` or `master` branch
- Pull requests (build only, no deploy)
- Manual workflow dispatch

### Manual Deployment

To deploy manually to GitHub Pages:

```bash
# Build and deploy
mkdocs gh-deploy

# With custom commit message
mkdocs gh-deploy -m "Update documentation"
```

## Configuration

The documentation is configured in `mkdocs.yml` at the repository root.

Key configurations:

- **Theme**: Material theme with custom colors
- **Plugins**: mkdocstrings, git-revision-date, git-authors, search, minify
- **Extensions**: PyMdown Extensions for enhanced Markdown features
- **Navigation**: Defined in the `nav` section

## Contributing

When adding new documentation:

1. **Create the file** in the appropriate directory
2. **Add to navigation** in `mkdocs.yml` under the `nav` section
3. **Follow style guide**:
   - Use clear, concise language
   - Include code examples
   - Add cross-references
   - Use proper headings hierarchy
4. **Test locally** with `mkdocs serve`
5. **Build in strict mode** to catch issues
6. **Submit PR** with documentation changes

## Troubleshooting

### Build Errors

**Missing dependencies**:
```bash
pip install -r docs/requirements.txt
```

**Import errors**:
```bash
# Install JAFF in editable mode
pip install -e .
```

**Plugin errors**:
```bash
# Reinstall mkdocs-material and plugins
pip install --upgrade mkdocs-material mkdocstrings[python]
```

### Preview Issues

**Port already in use**:
```bash
# Use a different port
mkdocs serve -a localhost:8001
```

**Live reload not working**:
```bash
# Use polling mode
mkdocs serve --dirtyreload
```

## Tools and Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)
- [Markdown Guide](https://www.markdownguide.org/)

## Style Guide

### Headings

- Use Title Case for page titles (H1)
- Use Sentence case for section headings (H2+)
- Don't skip heading levels
- Keep headings concise

### Code Examples

- Always include imports
- Use realistic examples
- Add comments for clarity
- Test code before documenting

### Voice and Tone

- Use second person ("you") for instructions
- Be clear and direct
- Avoid jargon when possible
- Define technical terms on first use

### Formatting

- **Bold** for UI elements and emphasis
- *Italic* for introducing new terms
- `Code` for code, filenames, and commands
- Links for cross-references

## License

Documentation is licensed under the same license as the JAFF project (MIT License).
