# エージェント本体コンテナ（agent サービス）
# 目的: ④最小権限で agent を焼き込む。実行時は read_only / cap_drop ALL で回す前提。
FROM python:3.12-slim

# --- OS層: git だけ入れる（git_guard が subprocess で叩く）------------------
# push/pull は git_guard から呼ばない設計なので、ネット遮断下でも git 自体は使える。
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# --- 非root ユーザー (uid1000 agent) ------------------------------------
# read_only ルートFS でも読める場所に HOME を作り、.gitconfig をビルド時に焼き込む。
ENV HOME=/home/agent
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin agent

# --- Python 実行環境の方針 -------------------------------------------------
# read_only ルートFS で「書けなくてコケる」を防ぐため、書き込み先を全部 /tmp(tmpfs) へ逃がす。
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/hf \
    XDG_CACHE_HOME=/tmp/cache

WORKDIR /app

# --- 依存だけ先にコピーしてレイヤキャッシュを効かせる -----------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# --- アプリ本体（.dockerignore で venv/sample/.git 等は除外）--------------
COPY . .

# --- git dubious ownership 対策 -------------------------------------------
# マウント /workspace の所有 uid とコンテナ内 uid(1000) がズレると git が拒否する。
# agent ユーザーの ~/.gitconfig にビルド時点で焼き込む（実行時 read_only でも読める）。
USER agent
RUN git config --global --add safe.directory /workspace \
 && git config --global core.autocrlf input \
 && git config --global core.fileMode false
# 既定は本番タスク実行。検証時は `docker compose run --rm agent python -c ...` で上書きする。
CMD ["python", "main.py"]