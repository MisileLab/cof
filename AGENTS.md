# AGENTS.md

This file is guidance for coding agents working in this repository.
Follow it before making changes.

## Scope and sources
- No Cursor rules found in `.cursor/rules/` or `.cursorrules`.
- No Copilot rules found in `.github/copilot-instructions.md`.
- Primary references: `pyproject.toml`, `README.md`, `tests/README.md`, and existing code in `src/cof`.

## Project overview
- Language: Python 3.8+.
- Package manager: uv (PEP 735 dependency-groups in `pyproject.toml`).
- Tests: pytest, pytest-asyncio, pytest-timeout.
- CLI: click-based entrypoint `cof` -> `cof.main:cli`.

## Build / install / run
Use uv for local setup and installs.

### Install dependencies
- `uv sync` (install project dependencies).
- `uv sync --dev` (install dev dependencies, including pytest).
- Alternative (pip): `pip install -e ".[dev]"`.

### Tool install (global)
- `uv tool install git+https://github.com/misilelab/cof`.

### Running the CLI locally
- `uv run cof --help` (preferred, ensures env is synced).
- `cof --help` (if your shell env is already configured).

## Tests
pytest configuration lives in `pyproject.toml`.

### Run all tests
- `pytest`

### Run a single file
- `pytest tests/<file>.py`

### Run a class
- `pytest tests/<file>.py::TestClass`

### Run a single test function
- `pytest tests/<file>.py::TestClass::test_function`

### Other common options
- `pytest -v`
- `pytest --lf`

## Linting / formatting / typing
- No explicit lint or format commands are defined in this repo.
- `.gitignore` includes `.ruff_cache/` and `.mypy_cache/`, but no config files were found.
- If you add linting or type-checking, document the commands in this file.

## Code style and conventions
Follow existing patterns in `src/cof` and `tests/`.

### Imports
- Group imports in this order: standard library, third-party, local.
- Keep all imports at the top of the file.
- Prefer explicit imports over `import *`.

### Types and data modeling
- Use type hints throughout public functions and class methods.
- Favor `@dataclass` for simple data containers.
- Use `Enum` classes for protocol constants and options.
- Keep `Optional[...]` explicit when `None` is valid.

### Naming
- Classes: `PascalCase`.
- Functions and methods: `snake_case`.
- Constants: `UPPER_CASE`.
- Test classes: `Test*` and test functions `test_*`.

### Error handling
- CLI-facing errors should raise `click.ClickException` with clear messages.
- Use custom exceptions for domain errors when needed.
- Avoid swallowing exceptions; log or re-raise with context.

### Logging
- Use module-level `logger = logging.getLogger(__name__)`.
- Prefer structured messages and include key identifiers (session_id, repo_path, etc.).
- CLI uses `logging.basicConfig(..., force=True)` in `cof.main`.

### Async patterns
- Use `async`/`await` consistently when you introduce async workflows.
- For async context managers, implement `__aenter__`/`__aexit__`.
- Avoid blocking calls inside async flows (use asyncio-friendly APIs).

### File I/O
- Use `Path` for path manipulation where possible.
- Keep reads/writes explicit and handle missing files gracefully.

### JSON and serialization
- Use `json.dumps(..., sort_keys=True)` for content hashing and deterministic output.
- Validate JSON content before usage; handle decode errors.

## Testing conventions
- Use pytest fixtures for common setup.
- Group related tests into `Test*` classes.
- Use `@pytest.mark.asyncio` for async tests.
- Use `pytest.raises(...)` for exception assertions.
- Use timeouts for network operations (`@pytest.mark.timeout`).

## Working with the storage model
- Object hashes are BLAKE3 hex strings.
- Objects are stored under `.cof/objects/{hot,warm,cold}`.
- Staging is stored in `.cof/index/staging.json`.
- Keep tier migration and garbage collection logic localized in storage modules.

## Files to review before large changes
- `src/cof/main.py` (CLI and repo operations)
- `src/cof/storage.py` (block storage)
- `src/cof/models.py` (dataclasses and types)
- `tests/` (test patterns)

## Adding new commands or features
- Expose new CLI commands via `click` in `src/cof/main.py`.
- Keep command behavior consistent with existing commands and errors.
- Add tests in `tests/` with clear, isolated fixtures.

## Documentation updates
- If you add or change commands, update `README.md` and this file.
- Keep instructions runnable and minimal.

## Safety and repo hygiene
- Do not commit secrets or credentials (see `.gitignore` entries).
- Keep changes minimal and aligned with existing patterns.
- Avoid refactors when fixing a bug unless requested.

## Suggested validation flow
1. `uv sync --dev`
2. `pytest` (or the relevant targeted test)

## References (external)
- uv docs (sync/commands): https://docs.astral.sh/uv/
- pytest invocation: https://docs.pytest.org/en/stable/how-to/usage.html
- Ruff linter: https://docs.astral.sh/ruff/linter/
- Mypy CLI: https://mypy.readthedocs.io/en/stable/command_line.html
