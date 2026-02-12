# Release Process

Guide for releasing new versions of JAFF.

## Overview

JAFF uses semantic versioning and automated releases via GitHub Actions.

## Versioning

### Semantic Versioning

JAFF follows [Semantic Versioning 2.0.0](https://semver.org/):

**Format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Examples

- `1.0.0` → `1.0.1`: Bug fix
- `1.0.0` → `1.1.0`: New feature
- `1.0.0` → `2.0.0`: Breaking change

## Release Checklist

### Pre-Release

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in:
  - [ ] `setup.py`
  - [ ] `src/jaff/__init__.py`
  - [ ] `docs/conf.py` (if applicable)
- [ ] No outstanding critical issues
- [ ] Code reviewed

### Release Steps

1. **Update Version**

```bash
# Edit version in setup.py
VERSION = "1.1.0"

# Edit version in __init__.py
__version__ = "1.1.0"
```

2. **Update CHANGELOG**

```markdown
## [1.1.0] - 2024-02-01

### Added
- New feature X
- Support for Y

### Changed
- Improved Z

### Fixed
- Bug in W
```

3. **Commit Changes**

```bash
git add setup.py src/jaff/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 1.1.0"
git push origin main
```

4. **Create Tag**

```bash
# Create annotated tag
git tag -a v1.1.0 -m "Release version 1.1.0"

# Push tag
git push origin v1.1.0
```

5. **GitHub Release**

- Go to GitHub Releases
- Click "Draft a new release"
- Select tag `v1.1.0`
- Title: `v1.1.0`
- Description: Copy from CHANGELOG
- Click "Publish release"

### Post-Release

- [ ] Verify PyPI upload
- [ ] Verify documentation deployed
- [ ] Announce release
- [ ] Close milestone (if applicable)
- [ ] Update roadmap

## Automated Release

### GitHub Actions

The `.github/workflows/release.yml` workflow automatically:

1. Runs tests
2. Builds package
3. Publishes to PyPI
4. Updates documentation

**Triggered by**: Pushing a tag matching `v*.*.*`

### PyPI Credentials

Stored as GitHub secrets:

- `PYPI_USERNAME`
- `PYPI_PASSWORD`

Or use PyPI API token:
- `PYPI_API_TOKEN`

## Manual Release

If automated release fails:

### Build Package

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*
```

### Upload to TestPyPI

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ jaff
```

### Upload to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Verify
pip install jaff --upgrade
```

## Release Types

### Patch Release (1.0.0 → 1.0.1)

**Purpose**: Bug fixes only

**Steps**:
1. Fix bugs
2. Update CHANGELOG
3. Bump patch version
4. Release

### Minor Release (1.0.0 → 1.1.0)

**Purpose**: New features (backward compatible)

**Steps**:
1. Develop features
2. Update documentation
3. Update CHANGELOG
4. Bump minor version
5. Release

### Major Release (1.0.0 → 2.0.0)

**Purpose**: Breaking changes

**Steps**:
1. Plan breaking changes
2. Update code
3. Update all documentation
4. Write migration guide
5. Update CHANGELOG
6. Bump major version
7. Announce widely
8. Release

## Hotfix Process

For critical bugs in production:

```bash
# Create hotfix branch from tag
git checkout -b hotfix/1.0.1 v1.0.0

# Fix bug
git add .
git commit -m "fix: critical bug"

# Bump version
# Update CHANGELOG

# Merge to main
git checkout main
git merge hotfix/1.0.1

# Tag and release
git tag -a v1.0.1 -m "Hotfix: critical bug"
git push origin v1.0.1
```

## Documentation Release

### Update Documentation

```bash
# Build docs
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Versioned Docs (Optional)

Using `mike`:

```bash
# Install mike
pip install mike

# Deploy version
mike deploy --push --update-aliases 1.1 latest

# Set default version
mike set-default --push latest
```

## Announcement

### Where to Announce

- GitHub Releases (automatic)
- PyPI (automatic)
- GitHub Discussions
- Mailing list (if applicable)
- Social media
- Project website

### Announcement Template

```markdown
# JAFF v1.1.0 Released! 🎉

We're excited to announce the release of JAFF v1.1.0!

## ✨ What's New

- New feature: GPU code generation
- Improved: CSE optimization
- Fixed: Index offset bug in Fortran codegen

## 📦 Installation

```bash
pip install --upgrade jaff
```

## 📚 Documentation

https://tgrassi.github.io/jaff

## 🙏 Thanks

Thanks to all contributors!

Full changelog: https://github.com/tgrassi/jaff/blob/main/CHANGELOG.md
```

## Rollback Procedure

If a release has critical issues:

### Remove from PyPI

1. Mark release as "yanked" on PyPI
2. Release hotfix version immediately

### Revert Tag

```bash
# Delete local tag
git tag -d v1.1.0

# Delete remote tag
git push --delete origin v1.1.0

# Create new fixed version
git tag -a v1.1.1 -m "Hotfix for v1.1.0"
git push origin v1.1.1
```

## Release Schedule

### Regular Releases

- **Patch releases**: As needed (bug fixes)
- **Minor releases**: Monthly or when features are ready
- **Major releases**: Annually or for breaking changes

### Security Releases

- Released immediately when security issue is found
- Backported to supported versions

## Supported Versions

| Version | Supported | End of Life |
|---------|-----------|-------------|
| 1.x     | ✅ Yes    | TBD         |
| 0.9.x   | ⚠️ Limited| 2024-06-01  |
| < 0.9   | ❌ No     | 2024-01-01  |

## Testing Releases

### Pre-release Versions

```bash
# Alpha
git tag v1.1.0-alpha.1

# Beta
git tag v1.1.0-beta.1

# Release candidate
git tag v1.1.0-rc.1
```

### Install Pre-releases

```bash
pip install --pre jaff
```

## Troubleshooting

### Build Fails

- Check setup.py syntax
- Verify all files included in MANIFEST.in
- Check dependencies

### Upload Fails

- Verify PyPI credentials
- Check package name availability
- Ensure version not already uploaded

### Tag Issues

```bash
# List all tags
git tag -l

# Delete wrong tag
git tag -d v1.1.0
git push --delete origin v1.1.0

# Recreate correct tag
git tag -a v1.1.0 -m "Release 1.1.0"
git push origin v1.1.0
```

## See Also

- [Changelog](../about/changelog.md)
- [Contributing Guide](contributing.md)
- [Semantic Versioning](https://semver.org/)
- [PyPI Documentation](https://packaging.python.org/)
