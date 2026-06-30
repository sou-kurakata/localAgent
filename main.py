from agent import build_agent


def main():
    print("起動中...\n")
    agent = build_agent()
    prompt = (
        "あなたはファイルをディスクに書き込む必要があります。"
        "コメントに書くだけでは保存されません。必ず write_candidate ツールを使ってください。\n"
        "手順:\n"
        "1. write_candidate('calc.py', 'def add(a, b):\\n    return a + b\\n') を呼ぶ\n"
        "2. write_candidate('test_calc.py', テストコード) を呼ぶ\n"
        "3. run_pytest() を呼ぶ\n"
        "テストコードは 'from calc import add' で対象をインポートすること。"
    )
    result = agent.run(prompt)
    print("\n【最終結果】")
    print(result)


if __name__ == "__main__":
    main()