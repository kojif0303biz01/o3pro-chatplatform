import os
import json
import logging
import azure.functions as func
from datetime import datetime
from typing import Optional

# 共通モジュールのインポート（Container Apps環境でパスが通る）
try:
    from packages.handlers.background_handler import BackgroundHandler
    from packages.cosmos_history.cosmos_history import CosmosHistory
except ImportError:
    logging.warning("Common packages not found. Running in standalone mode.")

app = func.FunctionApp()

# ロガー設定
logger = logging.getLogger(__name__)

@app.function_name(name="BackgroundJobProcessor")
@app.route(route="background/{job_id}", auth_level=func.AuthLevel.FUNCTION)
async def process_background_job(req: func.HttpRequest) -> func.HttpResponse:
    """
    バックグラウンドジョブ処理用Function
    Container Apps上でKEDAによってスケールされる
    """
    job_id = req.route_params.get('job_id')
    logger.info(f"Processing background job: {job_id}")
    
    try:
        # リクエストボディから詳細を取得
        req_body = req.get_json()
        session_id = req_body.get('session_id')
        message = req_body.get('message')
        mode = req_body.get('mode', 'background')
        effort = req_body.get('effort', 'medium')
        
        # バックグラウンドハンドラーを使用
        handler = BackgroundHandler()
        result = await handler.process({
            'session_id': session_id,
            'message': message,
            'mode': mode,
            'effort': effort,
            'job_id': job_id
        })
        
        return func.HttpResponse(
            json.dumps({
                'success': True,
                'job_id': job_id,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                'success': False,
                'job_id': job_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }),
            mimetype="application/json",
            status_code=500
        )

@app.function_name(name="SessionCleanup")
@app.timer_trigger(schedule="0 0 */6 * * *", arg_name="timer", run_on_startup=False)
async def cleanup_old_sessions(timer: func.TimerRequest) -> None:
    """
    古いセッションを定期的にクリーンアップ
    6時間ごとに実行
    """
    logger.info("Starting session cleanup task")
    
    try:
        # Cosmos DB接続
        cosmos_history = CosmosHistory()
        
        # 7日以上古いセッションを削除
        deleted_count = await cosmos_history.cleanup_old_sessions(days=7)
        
        logger.info(f"Cleaned up {deleted_count} old sessions")
        
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")

@app.function_name(name="HealthCheck") 
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    ヘルスチェックエンドポイント
    Container Appsのヘルスプローブで使用
    """
    return func.HttpResponse(
        json.dumps({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'function_runtime': os.getenv('FUNCTIONS_WORKER_RUNTIME', 'python'),
            'version': '1.0.0'
        }),
        mimetype="application/json",
        status_code=200
    )

@app.function_name(name="JobStatusMonitor")
@app.service_bus_queue_trigger(
    arg_name="msg", 
    queue_name="job-status-queue",
    connection="ServiceBusConnection"
)
async def monitor_job_status(msg: func.ServiceBusMessage):
    """
    Service Busキューからジョブステータスを監視
    Container Apps Dapr統合で使用可能
    """
    try:
        message_body = json.loads(msg.get_body().decode('utf-8'))
        job_id = message_body.get('job_id')
        status = message_body.get('status')
        
        logger.info(f"Job {job_id} status update: {status}")
        
        # ステータス更新処理
        # 実際の実装では、SignalRやWebSocketで通知
        
    except Exception as e:
        logger.error(f"Error processing status message: {str(e)}")