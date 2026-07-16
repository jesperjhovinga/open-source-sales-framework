# Open Source Sales Framework — common commands.
# `just` with no arguments lists everything.

default:
    @just --list

# Install the package and dev dependencies.
install:
    uv sync

# Run the test suite.
test *ARGS:
    uv run pytest {{ ARGS }}

# Test with a coverage report.
cov:
    uv run pytest --cov=bdcore --cov-report=term-missing

# Lint and type-check.
lint:
    uv run ruff check .
    uv run ty check

# Auto-fix lint findings and format.
fmt:
    uv run ruff check --fix .
    uv run ruff format .

# Fail if BD Core carries org-specific content (the seam is law).
seam:
    uv run bd check seam

# Fail if a normative doc claims a repo path that does not exist.
docs:
    uv run bd check docs

# Show the active org context.
context:
    uv run bd context

# Switch the active org. Usage: just use-context acme
use-context slug:
    @test -d "contexts/{{ slug }}" || { echo "ERROR: contexts/{{ slug }}/ does not exist"; exit 1; }
    @echo "{{ slug }}" > ACTIVE_CONTEXT.md
    @just context

# Validate a skill card's shape. Usage: just card skills/foo/skill-card.md
card path:
    uv run bd validate-card {{ path }}

# Everything CI runs.
ci: lint test seam docs
