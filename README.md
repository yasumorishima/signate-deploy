# signate-deploy

A CLI tool to automate SIGNATE competition workflows via GitHub Actions.

`git push` → GitHub Actions → Download data → Train → Submit to SIGNATE

```
signate-deploy init-repo          # Set up GitHub Actions workflows
signate-deploy init my-comp \
  --task-key <task_key> \
  --file-key train:<key> \
  --file-key test:<key>            # Create competition directory
signate-deploy submit my-comp \
  --memo "Baseline v1"             # Trigger train & submit
signate-deploy download my-comp   # Trigger data download only
```

## Installation

```bash
pip install signate-deploy
```

## Quick Start

### 1. Set up GitHub Actions

In your GitHub repository root:

```bash
signate-deploy init-repo
```

Creates:
- `.github/workflows/signate-submit.yml` — full pipeline (download → train → submit)
- `.github/workflows/signate-download.yml` — data download only

### 2. Set up GitHub Secrets

```bash
# Generate SIGNATE token
signate token --email=your@email.com --password=your-password

# Set as GitHub Secret (Base64 encoded)
cat ~/.signate/signate.json | base64 | gh secret set SIGNATE_TOKEN_B64
```

### 3. Get task_key and file_keys

```bash
pip install signate
signate file-list --task_key <task_key>
```

`task_key` is in the competition URL:
```
https://user.competition.signate.jp/.../detail/?...&task=THIS_IS_TASK_KEY
```

### 4. Create competition directory

```bash
signate-deploy init my-comp \
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

### 5. Edit train.py and push

```bash
# Edit my-comp/train.py (set TARGET column name, add preprocessing, etc.)
git add my-comp/ && git commit -m "Add my-comp baseline" && git push
```

### 6. Submit

```bash
signate-deploy submit my-comp --memo "Baseline v1"
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

- `⚠️ Never commit `data/` or `.signate/` — they are .gitignored by `init-repo`
- Requires [GitHub CLI (`gh`)](https://cli.github.com/) to be installed and authenticated
- Works on any OS (Windows/Mac/Linux)

## Links

- [PyPI](https://pypi.org/project/signate-deploy/)
- [Article (JP)](https://zenn.dev/shogaku/articles/signate-github-actions-cloud-ml)
- [Related: kaggle-notebook-deploy](https://github.com/yasumorishima/kaggle-notebook-deploy)
