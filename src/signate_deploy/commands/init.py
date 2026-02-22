"""signate-deploy init: コンペ用ディレクトリを雛形から生成する."""

import json
from pathlib import Path

import click


CONFIG_TEMPLATE = {
    "task_key": "",
    "file_keys": {},
}

TRAIN_TEMPLATE = """\
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

DATA_DIR = "{competition_dir}/data"
TARGET = "target"  # ターゲット列名に変更してください


def main():
    train = pd.read_csv(f"{{DATA_DIR}}/train.csv")
    test = pd.read_csv(f"{{DATA_DIR}}/test.csv")

    features = [c for c in train.columns if c not in ["id", TARGET]]
    X, y = train[features], train[TARGET]
    X_test = test[features]

    params = {{
        "objective": "binary",
        "metric": "auc",
        "verbosity": -1,
        "n_estimators": 1000,
        "learning_rate": 0.05,
        "random_state": 42,
    }}

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(X))
    test_preds = np.zeros(len(X_test))

    for fold, (tr_idx, val_idx) in enumerate(skf.split(X, y)):
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X.iloc[tr_idx], y.iloc[tr_idx],
            eval_set=[(X.iloc[val_idx], y.iloc[val_idx])],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
        )
        oof_preds[val_idx] = model.predict_proba(X.iloc[val_idx])[:, 1]
        test_preds += model.predict_proba(X_test)[:, 1] / 5
        print(f"Fold {{fold + 1}}: AUC = {{roc_auc_score(y.iloc[val_idx], oof_preds[val_idx]):.5f}}")

    print(f"Overall OOF AUC: {{roc_auc_score(y, oof_preds):.5f}}")

    submission = pd.DataFrame({{"id": test["id"], "pred": test_preds}})
    submission.to_csv(f"{{DATA_DIR}}/../submission.csv", index=False, header=False)
    print(f"Saved: submission.csv ({{len(submission)}} rows)")


if __name__ == "__main__":
    main()
"""

REQUIREMENTS_TEMPLATE = """\
pandas
numpy
scikit-learn
lightgbm
"""


@click.command("init")
@click.argument("competition_dir")
@click.option("--task-key", required=True, help="SIGNATEのtask_key（コンペURLから取得）")
@click.option(
    "--file-key",
    multiple=True,
    metavar="NAME:KEY",
    help="ファイルキー（例: --file-key train:abc123 --file-key test:def456）",
)
def init(competition_dir, task_key, file_key):
    """コンペ用ディレクトリを雛形から生成する.

    COMPETITION_DIR はローカルのディレクトリ名です。

    例:
      signate-deploy init my-comp --task-key abc123
      signate-deploy init my-comp --task-key abc123 --file-key train:key1 --file-key test:key2
    """
    dir_path = Path(competition_dir)
    if dir_path.exists():
        click.echo(f"Error: ディレクトリ '{competition_dir}' は既に存在します。", err=True)
        raise SystemExit(1)

    dir_path.mkdir(parents=True)

    # file_keys をパース
    file_keys = {}
    for fk in file_key:
        if ":" not in fk:
            click.echo(f"Error: --file-key の形式が不正です（NAME:KEY 形式で指定してください）: {fk}", err=True)
            raise SystemExit(1)
        name, key = fk.split(":", 1)
        file_keys[name] = key

    # signate-config.json
    config = CONFIG_TEMPLATE.copy()
    config["task_key"] = task_key
    config["file_keys"] = file_keys

    config_path = dir_path / "signate-config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")
    click.echo(f"  Created: {config_path}")

    # train.py
    train_path = dir_path / "train.py"
    train_path.write_text(TRAIN_TEMPLATE.format(competition_dir=competition_dir))
    click.echo(f"  Created: {train_path}")

    # requirements.txt
    req_path = dir_path / "requirements.txt"
    req_path.write_text(REQUIREMENTS_TEMPLATE)
    click.echo(f"  Created: {req_path}")

    click.echo("")
    click.echo(f"'{competition_dir}/' を作成しました。")
    click.echo("")
    click.echo("次のステップ:")
    click.echo(f"  1. {train_path} を編集（TARGET列名等を変更）")
    click.echo(f"  2. {config_path} のfile_keysを設定（まだなら）")
    click.echo(f"  3. git add {competition_dir}/ && git commit && git push")
    click.echo(f"  4. signate-deploy download {competition_dir}  # データDL確認")
    click.echo(f"  5. signate-deploy submit {competition_dir} --memo 'Baseline v1'")
