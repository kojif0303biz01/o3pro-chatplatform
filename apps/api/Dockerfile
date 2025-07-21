FROM python:3.12-slim

WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 要件ファイルをコピーしてインストール
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

# アプリケーションコードをコピー
COPY apps/api /app/apps/api
COPY packages /app/packages
COPY core /app/core
COPY handlers /app/handlers
COPY cosmos_history /app/cosmos_history

# Pythonパスを設定
ENV PYTHONPATH=/app:/app/packages

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]