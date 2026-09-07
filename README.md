# signate-deploy

A CLI tool to automate SIGNATE competition workflows via GitHub Actions.

`git push` → GitHub Actions → Download data → Train → Submit to SIGNATE

```
signate-deploy init-repo              # Set up GitHub Actions workflows
signate-deploy setup-token            # Get SIGNATE token & set GitHub Secret
signate-deploy competition-list       # List available competitions
signate-deploy task-list <comp_key>   # Get task_key from competition
signate-deploy file-list <task_key>   # Get file_keys from task
signate-deploy init my-comp \
  --task-key <task_key> \
  --file-key train:<key> \
  --file-key test:<key>               # Create competition directory
signate-deploy submit my-comp \
  --memo "Baseline v1"               # Trigger train & submit
signate-deploy download my-comp      # Trigger data download only
```

## Installation

```bash
pip install signate-deploy
```

> **Prerequisites:** [GitHub CLI (`gh`)](https://cli.github.com/) must be installed and authenticated.

## Quick Start

### 1. Install signate CLI

```bash
pip install signate
```

> The signate CLI is required to fetch your API token and get file keys.
> It is a separate package from signate-deploy.

### 2. Set up GitHub Actions

In your GitHub repository root:

```bash
python -m signate_deploy init-repo
```

Creates:
- `.github/workflows/signate-submit.yml` — full pipeline (download → train → submit)
- `.github/workflows/signate-download.yml` — data download only
- `scripts/refresh_signate_token.py` — auto token refresh script

### 3. Set SIGNATE credentials as GitHub Secrets

Run **inside your repository directory**:

```bash
gh secret set SIGNATE_EMAIL --body your@email.com
gh secret set SIGNATE_PASSWORD   # prompted securely
gh secret set WANDB_API_KEY      # if using W&B experiment tracking
```

The generated `scripts/refresh_signate_token.py` is called at the start of every Actions run to obtain a fresh token automatically — no manual token refresh needed.

> **Windows (cmd.exe):** Use `python -m signate_deploy` instead of `signate-deploy`
> since the Scripts folder may not be on PATH.

### 4. Get task_key and file_keys

```bash
# Find your competition_key from the competition URL:
# https://user.competition.signate.jp/.../detail/?competition=THIS_IS_COMPETITION_KEY

# Get task_key from competition_key
python -m signate_deploy task-list <competition_key>

# Get file_keys from task_key
python -m signate_deploy file-list <task_key>
```

> You can also browse available competitions with `python -m signate_deploy competition-list`.

### 5. Create competition directory

```bash
python -m signate_deploy init my-comp \
  --task-key abc123def456 \
  --file-key train:5f0e1ebb35af4963 \
  --file-key test:72f23ebe8f004fa0 \
  --file-key sample_submit:ad3502af26b9
```

Creates:
```
my-comp/
  signate-config.json   # task_key and file_keys
  train.py              # LightGBM 5-fold CV template
  requirements.txt      # pandas, numpy, scikit-learn, lightgbm
```

### 6. Edit train.py and push

```bash
# Edit my-comp/train.py (set TARGET column name, add preprocessing, etc.)
git add my-comp/ && git commit -m "Add my-comp baseline" && git push
```

### 7. Submit

```bash
python -m signate_deploy submit my-comp --memo "Baseline v1"
# → gh workflow run signate-submit.yml is triggered

# Check progress
gh run list --limit 1
gh run view --log
```

## signate-config.json

```json
{
  "task_key": "your_task_key",
  "file_keys": {
    "train": "file_key_for_train_csv",
    "test": "file_key_for_test_csv",
    "sample_submit": "file_key_for_sample_submit_csv"
  }
}
```

## Notes

- ⚠️ Never commit `data/` or `.signate/` — they are .gitignored by `init-repo`
- Requires [GitHub CLI (`gh`)](https://cli.github.com/) to be installed and authenticated
- Works on any OS (Windows/Mac/Linux)

## Commands

<!-- commands:start -->

### `signate-deploy competition-list`

参加可能なコンペティション一覧を表示する.

### `signate-deploy download`

GitHub Actions経由でSIGNATEからデータをダウンロードする.

```
signate-deploy download [COMPETITION_DIR] [OPTIONS]
```

### `signate-deploy file-list`

タスクのファイル一覧を表示する（file_keyを確認できる）.

```
signate-deploy file-list [TASK_KEY] [OPTIONS]
```

### `signate-deploy init`

コンペ用ディレクトリを雛形から生成する.

```
signate-deploy init [COMPETITION_DIR] [OPTIONS]
```

| Option | Description |
|---|---|
| `--task-key` | SIGNATEのtask_key（コンペURLから取得） (default: `Sentinel.UNSET`) |
| `--file-key` | ファイルキー（例: --file-key train:abc123 --file-key test:def456） (default: `Sentinel.UNSET`) |

### `signate-deploy init-repo`

リポジトリにGitHub Actionsワークフローと.gitignoreをセットアップする.

| Option | Description |
|---|---|
| `--force`, `-f` | 既存ファイルを上書きする |

### `signate-deploy setup-token`

SIGNATEトークンを取得してBase64エンコードする.

| Option | Description |
|---|---|
| `--email` | SIGNATEのメールアドレス (default: `Sentinel.UNSET`) |
| `--set-secret` | GitHub Secretsに自動設定する |

### `signate-deploy submit`

GitHub Actions経由でSIGNATEに提出する.

```
signate-deploy submit [COMPETITION_DIR] [OPTIONS]
```

| Option | Description |
|---|---|
| `--memo`, `-m` | 提出メモ (default: `GitHub Actions submission`) |

### `signate-deploy task-list`

コンペティションのタスク一覧を表示する（task_keyを確認できる）.

```
signate-deploy task-list [COMPETITION_KEY] [OPTIONS]
```

<!-- commands:end -->

## Links

- [PyPI](https://pypi.org/project/signate-deploy/)
- [Article (JP)](https://zenn.dev/shogaku/articles/signate-github-actions-cloud-ml)
- [Related: kaggle-notebook-deploy](https://github.com/yasumorishima/kaggle-notebook-deploy)
