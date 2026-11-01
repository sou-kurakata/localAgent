from watcher import LoopWatcher, is_same_error


def failed_output(*, path="/home/a/project", line=7, seconds="0.02",
                  actual="6.0", expected="4"):
    """run_pytest が返す失敗出力を模したもの。揺れる部分を引数で変えられる。"""
    sep = "\\" if ":\\" in path else "/"   # Windows パスなら区切りも \ にそろえる
    return (
        "=== STATUS: FAILED   (テスト失敗あり) ===\n"
        "F                                                                        [100%]\n"
        "=================================== FAILURES ===================================\n"
        "_________________________________ test_average _________________________________\n"
        f"{path}{sep}test_buggy_math.py:{line}: in test_average\n"
        f"    assert average([2, 6]) == {expected}\n"
        f"E   assert {actual} == {expected}\n"
        # 比較対象になる E 行にも、パス・行番号・アドレスが混ざることがある
        f"E    +  where {actual} = <function average at 0x{line:x}f3a>([2, 6])\n"
        f"E    raised in {path}{sep}buggy_math.py:{line}\n"
        "=========================== short test summary info ============================\n"
        f"FAILED test_buggy_math.py::test_average - assert {actual} == {expected}\n"
        f"1 failed in {seconds}s\n"
    )


PASSED = "=== STATUS: PASSED   (全テスト成功) ===\n.                     [100%]\n1 passed in 0.01s\n"


class TestIsSameError:
    def test_identical_output_is_same(self):
        assert is_same_error(failed_output(), failed_output())

    def test_ignores_execution_time(self):
        assert is_same_error(failed_output(seconds="0.02"), failed_output(seconds="1.37"))

    def test_ignores_line_number(self):
        assert is_same_error(failed_output(line=7), failed_output(line=42))

    def test_ignores_absolute_path(self):
        assert is_same_error(
            failed_output(path="/home/a/project"),
            failed_output(path="/tmp/workspace"),
        )

    def test_ignores_windows_absolute_path(self):
        assert is_same_error(
            failed_output(path=r"C:\Users\a\workspace"),
            failed_output(path="/workspace"),
        )

    def test_ignores_memory_address(self):
        prev = failed_output() + "E   <object at 0x7f3a2b1c>\n"
        curr = failed_output() + "E   <object at 0x10ffe0>\n"
        assert is_same_error(prev, curr)

    def test_changed_actual_value_counts_as_progress(self):
        # 値が変わったなら修正が効いて前進している、とみなす
        assert not is_same_error(failed_output(actual="6.0"), failed_output(actual="5.0"))

    def test_different_failing_test_is_different(self):
        other = failed_output().replace("test_average", "test_add")
        assert not is_same_error(failed_output(), other)

    def test_different_status_is_different(self):
        timeout = "[TIMEOUT] 60秒以内に終了しませんでした（生成コードの無限ループの可能性）。"
        assert not is_same_error(failed_output(), timeout)

    def test_passed_is_never_same_error(self):
        assert not is_same_error(PASSED, PASSED)

    def test_empty_input_is_not_same(self):
        assert not is_same_error("", failed_output())
        assert not is_same_error(failed_output(), "")


class TestLoopWatcher:
    def test_first_failure_continues(self):
        assert LoopWatcher().record(failed_output()) == "continue"

    def test_escalates_then_aborts_on_repeated_failure(self):
        watcher = LoopWatcher(abort_after=2)
        assert watcher.record(failed_output(line=1)) == "continue"
        assert watcher.record(failed_output(line=2)) == "escalate"
        assert watcher.record(failed_output(line=3)) == "abort"
        assert watcher.streak == 2

    def test_new_failure_resets_streak(self):
        watcher = LoopWatcher(abort_after=2)
        watcher.record(failed_output())
        watcher.record(failed_output())
        assert watcher.streak == 1
        assert watcher.record(failed_output(actual="5.0")) == "continue"
        assert watcher.streak == 0

    def test_abort_threshold_is_configurable(self):
        watcher = LoopWatcher(abort_after=3)
        results = [watcher.record(failed_output()) for _ in range(4)]
        assert results == ["continue", "escalate", "escalate", "abort"]
