import argparse
from pathlib import Path
from manager import run_task

DEFAULT_TASK = (
    "西暦の年を受け取り、うるう年ならTrue、そうでなければFalseを返す関数を作ってください。それをテストするコードも書いてください。"
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", help="problem_statement を書いたファイル")
    parser.add_argument("--repo", help="対象リポジトリのパス")
    parser.add_argument("--maz-iterations", type=int, default=3)
    args = parser.parse_args()

    print("起動中...\n")

    if args.task_file:
        task = Path(args.tsak_faile).read_text(encoding="utf-8")
    else:
        task = DEFAULT_TASK

    run_task(task, max_iterations=3)


if __name__ == "__main__":
    main()