# Repository Guidelines

## Project Structure & Module Organization

This workspace (`ai-model-learn`) currently has no source code, tests, assets, or build configuration. Keep the initial structure small and introduce directories only when needed:

- `src/` for reusable implementation code.
- `tests/` for automated tests, mirroring the source layout.
- `docs/` for setup instructions and technical notes.
- `examples/` for small, runnable demonstrations.

Add a root `README.md` when the first implementation lands. Document its purpose, prerequisites, and entry points.

## Build, Test, and Development Commands

No build, test, or local execution commands are configured yet. Use `ls -la` to inspect the workspace and `rg --files` to list nonignored files.

When introducing tooling, document exact install, run, and test commands in `README.md`. Declare dependencies in the chosen ecosystem's manifest and verify commands from the repository root. Once Git is initialized, run `git diff --check` before submitting changes to catch whitespace errors.

## Coding Style & Naming Conventions

Follow the selected language's standard conventions and keep indentation consistent within each file. Prefer descriptive module, function, and variable names. Use lowercase, underscore-separated filenames for Python modules if Python is introduced.

No formatter or linter is configured. Add shared configuration alongside the first relevant implementation; avoid unrelated formatting changes.

## Testing Guidelines

No testing framework or coverage threshold exists. Add tests with new behavior and regression tests with bug fixes. Keep tests deterministic and isolate external services or hardware dependencies. Document any fixtures, required resources, and the command for running the suite.

## Commit & Pull Request Guidelines

No Git history is available to establish existing conventions. Use concise, imperative commit subjects, such as `Add model loading example`, and keep commits focused.

Pull requests should explain the change, link relevant issues, and report validation commands and results. Explicitly note checks that were not run. Include screenshots only when visual behavior changes.

## Configuration & Generated Artifacts

Keep credentials, local environments, downloaded datasets, model weights, and generated outputs out of version control. Add appropriate `.gitignore` entries as these resources appear, and document how to obtain required artifacts.
