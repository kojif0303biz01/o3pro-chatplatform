# マルチステージビルド: ビルドステージ
FROM python:3.12-slim as builder

# ビルド時の依存関係インストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 依存関係のインストール（キャッシュ効率化）
COPY apps/api/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 実行ステージ
FROM python:3.12-slim

# メタデータ
LABEL maintainer="o3pro-chatplatform" \
      version="1.0.0" \
      description="FastAPI Backend for Azure Container Apps"

# 非rootユーザー作成
RUN useradd -m -u 1000 appuser

# ランタイム依存関係（最小限）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ビルドステージから依存関係をコピー
COPY --from=builder /root/.local /home/appuser/.local

# アプリケーションコードをコピー
COPY --chown=appuser:appuser apps/api /app/apps/api
COPY --chown=appuser:appuser packages /app/packages

# パッケージをPythonパスに追加
ENV PYTHONPATH=/app:/app/packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Container Apps用環境変数
ENV PORT=8000
ENV WORKERS=2

# ユーザー切り替え
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ポート公開
EXPOSE 8000

# 実行コマンド（プロダクション用設定）
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS}"]