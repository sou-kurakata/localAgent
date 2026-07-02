from manager import run_task


def main():
    print("起動中...\n")
    task = (
        "整数のリストを受け取り、最大値と最小値の差を返す関数 value_range(numbers) を "
        "calc.py に作成してください。"
        "ただし、空のリストが渡された場合は ValueError を送出してください。"
        "それをテストする test_calc.py も作成してください。"
        "テストには空リストで ValueError が出ることの確認も含めること。"
    )
    run_task(task, max_iterations=3)


if __name__ == "__main__":
    main()