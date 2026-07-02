from agent import build_agent
from tools.filesystem import list_directory
from watcher import LoopWatcher
from git_guard import start_isolation, commit_all, finish_isolation, GitError

# タスクの「意図」だけ受け取り、7Bが迷わない構造化プロンプトに整形する。
# 手で調整したプロンプトをテンプレート化して自動生成する。
def build_prompt(task: str, attempt: int, last_feedback: str = "") -> str:
    base = (
        "あなたはローカルのコーディングエージェントです。\n\n"
        f"# タスク\n{task}\n\n"
        "# 作業ディレクトリ\n"
        "list_directory() が見せるファイルが、あなたが読める/書ける/テストできる全てです。\n"
        "（read_file・write_candidate・run_pytest は同じ場所を見ています）\n\n"
        "# 使えるツール\n"
        "- list_directory(): 作業ディレクトリのファイル一覧を返す\n"
        "- read_file(<ファイル名>): 既存ファイルの中身を読む（修正前に必ず対象を読むこと）\n"
        "- write_candidate(<ファイル名>, <コード文字列>): ファイルを保存する（上書き可）\n"
        "- run_pytest(): 保存済みのテストを実行し、結果を返す\n\n"
        "# 進め方\n"
        "1. list_directory() で今あるファイルを確認する\n"
        "2. 既存の実装・テストがあれば read_file() で中身を読む\n"
        "3. 必要な修正/実装を write_candidate() で保存する（既存テストは上書きしない）\n"
        "4. run_pytest() が全て通るまで 2〜3 を繰り返す\n\n"
        "# ゴール\n"
        "run_pytest() で全テストが通れば完了。\n"
        "テストがまだ無い場合のみ、実装を検証するテストを書く（実装ファイルから import すること）。\n"
        "run_pytest() が PASSED になったら、それ以上ツールを呼ばず final_answer('done') で直ちに終了せよ。\n"
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

def promote_files():
    """M5① で実装予定。緑になった _agent_output/ の成果を workspace リポジトリへコピーする橋渡し。"""
    pass  # 今は何もしない。commit_all が空を返すのが正常。


def run_task(task, workspace, task_slug, max_iterations=5):
    # ① 隔離ブランチ作成＆checkout（失敗したらループに入る前に止める）
    try:
        state = start_isolation(workspace, task_slug)
    except GitError as e:
        print(f"⛔ 隔離開始に失敗: {e}")
        return False

    # state が確定した後だけ finally が動くよう、ここから別の try で包む
    try:
        print(f"=== タスク開始: {task} ===\n")
        watcher = LoopWatcher(abort_after=2)
        last_feedback = ""

        for attempt in range(1, max_iterations + 1):
            print(f"\n----- 試行 {attempt}/{max_iterations} -----")

            agent = build_agent(max_steps=3)   # 毎回作り直してコンテキストをリセット
            prompt = build_prompt(task, attempt, last_feedback)
            agent.run(prompt)

            # Manager 自身が pytest を実行して「真実」を確認（自己申告は信用しない）
            from tools.testing import run_pytest
            result = run_pytest()
            print(result)

            if is_passed(result):
                print(f"\n✅ 試行 {attempt} で成功しました。")
                promote_files()   # ← M5① で実装。今は下記の空スタブでOK
                sha = commit_all(workspace, f"agent: {task_slug} passed (attempt {attempt})")
                if sha:
                    print(f"   隔離ブランチにコミット: {sha[:8]}")
                return True

            action = watcher.record(result)
            if action == "abort":
                print("\n⛔ 停滞検知(同一エラー連続)により安全停止します。")
                return False

            last_feedback = result   # 失敗結果を次の試行へフィードバック

        print(f"\n⛔ {max_iterations} 回試行しましたが成功しませんでした。安全停止します。")
        return False
    finally:
        # ③ 成功・失敗・例外、どの経路でも必ず元ブランチへ戻す
        finish_isolation(workspace, state["base"])