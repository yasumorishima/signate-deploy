"""Tests for init-repo command."""

import pytest
from click.testing import CliRunner
from signate_deploy.cli import main


def test_init_repo_creates_workflows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init-repo"])
    assert result.exit_code == 0
    assert (tmp_path / ".github" / "workflows" / "signate-submit.yml").exists()
    assert (tmp_path / ".github" / "workflows" / "signate-download.yml").exists()


def test_init_repo_creates_gitignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init-repo"])
    assert result.exit_code == 0
    assert (tmp_path / ".gitignore").exists()
    content = (tmp_path / ".gitignore").read_text()
    assert "signate-deploy" in content


def test_init_repo_appends_to_existing_gitignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    runner = CliRunner()
    result = runner.invoke(main, ["init-repo"])
    assert result.exit_code == 0
    content = (tmp_path / ".gitignore").read_text()
    assert "*.pyc" in content
    assert "signate-deploy" in content


def test_init_repo_skip_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["init-repo"])
    result = runner.invoke(main, ["init-repo"])
    assert result.exit_code == 0
    assert "Skip" in result.output


def test_init_repo_force_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["init-repo"])
    result = runner.invoke(main, ["init-repo", "--force"])
    assert result.exit_code == 0
    assert "Skip" not in result.output
