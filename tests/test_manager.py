from manager import build_prompt, is_passed


def test_is_passed():
    assert is_passed("=== STATUS: PASSED   (全テスト成功) ===\n1 passed")
    assert not is_passed("=== STATUS: FAILED   (テスト失敗あり) ===\n1 failed")
    assert not is_passed("[TIMEOUT] 60秒以内に終了しませんでした")


def test_prompt_includes_task():
    prompt = build_prompt("average を直す", attempt=1)
    assert "average を直す" in prompt
    assert "前回" not in prompt


def test_prompt_carries_previous_failure():
    prompt = build_prompt("average を直す", attempt=2, last_feedback="E   assert 6.0 == 4")
    assert "試行1" in prompt
    assert "E   assert 6.0 == 4" in prompt
