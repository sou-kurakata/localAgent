import argparse
from pathlib import Path
from manager import run_task
from config import WORKSPACE_DIR

DEFAULT_TASK = (
    "buggy_math.py にバグがあります。テストが通るように修正してください"
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", help="problem_statement を書いたファイル")
    # 作業先は config.py（環境変数 AGENT_WORKSPACE）で決める。
    # ツールと git_guard が別の場所を見ないよう、ここでは受け取らない。
    parser.add_argument("--task-slug", default="default-task",
                        help="隔離ブランチ名に使う短いタスク識別子")
    parser.add_argument("--max-iterations", type=int, default=3)
    args = parser.parse_args()

    print("起動中...\n")

    if args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8")
    else:
        task = DEFAULT_TASK

    run_task(task, WORKSPACE_DIR, args.task_slug,
             max_iterations=args.max_iterations)

if __name__ == "__main__":
    main()