"""Tests for setup-token command."""

import base64
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner
from signate_deploy.cli import main


@pytest.fixture
def signate_installed(monkeypatch):
    """Pretend the `signate` package is importable.

    setup-token guards on `import signate`, but signate is deliberately not
    a dependency of this package (we shell out to its CLI). Without this
    stub the tests below only pass on a machine that happens to have signate
    installed -- CI does not, so they exited 1 before reaching the logic
    under test.
    """
    monkeypatch.setitem(sys.modules, "signate", types.ModuleType("signate"))


def _make_token_file(tmp_path):
    signate_dir = tmp_path / ".signate"
    signate_dir.mkdir()
    token_data = {"token": "dummy-token-value"}
    token_file = signate_dir / "signate.json"
    token_file.write_text(json.dumps(token_data))
    return token_file


def test_setup_token_success(tmp_path, monkeypatch, signate_installed):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_token_file(tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=True):
        runner = CliRunner()
        result = runner.invoke(main, ["setup-token", "--email=test@example.com"])

    assert result.exit_code == 0
    assert "Base64" in result.output


def test_setup_token_with_set_secret(tmp_path, monkeypatch, signate_installed):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_token_file(tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=True), \
         patch("signate_deploy.commands.setup_token._set_github_secret", return_value=True):
        runner = CliRunner()
        result = runner.invoke(main, ["setup-token", "--email=test@example.com", "--set-secret"])

    assert result.exit_code == 0
    assert "SIGNATE_TOKEN_B64" in result.output


def test_setup_token_fails_if_signate_token_fails(tmp_path, monkeypatch, signate_installed):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=False):
        runner = CliRunner()
        result = runner.invoke(main, ["setup-token", "--email=test@example.com"])

    assert result.exit_code != 0


def test_setup_token_fails_if_no_token_file(tmp_path, monkeypatch, signate_installed):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=True):
        runner = CliRunner()
        result = runner.invoke(main, ["setup-token", "--email=test@example.com"])

    assert result.exit_code != 0


def test_setup_token_fails_if_signate_not_installed(tmp_path, monkeypatch):
    """The import guard itself: no signate package -> exit 1, with the hint."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setitem(sys.modules, "signate", None)  # import raises ImportError

    runner = CliRunner()
    result = runner.invoke(main, ["setup-token", "--email=test@example.com"])

    assert result.exit_code != 0
    assert "pip install signate" in result.output
