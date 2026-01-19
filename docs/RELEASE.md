# Release Process

This document describes how to create releases for the resokerr library.

## Overview

The release process is fully automated using GitHub Actions and Commitizen. Releases are triggered manually from the GitHub Actions UI, not automatically on push.

## Prerequisites

### 1. GitHub Repository Secrets

You need to configure the following secret in your GitHub repository:

| Secret Name | Description |
|-------------|-------------|
| `PYPI_API_TOKEN` | PyPI API token for publishing packages |

#### How to get a PyPI API Token:

1. Log in to [PyPI](https://pypi.org)
2. Go to **Account Settings** → **API tokens**
3. Click **Add API token**
4. Set the scope to "Entire account" or limit it to the `resokerr` project
5. Copy the token (starts with `pypi-`)

#### How to add the secret to GitHub:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI API token
6. Click **Add secret**

### 2. GitHub Environment (Optional but Recommended)

The workflow uses an environment called `release` for additional protection:

1. Go to **Settings** → **Environments**
2. Create a new environment called `release`
3. Optionally, add protection rules like:
   - Required reviewers
   - Deployment branches (e.g., only `main`)

## Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic version bumping.

### Commit Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Version Bump Rules

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `fix:`, `docs:`, `chore:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:` | PATCH (0.1.2 → 0.1.3) | `fix: correct validation logic` |
| `feat:` | MINOR (0.1.2 → 0.2.0) | `feat: add new Result method` |
| `BREAKING CHANGE:` in footer or `!` after type | MAJOR (0.1.2 → 1.0.0) | `feat!: redesign API` |

### Examples

```bash
# Patch version bump
git commit -m "fix: handle edge case in Ok.unwrap()"
git commit -m "docs: update README examples"
git commit -m "chore: update dependencies"

# Minor version bump
git commit -m "feat: add flat_map method to Result types"

# Major version bump
git commit -m "feat!: remove deprecated methods"
# or
git commit -m "feat: new API design

BREAKING CHANGE: Result.unwrap() now raises instead of returning None"
```

## Creating a Release

### 1. Navigate to GitHub Actions

1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. Select **Release** from the workflow list

### 2. Run the Workflow

1. Click **Run workflow**
2. Configure the options:

| Option | Default | Description |
|--------|---------|-------------|
| **Publish to PyPI** | ✅ `true` | Whether to upload the package to PyPI |
| **Dry run** | ❌ `false` | Simulation mode - no persistent changes |

3. Click **Run workflow**

### 3. Workflow Steps

The workflow will:

1. ✅ Analyze commits since the last tag
2. ✅ Determine the appropriate version bump (PATCH/MINOR/MAJOR)
3. ✅ Update version in `pyproject.toml`
4. ✅ Generate/update `CHANGELOG.md`
5. ✅ Create a commit with the bump message
6. ✅ Create and push an annotated git tag
7. ✅ Build distribution packages (wheel and sdist)
8. ✅ Validate the package with `twine check`
9. ✅ Publish to PyPI (if enabled)
10. ✅ Create a GitHub Release with release notes

### Dry Run Mode

When **Dry run** is enabled:

- ✅ Commits are analyzed
- ✅ Version bump is calculated
- ✅ Changelog preview is generated
- ✅ Package is built and validated
- ❌ No commits are created
- ❌ No tags are pushed
- ❌ No PyPI upload
- ❌ No GitHub Release

Use dry run to preview what would happen without making any changes.

## Local Development

### Installing Dev Dependencies

```bash
# Using pip with dependency groups (Python 3.11+)
pip install -e ".[dev]"

# Or install tools directly
pip install commitizen build twine
```

### Creating Commits with Commitizen

```bash
# Interactive commit helper
cz commit

# Or use git commit with conventional format
git commit -m "feat: add new feature"
```

### Preview Version Bump

```bash
# See what the next version would be
cz bump --dry-run
```

### Preview Changelog

```bash
# See what would be added to the changelog
cz changelog --dry-run
```

## Troubleshooting

### "No version bump needed"

This happens when there are no conventional commits since the last tag. Ensure your commits follow the conventional commits format.

### Authentication Failed (PyPI)

1. Verify the `PYPI_API_TOKEN` secret is set correctly
2. Check the token hasn't expired
3. Verify the token has permissions for the `resokerr` project

### Version Not Updating

1. Check that `pyproject.toml` has the correct `[tool.commitizen]` section
2. Verify `version_provider = "pep621"` is set (reads version from `[project].version`)

## Files Modified by Release Process

| File | Modification |
|------|--------------|
| `pyproject.toml` | Version number updated in `[project].version` section |
| `CHANGELOG.md` | New version section added with changes |

## How `cz bump` Works

When you run `cz bump --yes --changelog`, commitizen performs all these steps automatically:

1. **Analyzes commits** since the last tag to determine version increment (PATCH/MINOR/MAJOR)
2. **Updates version** in `pyproject.toml` (`[project].version` via PEP 621 provider)
3. **Updates CHANGELOG.md** with the new version section and commit messages
4. **Creates a commit** with the configured message: `chore: :bookmark: Bump version to X.Y.Z`
5. **Creates an annotated tag** in format `vX.Y.Z`

This single command replaces the entire manual release process.
