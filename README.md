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

### 3. Set SIGNATE token as GitHub Secret

```bash
python -m signate_deploy setup-token --email=your@email.com --set-secret
```

This command will:
1. Run `signate token` interactively (you will be prompted for your password)
2. Base64-encode `~/.signate/signate.json`
3. Set it as `SIGNATE_TOKEN_B64` in GitHub Secrets automatically

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

## Links

- [PyPI](https://pypi.org/project/signate-deploy/)
- [Article (JP)](https://zenn.dev/shogaku/articles/signate-github-actions-cloud-ml)
- [Related: kaggle-notebook-deploy](https://github.com/yasumorishima/kaggle-notebook-deploy)
