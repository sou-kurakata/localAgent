"""M4: ループ検知 Watcher。

外側ループ（manager.run_task）が「同じ失敗を繰り返しているだけ」の状態に
陥っていないかを判定する。真の判定者は run_pytest だが、pytest 出力は実行ごとに
時刻・行番号・パス・アドレスなどが揺れるため、そのまま文字列比較すると
「毎回違うエラー」に見えてしまう。ここではノイズを正規化して落とし、
エラーの“同一性”だけを取り出して比較する。

設計方針:
  - 消す（揺れるノイズ）: 実行時間 / 行番号 / 絶対パス / 0xアドレス / 進捗%
  - 残す（同一性の核）  : STATUS種別 / 失敗テスト名 / E行の中身（比較値まで）
    → 値が変われば「前進」とみなし、別エラー扱いにする。
"""
import re

# --- 揺れるノイズを落とす正規化ルール（順序に意味あり）-----------------------
_SUBS = [
    (re.compile(r"0x[0-9a-fA-F]+"), "0xADDR"),                 # メモリアドレス
    (re.compile(r"\d+\.\d+s\b"), "<t>s"),                      # 実行時間 0.02s
    (re.compile(r"[A-Za-z]:\\(?:[^\s:\\]+\\)*([^\s:\\]+)"), r"\1"),  # Windows絶対パス→basename
    (re.compile(r"(?:/[^\s:/]+)+/([^\s:/]+)"), r"\1"),         # Unix絶対パス→basename
    (re.compile(r"(\.py):\d+"), r"\1:L"),                      # file.py:123 → file.py:L
    (re.compile(r":\d+:"), ":L:"),                             # :123:（tb-short行頭）
    (re.compile(r"\bline \d+\b"), "line L"),                   # "line 123"
    (re.compile(r"\[\s*\d+%\]"), "[PCT]"),                     # 進捗 [100%]
]


def _status_of(text: str) -> str:
    """出力の種別（PASSED/FAILED/TIMEOUT/NO_TESTS/...）を取り出す。"""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("=== STATUS:"):
            # "=== STATUS: FAILED   (…) ===" → "FAILED"
            return s.split(":", 1)[1].strip().split()[0]
        if s.startswith("[TIMEOUT]"):
            return "TIMEOUT"
    return "UNKNOWN"


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for pat, rep in _SUBS:
        text = pat.sub(rep, text)
    # 各行 末尾空白を除去し、空行を落とす
    lines = [ln.rstrip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln.strip())


def _signature(text: str):
    """エラーの同一性を表す (status, 失敗テスト名, E行) の指紋を返す。"""
    status = _status_of(text)
    norm = _normalize(text)

    failed_names = set()
    e_lines = []
    for ln in norm.splitlines():
        s = ln.strip()
        # tb-short の失敗ヘッダ:  ____ test_average ____
        m = re.match(r"^_+\s*(\S.*?)\s*_+$", s)
        if m:
            failed_names.add(m.group(1))
            continue
        # short summary:  FAILED test_x.py::test_y - AssertionError: ...
        if s.startswith("FAILED "):
            failed_names.add(re.sub(r"\s+", " ", s[len("FAILED "):]))
            continue
        # 例外/アサーションの実体:  E   assert 6.0 == 4
        if s == "E" or s.startswith("E "):
            e_lines.append(re.sub(r"\s+", " ", s))

    return (status, tuple(sorted(failed_names)), tuple(sorted(e_lines)))


def is_same_error(prev: str, curr: str) -> bool:
    """行番号・パス・時刻等を除いて正規化し、同一エラーかを判定。

    Args:
        prev: 前回の run_pytest 出力。
        curr: 今回の run_pytest 出力。
    """
    if not prev or not curr:
        return False
    # PASSED は「エラー」ではないので、同一エラー判定の対象外
    if _status_of(prev) == "PASSED" or _status_of(curr) == "PASSED":
        return False
    return _signature(prev) == _signature(curr)


class LoopWatcher:
    """連続で同一エラーが出た回数を数え、次アクションを助言する。

    record(result) の戻り値:
        "continue" : 新しい失敗。通常どおり次の試行へ。
        "escalate" : 前回と同一。プロンプトを強めて別アプローチを促す。
        "abort"    : 同一失敗が閾値回続いた。停滞とみなし安全停止。
    """
    def __init__(self, abort_after: int = 2):
        self._prev = None
        self._streak = 0          # 連続同一エラー回数
        self._abort_after = abort_after

    def record(self, result: str) -> str:
        same = self._prev is not None and is_same_error(self._prev, result)
        self._streak = self._streak + 1 if same else 0
        self._prev = result
        if not same:
            return "continue"
        return "abort" if self._streak >= self._abort_after else "escalate"

    @property
    def streak(self) -> int:
        return self._streak