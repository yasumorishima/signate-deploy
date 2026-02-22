"""signate-deploy download: GitHub Actions経由でデータをダウンロードする."""

import subprocess
from pathlib import Path

import click


@click.command("download")
@click.argument("competition_dir")
def download(competition_dir):
    """GitHub Actions経由でSIGNATEからデータをダウンロードする.

    COMPETITION_DIR 内の signate-config.json を使い、
    GitHub Actions の signate-download.yml を起動します。

    例:
      signate-deploy download my-comp
    """
    config_path = Path(competition_dir) / "signate-config.json"
    if not config_path.exists():
        click.echo(f"Error: {config_path} が見つかりません。", err=True)
        click.echo("signate-deploy init でディレクトリを作成してください。", err=True)
        raise SystemExit(1)

    click.echo(f"Triggering download workflow for '{competition_dir}'...")

    result = subprocess.run(
        [
            "gh", "workflow", "run", "signate-download.yml",
            "-f", f"competition_dir={competition_dir}",
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
    click.echo("Artifact取得: gh run download <run_id> --dir data/")
