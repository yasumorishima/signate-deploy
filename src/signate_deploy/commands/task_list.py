"""signate-deploy task-list: コンペティションのタスク一覧を表示する."""

import subprocess
import sys

import click

from signate_deploy.signate_cli import find_signate_exe


@click.command("task-list")
@click.argument("competition_key")
def task_list(competition_key):
    """コンペティションのタスク一覧を表示する（task_keyを確認できる）.

    COMPETITION_KEY はコンペティションURLの competition= パラメータの値です。

    例:
      signate-deploy task-list <competition_key>
    """
    signate_exe = find_signate_exe()
    if signate_exe is None:
        click.echo("Error: signate CLIが見つかりません。pip install signate を実行してください。", err=True)
        raise SystemExit(1)

    result = subprocess.run([signate_exe, "task-list", "--competition_key", competition_key])
    sys.exit(result.returncode)
