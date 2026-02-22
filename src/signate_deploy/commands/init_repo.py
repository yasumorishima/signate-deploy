"""signate-deploy init-repo: リポジトリにGitHub Actionsワークフローをセットアップする."""

from pathlib import Path

import click


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

      - name: Setup SIGNATE token
        run: |
          mkdir -p ~/.signate
          echo '${{ secrets.SIGNATE_TOKEN_B64 }}' | base64 -d > ~/.signate/signate.json

      - name: Install dependencies
        run: |
          pip install signate
          if [ -f "${{ inputs.competition_dir }}/requirements.txt" ]; then
            pip install -r "${{ inputs.competition_dir }}/requirements.txt"
          else
            pip install pandas numpy scikit-learn lightgbm
          fi

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

      - name: Setup SIGNATE token
        run: |
          mkdir -p ~/.signate
          echo '${{ secrets.SIGNATE_TOKEN_B64 }}' | base64 -d > ~/.signate/signate.json

      - name: Install signate
        run: pip install signate

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
    click.echo("  1. GitHub Secretsを設定:")
    click.echo("     signate token --email=your@email.com --password=your-password")
    click.echo("     cat ~/.signate/signate.json | base64 | gh secret set SIGNATE_TOKEN_B64")
    click.echo("  2. コンペ用ディレクトリを作成:")
    click.echo("     signate-deploy init <competition-dir> --task-key <task_key>")
