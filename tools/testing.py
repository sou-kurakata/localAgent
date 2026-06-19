import subprocess
from smolagents import tool
from config import SAFE_DIR


@tool
def run_pytest(target: str = ".") -> str:
    """SAFE_DIR 内で pytest を実行し、結果テキストを返す。

    Args:
        target: SAFE_DIR からの相対のテスト対象パス。
    """
    # subprocess.run([...,"pytest", target], cwd=SAFE_DIR,
    #                timeout=60, capture_output=True, text=True, encoding="cp932")
    # → timeout 必須（生成コードの無限ループ対策）。stdout+stderr を返す
    ...