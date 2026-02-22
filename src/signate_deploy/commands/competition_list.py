"""signate-deploy competition-list: 参加可能なコンペティション一覧を表示する."""

import subprocess
import sys

import click

from signate_deploy.signate_cli import find_signate_exe


@click.command("competition-list")
def competition_list():
    """参加可能なコンペティション一覧を表示する.

    signate competition-list のラッパーコマンドです。
    PATHが通っていなくてもsignate CLIを自動検出して実行します。

    例:
      signate-deploy competition-list
    """
    signate_exe = find_signate_exe()
    if signate_exe is None:
        click.echo("Error: signate CLIが見つかりません。pip install signate を実行してください。", err=True)
        raise SystemExit(1)

    result = subprocess.run([signate_exe, "competition-list"])
    sys.exit(result.returncode)
