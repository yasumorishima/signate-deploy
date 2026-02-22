"""Tests for init command."""

import json

import pytest
from click.testing import CliRunner
from signate_deploy.cli import main


def test_init_creates_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init", "my-comp", "--task-key", "abc123"])
    assert result.exit_code == 0
    assert (tmp_path / "my-comp").is_dir()


def test_init_creates_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, [
        "init", "my-comp",
        "--task-key", "abc123",
        "--file-key", "train:key1",
        "--file-key", "test:key2",
    ])
    assert result.exit_code == 0
    config = json.loads((tmp_path / "my-comp" / "signate-config.json").read_text())
    assert config["task_key"] == "abc123"
    assert config["file_keys"]["train"] == "key1"
    assert config["file_keys"]["test"] == "key2"


def test_init_creates_train_py(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init", "my-comp", "--task-key", "abc123"])
    assert result.exit_code == 0
    assert (tmp_path / "my-comp" / "train.py").exists()


def test_init_creates_requirements(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init", "my-comp", "--task-key", "abc123"])
    assert result.exit_code == 0
    assert (tmp_path / "my-comp" / "requirements.txt").exists()


def test_init_fails_if_dir_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "my-comp").mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["init", "my-comp", "--task-key", "abc123"])
    assert result.exit_code != 0


def test_init_invalid_file_key_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init", "my-comp", "--task-key", "abc123", "--file-key", "invalid"])
    assert result.exit_code != 0


def test_init_requires_task_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init", "my-comp"])
    assert result.exit_code != 0
