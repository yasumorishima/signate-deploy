"""Tests for setup-token command."""

import base64
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner
from signate_deploy.cli import main


def _make_token_file(tmp_path):
    signate_dir = tmp_path / ".signate"
    signate_dir.mkdir()
    token_data = {"token": "dummy-token-value"}
    token_file = signate_dir / "signate.json"
    token_file.write_text(json.dumps(token_data))
    return token_file


def test_setup_token_success(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_token_file(tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=True):
        runner = CliRunner()
        result = runner.invoke(main, [
            "setup-token",
            "--email=test@example.com",
            "--password=pass",
        ])

    assert result.exit_code == 0
    assert "Base64" in result.output


def test_setup_token_with_set_secret(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_token_file(tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=True), \
         patch("signate_deploy.commands.setup_token._set_github_secret", return_value=True):
        runner = CliRunner()
        result = runner.invoke(main, [
            "setup-token",
            "--email=test@example.com",
            "--password=pass",
            "--set-secret",
        ])

    assert result.exit_code == 0
    assert "SIGNATE_TOKEN_B64" in result.output


def test_setup_token_fails_if_signate_token_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=False):
        runner = CliRunner()
        result = runner.invoke(main, [
            "setup-token",
            "--email=test@example.com",
            "--password=pass",
        ])

    assert result.exit_code != 0


def test_setup_token_fails_if_no_token_file(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with patch("signate_deploy.commands.setup_token._run_signate_token", return_value=True):
        runner = CliRunner()
        result = runner.invoke(main, [
            "setup-token",
            "--email=test@example.com",
            "--password=pass",
        ])

    assert result.exit_code != 0
