# Azure Functions Python用イメージ
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# メタデータ
LABEL maintainer="o3pro-chatplatform" \
      version="1.0.0" \
      description="Azure Functions for Container Apps"

# 環境変数
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    FUNCTIONS_WORKER_RUNTIME=python

# 作業ディレクトリ
WORKDIR /home/site/wwwroot

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# packagesディレクトリをコピー（共通モジュール）
COPY --from=api-build /app/packages /home/site/wwwroot/packages

# PYTHONPATHの設定
ENV PYTHONPATH=/home/site/wwwroot:/home/site/wwwroot/packages