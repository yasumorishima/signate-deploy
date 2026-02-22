"""signate CLIの実行ファイルを探すユーティリティ."""

import shutil
import site
import sys
from pathlib import Path


def find_signate_exe() -> str | None:
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
