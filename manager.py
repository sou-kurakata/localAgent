from agent import build_agent
from tools.filesystem import list_directory


# タスクの「意図」だけ受け取り、7Bが迷わない構造化プロンプトに整形する。
# 手で調整したプロンプトをテンプレート化して自動生成する。
def build_prompt(task: str, attempt: int, last_feedback: str = "") -> str:
    base = (
        "あなたはローカルのコーディングエージェントです。\n\n"
        f"# タスク\n{task}\n\n"
        "# 使えるツール\n"
        "- write_candidate(<ファイル名>, <コード文字列>): ファイルを保存する\n"
        "- run_pytest(): 保存済みのテストを実行し、結果を返す\n\n"
        "# ゴール\n"
        "タスクを実装し、それを検証するテストを書き、run_pytest() で全て通ることを確認せよ。\n"
        "テストは実装ファイルから import すること。\n"
        "全て通ったら完了。\n"
    )
    if last_feedback:
        base += (
            f"\n# 前回 (試行{attempt - 1}) の失敗\n"
            f"以下のテスト結果を踏まえて修正してください:\n{last_feedback}\n"
        )
    return base


# run_pytest の戻り値（先頭行が "=== STATUS: ... ===")から成否を判定する。
def is_passed(pytest_output: str) -> bool:
    return "STATUS: PASSED" in pytest_output


def run_task(task: str, max_iterations: int = 3) -> bool:
    print(f"=== タスク開始: {task} ===\n")
    last_feedback = ""

    for attempt in range(1, max_iterations + 1):
        print(f"\n----- 試行 {attempt}/{max_iterations} -----")

        # 毎回エージェントを作り直す = コンテキストをリセットし、
        # 前回の20,000トークン肥大やループ状態を持ち越さない。
        agent = build_agent(max_steps=3)   # ← 短く区切る。10分ステップ対策
        prompt = build_prompt(task, attempt, last_feedback)

        agent.run(prompt)

        # Manager 自身が pytest を直接実行して「真実」を確認する。
        # エージェントの自己申告（"All tests passed"）は信用しない。
        from tools.testing import run_pytest
        result = run_pytest()
        print(result)

        if is_passed(result):
            print(f"\n✅ 試行 {attempt} で成功しました。")
            return True

        last_feedback = result   # 失敗結果を次の試行へフィードバック

    print(f"\n⛔ {max_iterations} 回試行しましたが成功しませんでした。安全停止します。")
    return False