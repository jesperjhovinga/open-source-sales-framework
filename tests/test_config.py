import pytest

from bdcore.config import Config, load_dotenv


def test_load_reads_real_environment_variables(monkeypatch, tmp_path):
    monkeypatch.setenv("BD_APOLLO_API_KEY", "live-key")
    monkeypatch.delenv("BD_APIFY_API_TOKEN", raising=False)
    config = Config.load(tmp_path)
    assert config.apollo_api_key == "live-key"
    assert config.apify_api_token is None


def test_env_file_backfills_but_never_overrides_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("BD_APOLLO_API_KEY", "from-env")
    monkeypatch.delenv("BD_APIFY_API_TOKEN", raising=False)
    (tmp_path / ".env").write_text("BD_APOLLO_API_KEY=from-file\nBD_APIFY_API_TOKEN=file-token\n", encoding="utf-8")

    config = Config.load(tmp_path)
    assert config.apollo_api_key == "from-env"  # exported var wins
    assert config.apify_api_token == "file-token"  # .env fills the gap


def test_missing_key_is_none_not_an_error(monkeypatch, tmp_path):
    monkeypatch.delenv("BD_APOLLO_API_KEY", raising=False)
    monkeypatch.delenv("BD_APIFY_API_TOKEN", raising=False)
    assert Config.load(tmp_path).apollo_api_key is None


def test_require_returns_a_configured_value():
    assert Config(apollo_api_key="k").require("apollo_api_key") == "k"


def test_require_fails_loud_on_a_missing_key():
    with pytest.raises(RuntimeError, match="BD_APOLLO_API_KEY is not set"):
        Config().require("apollo_api_key")


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("KEY=value", {"KEY": "value"}),
        ("export KEY=value", {"KEY": "value"}),
        ('KEY="quoted"', {"KEY": "quoted"}),
        ("KEY = spaced ", {"KEY": "spaced"}),
        ("# comment", {}),
        ("", {}),
        ("NOEQUALS", {}),
    ],
)
def test_load_dotenv_parsing(tmp_path, line, expected):
    (tmp_path / ".env").write_text(line + "\n", encoding="utf-8")
    assert load_dotenv(tmp_path / ".env") == expected


def test_load_dotenv_missing_file_is_empty(tmp_path):
    assert load_dotenv(tmp_path / ".env") == {}
