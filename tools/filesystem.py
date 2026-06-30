from pathlib import Path
from smolagents import tool
from config import SAFE_DIR

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

@tool
def write_candidate(filename: str, content: str) -> str:
    """候補コードを SAFE_DIR 直下に書き込む（既存ソースは上書き不可）。

    Args:
        filename: 書き込むファイル名。ディレクトリ区切りは含められない。
        content: ファイルに書き込むテキスト内容。
    """
    # ① ファイル名にパス区切り・親参照を含ませない（トラバーサル封じ）
    if "/" in filename or "\\" in filename or ".." in filename:
        return "[Error] filename にパス区切りや '..' は使えません。ファイル名のみ指定してください。"
    if Path(filename).name != filename:
        return "[Error] filename が不正です。ファイル名のみ指定してください。"

    # ② 拡張子を絞る（誤って .bat 等を吐かせない補助線）
    if not filename.endswith(".py"):
        return "[Error] 書き込めるのは .py ファイルのみです。"

    # ③ SAFE_DIR を必ず用意し、その配下に確実に収める
    SAFE_DIR.mkdir(parents=True, exist_ok=True)
    target = (SAFE_DIR / filename).resolve()
    if SAFE_DIR.resolve() not in target.parents:
        return "[Error] SAFE_DIR の外には書き込めません。"

    # ④ 書き込み（UTF-8固定。M1の run_pytest と文字コードを揃える）
    try:
        target.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"[Error] 書き込みに失敗しました: {e}"

    return f"[OK] 書き込み成功: {target.name}（{len(content)} 文字）"