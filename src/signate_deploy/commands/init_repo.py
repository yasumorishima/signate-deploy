"""signate-deploy init-repo: リポジトリにGitHub Actionsワークフローをセットアップする."""

from pathlib import Path

import click


REFRESH_TOKEN_SCRIPT = """\
\"\"\"SIGNATE APIトークンをメール/パスワードで自動取得してsignate.jsonに保存する.\"\"\"

import os
import sys
from pathlib import Path

import requests

CLOUD_URL = "https://api.cloud.signate.jp/api"
JWT_COOKIE_KEY = "cloud_user"
CSRF_COOKIE_KEY = "_user_csrf_cloud"


def refresh_token(email: str, password: str) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": "python-requests/2.x"})

    # 1. CSRFトークン取得
    session.get(f"{CLOUD_URL}/v1/token").raise_for_status()
    csrf = next(c.value for c in session.cookies if c.name == CSRF_COOKIE_KEY)

    # 2. サインイン
    session.post(
        f"{CLOUD_URL}/v1/sign_in",
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
        json={"email": email, "password": password, "individual": True},
    ).raise_for_status()

    # 3. 組織ログイン
    session.post(
        f"{CLOUD_URL}/v1/organizations/sign_in",
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
        json={"id": 1},
    ).raise_for_status()

    # 4. JWT取得・保存
    jwt = next(c.value for c in session.cookies if c.name == JWT_COOKIE_KEY)
    token_path = Path.home() / ".signate" / "signate.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(jwt)
    print("SIGNATE token refreshed successfully.")


if __name__ == "__main__":
    email = os.environ.get("SIGNATE_EMAIL")
    password = os.environ.get("SIGNATE_PASSWORD")
    if not email or not password:
        print("Error: SIGNATE_EMAIL and SIGNATE_PASSWORD must be set.", file=sys.stderr)
        sys.exit(1)
    refresh_token(email, password)
"""

SUBMIT_WORKFLOW = """\
name: SIGNATE Train & Submit

on:
  workflow_dispatch:
    inputs:
      competition_dir:
        description: "Competition directory name"
        required: true
        type: string
      memo:
        description: "Submission memo"
        required: false
        default: "GitHub Actions submission"

jobs:
  submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install signate requests
          if [ -f "${{ inputs.competition_dir }}/requirements.txt" ]; then
            pip install -r "${{ inputs.competition_dir }}/requirements.txt"
          else
            pip install pandas numpy scikit-learn lightgbm
          fi

      - name: Refresh SIGNATE token
        env:
          SIGNATE_EMAIL: ${{ secrets.SIGNATE_EMAIL }}
          SIGNATE_PASSWORD: ${{ secrets.SIGNATE_PASSWORD }}
        run: python scripts/refresh_signate_token.py

      - name: Download data
        run: |
          python - <<'EOF'
          import json, subprocess, os
          config = json.load(open("${{ inputs.competition_dir }}/signate-config.json"))
          task_key = config["task_key"]
          os.makedirs("${{ inputs.competition_dir }}/data", exist_ok=True)
          os.chdir("${{ inputs.competition_dir }}/data")
          for file_key in config.get("file_keys", {}).values():
              subprocess.run(
                  ["signate", "download", "--task_key", task_key, "--file_key", file_key],
                  check=True,
              )
          EOF

      - name: Train and predict
        env:
          WANDB_API_KEY: ${{ secrets.WANDB_API_KEY }}
        run: python "${{ inputs.competition_dir }}/train.py"

      - name: Submit
        run: |
          python - <<'EOF'
          import json, subprocess
          config = json.load(open("${{ inputs.competition_dir }}/signate-config.json"))
          subprocess.run([
              "signate", "submit",
              "${{ inputs.competition_dir }}/submission.csv",
              "--task_key", config["task_key"],
              "--memo", "${{ inputs.memo }}",
          ], check=True)
          EOF

      - name: Upload submission as artifact
        uses: actions/upload-artifact@v4
        with:
          name: submission-${{ github.run_number }}
          path: ${{ inputs.competition_dir }}/submission.csv
          retention-days: 90
"""

