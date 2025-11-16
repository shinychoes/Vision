# Contributing to vision

First off, thank you for your interest in contributing to `vision`!

This document describes how to propose changes and how we work together within the `shinychoes` organization.

## Ways to contribute

- **Report bugs**
  - Use GitHub Issues.
  - Include clear steps to reproduce, expected behavior, and actual behavior.
- **Suggest features or improvements**
  - Open a GitHub Issue tagged as an enhancement or feature request.
  - Explain the motivation and potential impact.
- **Improve documentation**
  - Fix typos, clarify explanations, or extend docs where they are thin.
- **Code contributions**
  - Fix open issues, improve tests, refactor, or add well-motivated new functionality.

## Code of Conduct

By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

If you witness or experience unacceptable behavior, please refer to the reporting guidelines in the Code of Conduct.

## Development workflow

> These are general guidelines; adapt as needed for language- or subproject-specific workflows.

For now, most concrete code lives in the `UI_UX/` subdirectory (Python one-screen budget utilities). The `Vision/` directory is currently a placeholder for future vision/neural network components. See the root `README.md` and `UI_UX/README.md` for subproject-specific setup instructions.

1. **Fork the repository** (if you are external to `shinychoes`) and create your branch from `main`.
2. **Create a feature branch**
   - Use a descriptive name (e.g. `feature/add-visualizer`, `fix/augmentations-bug`).
3. **Make your changes**
   - Keep changes focused and atomic.
   - Add or update tests where appropriate.
4. **Run tests and linters**
   - Ensure existing tests pass.
   - Run formatters/linters used by the project.
5. **Open a Pull Request (PR)**
   - Explain the motivation and summarize the changes.
   - Link to related issues.
   - Include screenshots or logs if relevant (especially for UI or training improvements).

## Commit and pull request guidelines

- **Commits**
  - Make small, logical commits.
  - Use clear commit messages in the imperative mood (e.g. `Add dataset loader for X`).
- **Pull Requests**
  - Keep PRs focused; avoid large unrelated batches of changes.
  - Mark PRs as draft if early feedback is desired.
  - Be responsive to review comments and feel free to ask clarifying questions.

## Coding style

- Follow existing style in the files you are editing.
- Use language-appropriate formatters and linters (e.g. `black`/`ruff` for Python, `prettier`/`eslint` for JS/TS, etc.) where configured.
- Prefer clear, maintainable code with comments only where they add real value.

## Documentation

- Update `README.md`, `UI_UX/README.md`, or other relevant docs when behavior, APIs, or usage changes.
- Add docstrings or inline documentation where functions/classes are non-obvious.

## Issue triage

For maintainers within `shinychoes`:

- Label issues (bug, enhancement, question, etc.).
- Prioritize and assign issues as capacity allows.
- Close issues when resolved and reference the PR that fixed them.

## License

By submitting a contribution, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE), the same license that covers this project.
