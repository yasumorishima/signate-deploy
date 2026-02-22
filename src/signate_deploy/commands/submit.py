"""signate-deploy submit: GitHub Actions経由でSIGNATEに提出する."""

import subprocess
from pathlib import Path

import click


@click.command("submit")
@click.argument("competition_dir")
@click.option("--memo", "-m", default="GitHub Actions submission", help="提出メモ")
def submit(competition_dir, memo):
    """GitHub Actions経由でSIGNATEに提出する.

    COMPETITION_DIR 内の signate-config.json を使い、
    GitHub Actions の signate-submit.yml を起動します。

    例:
      signate-deploy submit my-comp
      signate-deploy submit my-comp --memo "LightGBM baseline v1"
    """
    config_path = Path(competition_dir) / "signate-config.json"
    if not config_path.exists():
        click.echo(f"Error: {config_path} が見つかりません。", err=True)
        click.echo("signate-deploy init でディレクトリを作成してください。", err=True)
        raise SystemExit(1)

    click.echo(f"Triggering submit workflow for '{competition_dir}'...")
    click.echo(f"  Memo: {memo}")

    result = subprocess.run(
        [
            "gh", "workflow", "run", "signate-submit.yml",
            "-f", f"competition_dir={competition_dir}",
            "-f", f"memo={memo}",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        click.echo("Error: gh workflow run に失敗しました。", err=True)
        click.echo(result.stderr, err=True)
        raise SystemExit(1)

    click.echo("")
    click.echo("Workflow を起動しました。")
    click.echo("進捗確認: gh run list --limit 1")
    click.echo("ログ確認:  gh run view --log")