DOWNLOAD_WORKFLOW = """\
name: SIGNATE Download Data

on:
  workflow_dispatch:
    inputs:
      competition_dir:
        description: "Competition directory name"
        required: true
        type: string

jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install signate
        run: pip install signate requests

      - name: Refresh SIGNATE token
        env:
          SIGNATE_EMAIL: ${{ secrets.SIGNATE_EMAIL }}
          SIGNATE_PASSWORD: ${{ secrets.SIGNATE_PASSWORD }}
        run: python scripts/refresh_signate_token.py

      - name: Download data
        run: |
          python - <<'EOF'
          import json, subprocess, os
          config = json.load(open("${{ inputs.competition_dir }}/signate-config.json"))
          task_key = config["task_key"]
          os.makedirs("${{ inputs.competition_dir }}/data", exist_ok=True)
          os.chdir("${{ inputs.competition_dir }}/data")
          for name, file_key in config.get("file_keys", {}).items():
              print(f"Downloading {name}...")
              subprocess.run(
                  ["signate", "download", "--task_key", task_key, "--file_key", file_key],
                  check=True,
              )
          EOF

      - name: Upload data as artifact
        uses: actions/upload-artifact@v4
        with:
          name: signate-data-${{ inputs.competition_dir }}
          path: ${{ inputs.competition_dir }}/data/
          retention-days: 90
"""

GITIGNORE_ADDITIONS = """\
# === signate-deploy ===
# Data files
data/
*.csv
*.zip

# Credentials (NEVER commit these)
.signate/
signate.json

# Virtual environments
.venv/
venv/
"""


@click.command("init-repo")
@click.option("--force", "-f", is_flag=True, default=False, help="既存ファイルを上書きする")
def init_repo(force):
    """リポジトリにGitHub Actionsワークフローと.gitignoreをセットアップする.

    カレントディレクトリに以下を生成します:
    - .github/workflows/signate-submit.yml
    - .github/workflows/signate-download.yml
    - scripts/refresh_signate_token.py
    - .gitignore への追記
    """
    created = []

    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in [
        ("signate-submit.yml", SUBMIT_WORKFLOW),
        ("signate-download.yml", DOWNLOAD_WORKFLOW),
    ]:
        path = workflow_dir / filename
        if path.exists() and not force:
            click.echo(f"  Skip: {path} (既に存在。--force で上書き)")
        else:
            path.write_text(content)
            created.append(str(path))
            click.echo(f"  Created: {path}")

    # refresh_signate_token.py
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    refresh_script_path = scripts_dir / "refresh_signate_token.py"
    if refresh_script_path.exists() and not force:
        click.echo(f"  Skip: {refresh_script_path} (既に存在。--force で上書き)")
    else:
        refresh_script_path.write_text(REFRESH_TOKEN_SCRIPT)
        created.append(str(refresh_script_path))
        click.echo(f"  Created: {refresh_script_path}")

    # .gitignore
    gitignore_path = Path(".gitignore")
    marker = "# === signate-deploy ==="
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if marker in existing and not force:
            click.echo(f"  Skip: {gitignore_path} (signate-deployセクション追加済み)")
        else:
            if marker not in existing:
                with open(gitignore_path, "a") as f:
                    f.write("\n" + GITIGNORE_ADDITIONS)
                created.append(f"{gitignore_path} (追記)")
                click.echo(f"  Updated: {gitignore_path}")
    else:
        gitignore_path.write_text(GITIGNORE_ADDITIONS)
        created.append(str(gitignore_path))
        click.echo(f"  Created: {gitignore_path}")

    click.echo("")
    if created:
        click.echo(f"{len(created)}個のファイルをセットアップしました。")
    else:
        click.echo("全てのファイルが既に存在しています。")

    click.echo("")
    click.echo("次のステップ:")
    click.echo("  1. GitHub Secretsを設定（リポのディレクトリ内で実行）:")
    click.echo("     gh secret set SIGNATE_EMAIL --body your@email.com")
    click.echo("     gh secret set SIGNATE_PASSWORD  # プロンプトで入力")
    click.echo("     gh secret set WANDB_API_KEY     # W&Bを使う場合")
    click.echo("  2. コンペ用ディレクトリを作成:")
    click.echo("     python -m signate_deploy init <competition-dir> --task-key <task_key>")
