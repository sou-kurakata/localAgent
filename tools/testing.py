import os
import sys
import subprocess
from smolagents import tool
from config import SAFE_DIR

# pytest の終了コードを、LLMが解釈しやすいステータスへ翻訳する
_PYTEST_EXIT = {
    0: "PASSED   (全テスト成功)",
    1: "FAILED   (テスト失敗あり)",
    2: "INTERRUPTED (実行が中断された)",
    3: "INTERNAL_ERROR (pytest内部エラー)",
    4: "USAGE_ERROR (pytestの使い方エラー)",
    5: "NO_TESTS (テストが1件も収集されなかった)",
}

_MAX_OUTPUT = 4000  # LLMへ返す最大文字数。num_ctx節約のため


@tool
def run_pytest() -> str:
    """SAFE_DIR 内で pytest を実行し、結果を返す。

    Args:
        target: SAFE_DIR からの相対パス。省略時は SAFE_DIR 全体を対象にする。
    """
    if not SAFE_DIR.is_dir():
        return f"[Error] 出力ディレクトリが存在しません: {SAFE_DIR}"

    # 子プロセスの出力を強制的に UTF-8 に固定（Windowsのcp932事故を防ぐ）
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", ".", "-q", "--tb=short"],
            cwd=SAFE_DIR,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] 60秒以内に終了しませんでした（生成コードの無限ループの可能性）。"

    status = _PYTEST_EXIT.get(proc.returncode, f"UNKNOWN (exit={proc.returncode})")
    output = (proc.stdout or "") + (proc.stderr or "")
    if len(output) > _MAX_OUTPUT:
        # 失敗の要約は末尾に集まるので、末尾を優先して残す
        output = "...(冒頭省略)...\n" + output[-_MAX_OUTPUT:]

    return f"=== STATUS: {status} ===\n{output}"
