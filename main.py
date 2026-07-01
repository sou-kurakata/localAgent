from manager import run_task


def main():
    print("起動中...\n")
    task = (
        "数値のリストを受け取り、偶数だけを合計して返す関数 sum_even(numbers) を "
        "calc.py に作成してください。空リストの場合は 0 を返します。"
        "それをテストする test_calc.py も作成してください。"
        
    )
    run_task(task, max_iterations=3)


if __name__ == "__main__":
    main()