import importlib

import pytest

import config


@pytest.fixture
def reload_config(monkeypatch):
    """環境変数を変えて config を読み直し、終わったら元に戻す。"""
    yield lambda: importlib.reload(config)
    monkeypatch.undo()
    importlib.reload(config)


def test_workspace_from_env(reload_config, monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_WORKSPACE", str(tmp_path))
    cfg = reload_config()
    assert cfg.WORKSPACE_DIR == tmp_path.resolve()


def test_workspace_default_is_sibling_dir(reload_config, monkeypatch, tmp_path):
    monkeypatch.delenv("AGENT_WORKSPACE", raising=False)
    project = tmp_path / "localAgent"
    project.mkdir()
    monkeypatch.chdir(project)
    cfg = reload_config()
    assert cfg.WORKSPACE_DIR == (tmp_path / "workspace").resolve()


def test_tools_and_git_share_one_root(reload_config, monkeypatch, tmp_path):
    # ツール(SAFE_DIR)と git_guard(WORKSPACE_DIR)が別の場所を見ないこと
    monkeypatch.setenv("AGENT_WORKSPACE", str(tmp_path))
    cfg = reload_config()
    assert cfg.SAFE_DIR == cfg.WORKSPACE_DIR
