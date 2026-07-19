"""Read external-API secrets from the environment (and an optional .env file).

Most connectors bind through Claude's MCP and need no secret here — see
`contexts/<org>/connectors.md`. This covers the few external APIs a skill may
call directly. Keys are read from real environment variables first; a `.env`
file at the repo root fills in anything not already set (never overriding it,
so an exported var always wins). See `.env.example` for the shape.

Fail-loud is deferred to the point of use: a key that stays None means "not
configured", and the skill that needs it decides whether that is fatal (Apollo
enrichment) or skippable (manual export). Reading config is not itself an error.
"""

import os
from dataclasses import dataclass, fields
from pathlib import Path

ENV_PREFIX = "BD_"


def load_dotenv(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict. Blank lines and # comments are ignored.

    Deliberately tiny — KEY=VALUE only, with optional `export ` and surrounding
    quotes stripped. No interpolation, no multiline. If a connector ever needs
    more, reach for python-dotenv then, not now.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip().removeprefix("export ").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("\"'")
    return values


@dataclass(frozen=True)
class Config:
    """External-API secrets. None means "not configured"."""

    apollo_api_key: str | None = None
    apify_api_token: str | None = None

    @classmethod
    def load(cls, root: Path | None = None) -> "Config":
        """Build Config from the environment, backfilled by a .env at repo root."""
        dotenv = load_dotenv((root or Path.cwd()) / ".env")
        kwargs = {}
        for f in fields(cls):
            env_name = ENV_PREFIX + f.name.upper()
            kwargs[f.name] = os.environ.get(env_name) or dotenv.get(env_name) or None
        return cls(**kwargs)

    def require(self, field_name: str) -> str:
        """Return a key's value or fail loud if it is not configured."""
        value = getattr(self, field_name)
        if not value:
            env_name = ENV_PREFIX + field_name.upper()
            raise RuntimeError(f"{env_name} is not set — add it to .env or the environment (see .env.example)")
        return value
