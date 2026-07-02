from pathlib import Path
from smolagents import LiteLLMModel

# ローカルLLM (Ollama) 接続設定
# "ollama_chat/" を付けると LiteLLM が Ollama のネイティブ /api/chat を使い、
# チャットテンプレートが正しく当たり num_ctx も渡せる（OpenAI互換エンドポイントは経由しない）
MODEL = LiteLLMModel(
    model_id="ollama_chat/qwen2.5-coder:7b",
    api_base="http://localhost:11434",
    num_ctx=32768,
    temperature=0.2,
    # api_key は ollama provider では不要（付けても無害）
)

# プロジェクト共通の定数
PROJECT_ROOT = Path.cwd()
SAFE_DIR = PROJECT_ROOT / "_agent_output"  # シャドーイング出力先（M2で使用）
MAX_ITERATIONS = 5                         # 外側ループ上限（M3で使用）
WORKSPACE_DIR = PROJECT_ROOT.parent / "workspace" # 昇格用