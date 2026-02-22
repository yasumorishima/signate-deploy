"""signate-deploy file-list: タスクのファイル一覧を表示する."""

import subprocess
import sys

import click

from signate_deploy.signate_cli import find_signate_exe


@click.command("file-list")
@click.argument("task_key")
def file_list(task_key):
    """タスクのファイル一覧を表示する（file_keyを確認できる）.

    TASK_KEY は task-list コマンドで確認できます。

    例:
      signate-deploy file-list <task_key>
    """
    signate_exe = find_signate_exe()
    if signate_exe is None:
        click.echo("Error: signate CLIが見つかりません。pip install signate を実行してください。", err=True)
        raise SystemExit(1)

    result = subprocess.run([signate_exe, "file-list", "--task_key", task_key])
    sys.exit(result.returncode)
