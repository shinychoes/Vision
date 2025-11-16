RELEASE.md

This document describes the recommended release process for `vision-ui`.

Prerequisites
- A GitHub repo with `GITHUB_TOKEN` set by Actions. Use `PYPI_API_TOKEN` for PyPI publishing.
- Repository should be in a clean state with all tests passing: `pytest -q`.

Local release (dry run)
1. Bump version in `pyproject.toml` (update `version = "0.xyz"`).
2. Build wheel and sdist:

```powershell
python -m pip install --upgrade build
python -m build
```

3. Install locally from dist and smoke test CLI:

```powershell
pip install dist/vision_ui-<version>-py3-none-any.whl
vision-ui --help
vision-ui summarize-multi --file UI_UX/README.md --profiles phone --format json
```

Publish to Test PyPI (optional)
1. Create a Test PyPI token from https://test.pypi.org.
2. Upload with twine:

```powershell
python -m pip install --upgrade twine
python -m twine upload --repository testpypi dist/*
```

Publish to PyPI (manual)
1. Create a PyPI token.
2. Upload with twine:

```powershell
python -m twine upload dist/*
```

GitHub Actions release (automated)
1. Add `PYPI_API_TOKEN` to repository secrets for automatic PyPI publishing.
2. Tag a release with semver (e.g., `git tag -a v0.1.0 -m "Release 0.1.0"`) and push the tag.
3. The `release.yml` workflow will build and publish artifacts automatically when a tag matching `v*` is pushed.

Notes
- The release workflow will attempt to publish to PyPI if `PYPI_API_TOKEN` exists; otherwise it will only create a release artifact (GitHub release with sdist/wheel attached).
- Use the `RELEASE.md` file as a guide for manual and automated releases, and keep it updated as packaging or CI changes.
