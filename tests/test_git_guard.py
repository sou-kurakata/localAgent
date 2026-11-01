import subprocess

import pytest

from git_guard import GitError, commit_all, finish_isolation, start_isolation


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """コミットが 1 つある main ブランチだけの git リポジトリ。"""
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "test")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "test@localhost")
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "calc.py").write_text("x = 1\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def current_branch(repo):
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def test_creates_isolated_branch(repo):
    state = start_isolation(repo, "fix average")
    assert state["base"] == "main"
    assert state["branch"].startswith("feature/agent-fix-average-")
    assert current_branch(repo) == state["branch"]


def test_refuses_non_git_directory(tmp_path):
    with pytest.raises(GitError):
        start_isolation(tmp_path, "task")


def test_refuses_dirty_working_tree(repo):
    (repo / "calc.py").write_text("x = 2\n", encoding="utf-8")
    with pytest.raises(GitError):
        start_isolation(repo, "task")
    assert current_branch(repo) == "main"


def test_commits_only_on_isolated_branch(repo):
    state = start_isolation(repo, "task")
    (repo / "calc.py").write_text("x = 2\n", encoding="utf-8")

    sha = commit_all(repo, "agent: task passed")
    finish_isolation(repo, state["base"])

    assert sha
    assert current_branch(repo) == "main"
    assert (repo / "calc.py").read_text(encoding="utf-8") == "x = 1\n"
    assert git(repo, "log", "-1", "--format=%s", state["branch"]) == "agent: task passed"


def test_skips_empty_commit(repo):
    start_isolation(repo, "task")
    assert commit_all(repo, "nothing changed") == ""
