import re
import subprocess
from pathlib import Path
from datetime import datetime


class GitError(Exception):
    pass


def _git(args, cwd, check=True):
    """workspace内でgitを実行。capture_outputで標準出力を返す。
    push/pull/fetch/remoteは意図的にこのモジュールから呼ばない（ネット遮断）。"""
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",   # Windowsのcp932事故を防ぐ（M1で踏んだやつ）
    )
    if check and r.returncode != 0:
        raise GitError(f"git {' '.join(args)} 失敗:\n{r.stderr.strip()}")
    return r.stdout.strip()


def ensure_repo(workspace: Path):
    """gitリポジトリであることを確認。無ければ止める（勝手にinitしない）。"""
    if _git(["rev-parse", "--is-inside-work-tree"], workspace, check=False) != "true":
        raise GitError(f"{workspace} はgitリポジトリではありません。")


def working_tree_clean(workspace: Path) -> bool:
    return _git(["status", "--porcelain"], workspace) == ""


def _slugify(task_slug: str) -> str:
    """ブランチ名に使える文字だけ残す。"""
    s = re.sub(r"[^A-Za-z0-9._-]", "-", task_slug).strip("-")
    return s or "task"


def start_isolation(workspace: Path, task_slug: str) -> dict:
    """隔離ブランチを作ってcheckout。元ブランチを記録して返す。"""
    ensure_repo(workspace)
    if not working_tree_clean(workspace):
        raise GitError("作業ツリーが汚れています。commit/stashしてから夜間runを回してください。")
    base = _git(["rev-parse", "--abbrev-ref", "HEAD"], workspace)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = f"feature/agent-{_slugify(task_slug)}-{ts}"
    _git(["checkout", "-b", branch], workspace)
    return {"base": base, "branch": branch}


def commit_all(workspace: Path, message: str) -> str:
    """緑の成果を隔離ブランチにコミット。変更なしなら空コミットを避ける。"""
    _git(["add", "-A"], workspace)
    if working_tree_clean(workspace):
        return ""   # まだ①昇格が無いうちは、ここが空になるのは正常
    _git(["commit", "-m", message], workspace)
    return _git(["rev-parse", "HEAD"], workspace)


def finish_isolation(workspace: Path, base_branch: str):
    """runの終わり。元ブランチに戻すだけ。merge/delete/pushは人間の朝レビューに委ねる。"""
    _git(["checkout", base_branch], workspace)