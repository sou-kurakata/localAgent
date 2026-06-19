from agent import build_agent


def main():
    print("起動中...\n")
    agent = build_agent()
    prompt = "カレントディレクトリにあるファイルの一覧を確認して、教えてください。"
    result = agent.run(prompt)
    print("\n【最終結果】")
    print(result)


if __name__ == "__main__":
    main()