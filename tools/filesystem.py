from pathlib import Path
from smolagents import tool
from config import SAFE_DIR

@tool
def list_directory(path: str = ".") -> str:
    """指定ディレクトリのファイル/フォルダ一覧を返す。

    Args:
        path: 一覧を取得するディレクトリのパス。省略時はカレント。
    """
    # 全ツール共通の作業ルート = SAFE_DIR に統一。
    # 旧実装は Path.cwd() 基準で、read/write/run_pytest（=SAFE_DIR）と
    # ルートがズレ、一覧に修正対象が映らず7Bが対象を見失う原因だった。
    SAFE_DIR.mkdir(parents=True, exist_ok=True)
    root = SAFE_DIR.resolve()
    target = (root / path).resolve()

    # M3のトラバーサルガードは基準をSAFE_DIRへ差し替えて温存
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

@tool
def read_file(filename: str) -> str:
    """SAFE_DIR 直下の既存ファイルの中身を読む。修正前に対象を読むために使う。

    Args:
        filename: 読むファイル名。ディレクトリ区切りは含められない。
    """
    # write_candidate と同じトラバーサル封じを踏襲
    if "/" in filename or "\\" in filename or ".." in filename:
        return "[Error] filename にパス区切りや '..' は使えません。"
    if Path(filename).name != filename:
        return "[Error] filename が不正です。ファイル名のみ指定してください。"

    target = (SAFE_DIR / filename).resolve()
    if SAFE_DIR.resolve() not in target.parents:
        return "[Error] SAFE_DIR の外は読めません。"
    if not target.is_file():
        return f"[Error] ファイルが存在しません: {filename}"

    return target.read_text(encoding="utf-8")