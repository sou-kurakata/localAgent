import pytest

import tools.filesystem as filesystem
import tools.testing as testing


@pytest.fixture
def safe_dir(tmp_path, monkeypatch):
    """ツールの作業ルートを一時ディレクトリに差し替える。"""
    root = tmp_path / "workspace"
    root.mkdir()
    monkeypatch.setattr(filesystem, "SAFE_DIR", root)
    monkeypatch.setattr(testing, "SAFE_DIR", root)
    return root


class TestWriteCandidate:
    def test_writes_python_file(self, safe_dir):
        result = filesystem.write_candidate("calc.py", "x = 1\n")
        assert result.startswith("[OK]")
        assert (safe_dir / "calc.py").read_text(encoding="utf-8") == "x = 1\n"

    @pytest.mark.parametrize("filename", [
        "../escape.py",
        "sub/inner.py",
        r"sub\inner.py",
        "..",
    ])
    def test_rejects_path_traversal(self, safe_dir, filename):
        assert filesystem.write_candidate(filename, "x = 1").startswith("[Error]")
        assert not (safe_dir.parent / "escape.py").exists()

    @pytest.mark.parametrize("filename", ["run.bat", "notes.txt", "calc.py.sh"])
    def test_rejects_non_python_files(self, safe_dir, filename):
        assert filesystem.write_candidate(filename, "echo hi").startswith("[Error]")
        assert not (safe_dir / filename).exists()

    def test_cannot_overwrite_tests(self, safe_dir):
        # テストを書き換えて「通ったこと」にする自作自演を防ぐ
        original = "def test_x():\n    assert False\n"
        (safe_dir / "test_calc.py").write_text(original, encoding="utf-8")
        result = filesystem.write_candidate("test_calc.py", "def test_x():\n    pass\n")
        assert result.startswith("[Error]")
        assert (safe_dir / "test_calc.py").read_text(encoding="utf-8") == original


class TestReadFile:
    def test_reads_existing_file(self, safe_dir):
        (safe_dir / "calc.py").write_text("x = 1\n", encoding="utf-8")
        assert filesystem.read_file("calc.py") == "x = 1\n"

    def test_rejects_path_traversal(self, safe_dir):
        (safe_dir.parent / "secret.txt").write_text("secret", encoding="utf-8")
        assert filesystem.read_file("../secret.txt").startswith("[Error]")

    def test_missing_file(self, safe_dir):
        assert filesystem.read_file("nothing.py").startswith("[Error]")


class TestListDirectory:
    def test_lists_files_and_dirs(self, safe_dir):
        (safe_dir / "calc.py").write_text("", encoding="utf-8")
        (safe_dir / "pkg").mkdir()
        assert filesystem.list_directory() == "FILE\tcalc.py\nDIR \tpkg"

    def test_empty_directory(self, safe_dir):
        assert filesystem.list_directory() == "(空のディレクトリ)"

    def test_rejects_outside_of_safe_dir(self, safe_dir):
        assert filesystem.list_directory("..").startswith("[Error]")


class TestRunPytest:
    def test_passed(self, safe_dir):
        (safe_dir / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        assert testing.run_pytest().startswith("=== STATUS: PASSED")

    def test_failed(self, safe_dir):
        (safe_dir / "test_ng.py").write_text("def test_ng():\n    assert 1 == 2\n", encoding="utf-8")
        result = testing.run_pytest()
        assert result.startswith("=== STATUS: FAILED")
        assert "assert 1 == 2" in result

    def test_no_tests(self, safe_dir):
        assert testing.run_pytest().startswith("=== STATUS: NO_TESTS")
