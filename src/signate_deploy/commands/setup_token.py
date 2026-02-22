"""signate-deploy setup-token: SIGNATEトークンを取得してGitHub Secretsに設定する."""

import base64
import json
import shutil
import site
import subprocess
import sys
from pathlib import Path

import click


def _find_signate_exe() -> str | None:
    """signate CLIの実行ファイルを探す."""
    # 1. PATHが通っていれば即返す
    found = shutil.which("signate")
    if found:
        return found

    # 2. pip install --user 先のScriptsを探す（Windows Store Python等）
    try:
        user_scripts = Path(site.getusersitepackages()).parent / "Scripts"
        for name in ["signate.exe", "signate"]:
            candidate = user_scripts / name
            if candidate.exists():
                return str(candidate)
    except Exception:
        pass

    # 3. sys.executable と同階層のScriptsを探す
    for scripts in [
        Path(sys.executable).parent / "Scripts",
        Path(sys.executable).parent,
    ]:
        for name in ["signate.exe", "signate"]:
            candidate = scripts / name
            if candidate.exists():
                return str(candidate)

    return None


def _run_signate_token(email: str, password: str) -> bool:
    """signate token コマンドを実行してトークンを取得する."""
    signate_exe = _find_signate_exe()
    if signate_exe is None:
        click.echo("Error: signate CLIが見つかりません。pip install signate を実行してください。", err=True)
        return False

    result = subprocess.run(
        [signate_exe, "token", f"--email={email}", f"--password={password}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo("Error: SIGNATEトークンの取得に失敗しました。", err=True)
        click.echo(result.stderr or result.stdout, err=True)
        return False
    return True


def _read_token_b64() -> str | None:
    """~/.signate/signate.json を読み込んでBase64エンコードする."""
    token_path = Path.home() / ".signate" / "signate.json"
    if not token_path.exists():
        click.echo(f"Error: {token_path} が見つかりません。", err=True)
        return None
    content = token_path.read_bytes()
    if not content.strip():
        click.echo("Error: signate.json が空です。", err=True)
        return None
    return base64.b64encode(content).decode("ascii")


def _set_github_secret(secret_value: str) -> bool:
    """gh secret set SIGNATE_TOKEN_B64 を実行する."""
    result = subprocess.run(
        ["gh", "secret", "set", "SIGNATE_TOKEN_B64", "--body", secret_value],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo("Error: gh secret set に失敗しました。", err=True)
        click.echo(result.stderr, err=True)
        return False
    return True


@click.command("setup-token")
@click.option("--email", required=True, prompt="SIGNATE email", help="SIGNATEのメールアドレス")
@click.option("--password", required=True, prompt="SIGNATE password", hide_input=True, help="SIGNATEのパスワード")
@click.option("--set-secret", is_flag=True, default=False, help="GitHub Secretsに自動設定する")
def setup_token(email, password, set_secret):
    """SIGNATEトークンを取得してBase64エンコードする.

    --set-secret を付けるとGitHub Secretsにも自動設定します。

    例:
      signate-deploy setup-token --email=your@email.com --password=your-password
      signate-deploy setup-token --email=your@email.com --password=your-password --set-secret
    """
    # signate パッケージの確認
    try:
        import signate  # noqa: F401
    except ImportError:
        click.echo("Error: signateパッケージがインストールされていません。", err=True)
        click.echo("  pip install signate", err=True)
        raise SystemExit(1)

    # トークン取得
    click.echo("SIGNATEトークンを取得中...")
    if not _run_signate_token(email, password):
        raise SystemExit(1)
    click.echo("  トークン取得成功")

    # Base64エンコード
    token_b64 = _read_token_b64()
    if token_b64 is None:
        raise SystemExit(1)
    click.echo("  Base64エンコード完了")

    if set_secret:
        # GitHub Secretsに設定
        click.echo("GitHub Secretsに設定中...")
        if not _set_github_secret(token_b64):
            raise SystemExit(1)
        click.echo("  SIGNATE_TOKEN_B64 を設定しました")
        click.echo("")
        click.echo("完了！次のステップ:")
        click.echo("  signate-deploy init <competition-dir> --task-key <task_key>")
    else:
        click.echo("")
        click.echo("Base64エンコード済みトークン（GitHub Secretsに設定してください）:")
        click.echo(f"  gh secret set SIGNATE_TOKEN_B64 --body '{token_b64}'")
        click.echo("")
        click.echo("または --set-secret オプションで自動設定:")
        click.echo(f"  signate-deploy setup-token --email={email} --password=*** --set-secret")
