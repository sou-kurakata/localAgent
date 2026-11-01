# localAgent

寝ている間に、ローカル LLM だけでコードのバグ修正を進める自律型エージェントです。

外部の商用 AI API には一切つながず、Ollama 上の `qwen2.5-coder:7b` と pytest だけで「修正 → テスト → 再修正」のループを回します。朝起きたら、隔離ブランチに積まれた成果を `git diff` で確認してマージするかどうかを決める、という運用を想定しています。

## 特徴

### 暴走しても既存コードとリモートを壊さない
- 作業は毎回 `feature/agent-<task>-<timestamp>` という隔離ブランチで行い、終了時は成功・失敗・例外のどの経路でも元のブランチに戻す
- git 操作は `git_guard.py` に閉じ込め、`push` / `pull` / `fetch` / `remote` はコードから呼ばない
- 作業ツリーが汚れている場合は開始しない

### エージェントに与える行動空間を絞る
エージェントが使えるツールは次の 4 つだけです。

| ツール | 役割 | 制限 |
| --- | --- | --- |
| `list_directory` | 作業ディレクトリの一覧 | 作業ディレクトリ外は参照不可 |
| `read_file` | ファイルの読み取り | パス区切り・`..` を拒否 |
| `write_candidate` | ファイルの書き込み | `.py` のみ。`test_*` は書き換え不可 |
| `run_pytest` | テストの実行 | 60 秒でタイムアウト |

テストファイルを書き換えられないようにしているのは、実装ではなくテストの方を歪めて「通ったことにする」のを防ぐためです。

### 自己申告を信用しない
エージェントが「直した」と言っても、Manager が自分で pytest を実行して成否を判定します。成功したときだけ隔離ブランチにコミットします。

### 同じ失敗の繰り返しを検知して止まる
`watcher.py` が pytest の出力から実行時間・行番号・絶対パス・メモリアドレスなどの揺れを正規化し、「ステータス・失敗したテスト名・`E` 行」を指紋として比較します。同じ指紋の失敗が続いたら停滞とみなして安全停止します。試行回数にも上限があります。

### コンテナで封じ込める
`docker-compose.yml` では、生成コードを実行する agent コンテナを次のように縛っています。

- 外向きゲートウェイのない内部ネットワークにだけ接続（インターネット遮断）
- マウントするのはワークスペースの 1 ディレクトリだけ
- トークンや鍵は渡さない（渡すのはコミット用の名前とメールだけ）
- 非 root ユーザー、`cap_drop: ALL`、`no-new-privileges`、読み取り専用のルート FS

## 処理の流れ

```
Manager（安全制御・git・判定を担当）
  │ 隔離ブランチを作成
  ▼
┌─ 外側ループ（max_iterations 回まで）──────────┐
│  CodeAgent を毎回作り直して実行                │
│    └ list_directory / read_file /             │
│      write_candidate / run_pytest を使って修正 │
│  Manager が pytest を実行して判定              │
│    ├ 成功 → 隔離ブランチにコミットして終了     │
│    └ 失敗 → 前回と同じ失敗なら安全停止         │
│             違えば結果を次の試行に渡す         │
└──────────────────────────────────────────────┘
  │ 元のブランチに戻す
  ▼
朝、人間が git diff で確認してマージ or 破棄
```

## 構成

| ファイル | 役割 |
| --- | --- |
| `main.py` | エントリポイント |
| `manager.py` | 外側ループ、プロンプト組み立て、成否判定 |
| `agent.py` | smolagents の `CodeAgent` にモデルとツールを配線 |
| `config.py` | モデル設定と共通定数 |
| `tools/` | エージェントに許可するツール |
| `watcher.py` | 同一エラーの検知 |
| `git_guard.py` | 隔離ブランチの作成・コミット・復帰 |
| `Dockerfile` / `docker-compose.yml` | コンテナでの封じ込め |
| `sample/` | 動作確認用のサンプル（バグ入りの `buggy_math.py` とそのテスト） |
| `Plan.md` | 開発初期の構想メモ（実装とは異なる箇所あり） |

## 使い方

### 準備
作業対象のワークスペースは、このリポジトリと同じ階層の `workspace` ディレクトリです。git リポジトリとして初期化し、変更がない状態にしておきます。

```
dev/
├── localAgent/   # このリポジトリ
└── workspace/    # エージェントが作業する git リポジトリ
```

サンプルで試す場合は、`sample/` の中身を `workspace/` にコピーしてコミットしてください。

### Docker で実行する（推奨）

```bash
cp .env.example .env   # WORKSPACE_HOST をワークスペースの絶対パスに書き換える
docker compose up -d ollama
docker compose exec ollama ollama pull qwen2.5-coder:7b   # 初回のみ
docker compose run --rm agent
```

### ホストで実行する

```bash
ollama pull qwen2.5-coder:7b
python -m venv venv
source venv/bin/activate   # Windows は venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### オプション

| オプション | 説明 | 既定値 |
| --- | --- | --- |
| `--task-file` | タスク内容を書いたテキストファイル | サンプルのバグ修正タスク |
| `--task-slug` | 隔離ブランチ名に使う識別子 | `default-task` |
| `--max-iterations` | 外側ループの試行回数の上限 | `3` |

## 技術スタック
- Python 3.12
- [smolagents](https://github.com/huggingface/smolagents)（`CodeAgent`）
- LiteLLM 経由で Ollama（`qwen2.5-coder:7b`、コンテキスト長 32k）
- pytest
- Docker Compose
