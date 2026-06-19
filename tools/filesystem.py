from pathlib import Path
from smolagents import tool


@tool
def list_directory(path: str = ".") -> str:
    """指定ディレクトリのファイル/フォルダ一覧を返す。

    Args:
        path: 一覧を取得するディレクトリのパス。省略時はカレント。
    """
    root = Path.cwd().resolve()
    target = (root / path).resolve()

    if root not in target.parents and target != root:
        return "[Error] 作業ディレクトリ外へのアクセスは禁止されています。"
    if not target.is_dir():
        return f"[Error] {target} はディレクトリではありません。"

    lines = []
    for item in sorted(target.iterdir()):
        kind = "DIR " if item.is_dir() else "FILE"
        lines.append(f"{kind}\t{item.name}")
    return "\n".join(lines) if lines else "(空のディレクトリ)"